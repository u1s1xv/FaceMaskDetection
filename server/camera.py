"""
视频源抽象 —— 采集线程 + 最新帧槽位。

设计要点（都是为实时性服务的）：

1. **latest-frame-wins（单槽缓冲）**
   采集线程只维护"最新一帧"，读方拿到的是当前最新帧，而不是排队中的旧帧。
   如果改成队列，当推理慢于采集时，队列会越积越长，画面延迟持续累积 ——
   用户看到的是几秒前的画面。实时系统宁可掉帧，也不要延迟。

2. **采集与推理解耦**
   采集线程只管抓帧，不阻塞在推理上。抓帧节奏由摄像头决定，
   推理节奏由算力决定，两者互不拖累。

3. **断流自动重连**
   USB 摄像头拔插、RTSP 抖动都会让 read() 连续失败。
   连续失败达到阈值就重新打开设备，并用退避避免疯狂重试。

4. **视频文件可当虚拟摄像头**
   source 传文件路径时循环播放，行为与真摄像头一致 ——
   这样自动化验证可复现，演示时也不用真对着摄像头。
"""

import logging
import os
import threading
import time

import cv2

logger = logging.getLogger(__name__)

# 采集后端优先级。
# 实测（640x480 本机摄像头）：MSMF 31.3 FPS，DSHOW 15.0 FPS，ANY 29.5 FPS。
# DSHOW 是网上最常被推荐的 Windows 后端，但在这台机器上只有一半帧率，
# 所以默认走 MSMF，打不开再降级到 DSHOW（部分 USB 摄像头 MSMF 兼容性差）。
# 采集后端候选 —— **按源类型区分**。
#
# 设备（USB 摄像头）和文件/网络流要用不同的后端：
#   MSMF / DSHOW 是摄像头专用后端，拿来打开视频文件会让 OpenCV 陷入异常路径，
#   实测一个 29 秒的 mp4 读首帧花了 76 秒。
#   文件与 RTSP 应该交给 FFMPEG。
DEVICE_BACKENDS = [
    ("MSMF", cv2.CAP_MSMF),
    ("DSHOW", cv2.CAP_DSHOW),
    ("ANY", cv2.CAP_ANY),
]
STREAM_BACKENDS = [
    ("FFMPEG", cv2.CAP_FFMPEG),
    ("ANY", cv2.CAP_ANY),
]

RECONNECT_AFTER_FAILURES = 30      # 连续读失败多少次后重连
RECONNECT_BACKOFF_SECONDS = 1.0    # 重连失败后的退避时间


class FrameSlot:
    """单槽缓冲：写入总是覆盖，读取总是拿最新。

    额外统计"被覆盖但从未被读取"的帧数 —— 这个数就是丢帧数，
    是判断"推理跟不跟得上采集"的直接指标。
    """

    def __init__(self):
        # 用 Condition 而不是裸 Lock：读方可以"等新帧"而不是空转轮询。
        # 轮询会带来 GIL 争用 —— 推流线程每秒唤醒 250 次抢锁，
        # 和推理线程互相拖累（实测把双方的帧率都压低了）。
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self._seq = 0
        self._data = None
        self._ts = 0.0
        self._consumed_seq = 0
        self._dropped = 0

    def put(self, data):
        with self._cond:
            if self._seq > self._consumed_seq and self._data is not None:
                self._dropped += 1        # 上一帧还没被读走就被覆盖了
            self._seq += 1
            self._data = data
            self._ts = time.time()
            self._cond.notify_all()       # 叫醒等新帧的推流线程
            return self._seq

    def get(self):
        """取"尚未被消费的最新帧"。返回 (seq, data, ts)。

        如果自上次 get() 以来没有新帧写入，data 返回 None。

        这一条是必须的：消费者（推理循环）会以远高于采集的节奏轮询，
        若每次都返回同一帧，推理会反复处理同一张图，白白烧掉 CPU。
        （早期版本漏了这个判断，实测 151 帧被"消费"了 3356 次。）
        """
        with self._lock:
            if self._data is None or self._seq == self._consumed_seq:
                return self._seq, None, self._ts
            self._consumed_seq = self._seq
            return self._seq, self._data, self._ts

    def peek(self):
        """看一眼最新帧但不标记为已消费（推流用）。"""
        with self._lock:
            return self._seq, self._data, self._ts

    def wait_newer(self, since_seq, timeout=1.0):
        """阻塞直到出现比 since_seq 更新的帧，或超时。

        返回 (seq, data, ts)。超时且没有新帧时 seq 仍等于 since_seq。
        用它替代"睡几毫秒再看一眼"的轮询：不空转、不抢 GIL、延迟更低。
        """
        with self._cond:
            # 两条都要判：既没有更新的帧，也还没有任何帧时，都应该等待。
            # 只判前者的话，调用方传入一个小于初始 seq 的值（比如 -1）就会立即返回，
            # 变成忙等待。
            if self._data is None or self._seq <= since_seq:
                self._cond.wait(timeout)
            return self._seq, self._data, self._ts

    @property
    def dropped(self):
        with self._lock:
            return self._dropped


def _parse_source(source):
    """把外部传入的 source 规整成 cv2 能吃的形式。

    "0" / "2"      -> 摄像头序号（int）
    "rtsp://..."   -> 网络流
    "D:/a/b.mp4"   -> 视频文件
    """
    if isinstance(source, int):
        return source, "device"
    text = str(source).strip()
    if text.isdigit():
        return int(text), "device"
    low = text.lower()
    if low.startswith(("rtsp://", "rtmp://", "http://", "https://")):
        return text, "stream"
    return text, "file"


def list_devices(max_index=4):
    """枚举本机可用摄像头。

    OpenCV 没有可靠的设备枚举接口，只能逐个序号试探。打开设备有开销，
    所以限制扫描范围 —— 上位机现场不会有几十个摄像头。

    **每个序号独立兜底**：某台设备被别的进程占用、或驱动抛异常时，
    不能让它把整个枚举带崩。枚举失败会让 /cameras 返回 500，
    而那个端点还承载着推流状态 —— 代价远大于"少列出一个摄像头"。
    """
    found = []
    for idx in range(max_index):
        try:
            probe = _probe_device(idx)
        except Exception as exc:                   # noqa: BLE001
            logger.warning("枚举摄像头 %d 失败（已跳过）: %s", idx, exc)
            continue
        if probe is not None:
            found.append(probe)
    return found


def _probe_device(idx):
    """试探单个序号；可用则返回设备信息，否则返回 None。"""
    for name, api in DEVICE_BACKENDS:
        cap = None
        try:
            cap = cv2.VideoCapture(idx, api)
            if cap.isOpened() and cap.read()[0]:
                return {
                    "index": idx,
                    "backend": name,
                    "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                }
        except Exception:                          # noqa: BLE001
            pass
        finally:
            if cap is not None:
                try:
                    cap.release()
                except Exception:                  # noqa: BLE001
                    pass
    return None


class CameraSource:
    """一个视频源：独立采集线程 + 最新帧槽位。"""

    def __init__(self, source, width=640, height=480, backend=None,
                 loop_file=True, name=None):
        self.raw_source, self.kind = _parse_source(source)
        self.width = int(width)
        self.height = int(height)
        self.loop_file = loop_file
        self.name = name or str(source)
        self._forced_backend = backend

        self._cap = None
        self._cap_backend = None
        self._thread = None
        self._running = False
        self._lock = threading.Lock()

        self._slot = FrameSlot()
        self._started_at = 0.0
        self._source_fps = 0.0             # 文件源的帧率，用于节流
        self._next_frame_at = 0.0          # 下一帧的目标时间点（节流用）

        # 统计量用独立的锁：采集线程写、HTTP 线程读，不能和 _lock 混用
        # （早期版本采集线程无锁写 _fps_window、读时加锁，保护不一致，
        #   导致 fps 算出 489 这种不可能的值）
        self._stats_lock = threading.Lock()
        self._fps_window = []              # 最近 2 秒的帧时间戳，用于滚动 FPS
        self._frames = 0
        self._reconnects = 0
        self._failures = 0
        self._last_error = ""

    # ------------------------------------------------------------ 开关
    def start(self):
        if self._running:
            return
        self._open()
        self._running = True
        self._started_at = time.time()
        self._thread = threading.Thread(target=self._capture_loop,
                                        name="camera-%s" % self.name, daemon=True)
        self._thread.start()
        logger.info("视频源已启动: %s（%s, 后端 %s, %dx%d）",
                    self.name, self.kind, self._cap_backend, self.width, self.height)

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=3.0)
            self._thread = None
        with self._lock:
            if self._cap is not None:
                self._cap.release()
                self._cap = None
        logger.info("视频源已停止: %s（累计 %d 帧，重连 %d 次）",
                    self.name, self._frames, self._reconnects)

    @property
    def is_running(self):
        return self._running

    # ------------------------------------------------------------ 采集
    def _open(self):
        """按后端优先级尝试打开；成功则记录实际使用的后端。"""
        if self._forced_backend:
            candidates = [(self._forced_backend, _api_of(self._forced_backend))]
        elif self.kind == "device":
            candidates = DEVICE_BACKENDS
        else:
            candidates = STREAM_BACKENDS
        last_exc = None
        for name, api in candidates:
            if api is None:
                continue
            try:
                cap = cv2.VideoCapture(self.raw_source, api)
                if cap.isOpened() and cap.read()[0]:
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                    # 视频文件：记下源帧率，采集线程据此节流。
                    # 不节流的话解码器会全速跑（实测 286 FPS），虚拟摄像头就失真了。
                    if self.kind == "file":
                        src_fps = cap.get(cv2.CAP_PROP_FPS)
                        if src_fps and 1.0 < src_fps < 240.0:
                            self._source_fps = float(src_fps)
                    with self._lock:
                        if self._cap is not None:
                            self._cap.release()
                        self._cap = cap
                        self._cap_backend = name
                    self._failures = 0
                    return True
                cap.release()
            except Exception as exc:               # noqa: BLE001
                last_exc = exc
        self._last_error = "无法打开视频源 %s%s" % (
            self.raw_source, "（%s）" % last_exc if last_exc else "")
        logger.error(self._last_error)
        return False

    def _reopen(self):
        """断流后重连。用退避避免疯狂重试。"""
        self._reconnects += 1
        with self._lock:
            if self._cap is not None:
                self._cap.release()
                self._cap = None
        time.sleep(RECONNECT_BACKOFF_SECONDS)
        if not self._running:
            return False
        ok = self._open()
        if ok:
            logger.warning("视频源 %s 重连成功（第 %d 次）", self.name, self._reconnects)
        else:
            logger.warning("视频源 %s 重连失败（第 %d 次）", self.name, self._reconnects)
        return ok

    def _capture_loop(self):
        while self._running:
            with self._lock:
                cap = self._cap
            if cap is None:
                if not self._reopen():
                    continue
                continue

            ok, frame = cap.read()

            if not ok:
                # 文件源读到结尾：循环播放，模拟"永远有下一帧"的摄像头
                if self.kind == "file" and self.loop_file:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                with self._stats_lock:
                    self._failures += 1
                    self._last_error = "读帧失败（连续 %d 次）" % self._failures
                    failures = self._failures
                if failures >= RECONNECT_AFTER_FAILURES:
                    self._reopen()
                else:
                    time.sleep(0.005)          # 别把 CPU 打满
                continue

            now = time.time()
            with self._stats_lock:
                self._failures = 0
                self._frames += 1
                self._fps_window.append(now)
                cutoff = now - 2.0
                while self._fps_window and self._fps_window[0] < cutoff:
                    self._fps_window.pop(0)

            self._slot.put(frame)

            # 文件源节流：按视频自身帧率放帧，否则解码器会全速跑
            # （实测 29 秒的片子 3 秒就放完了，虚拟摄像头失去意义）
            if self._source_fps > 0:
                target = self._next_frame_at
                if target <= 0:
                    self._next_frame_at = now
                    target = now
                self._next_frame_at += 1.0 / self._source_fps
                delay = self._next_frame_at - time.time()
                if delay > 0:
                    time.sleep(min(delay, 0.5))

    # ------------------------------------------------------------ 读取
    def read_latest(self):
        """取最新帧并标记为已消费。返回 (seq, frame, ts)；无新帧时 frame 为 None。"""
        seq, frame, ts = self._slot.get()
        return seq, frame, ts

    def peek_latest(self):
        """取最新帧但不消费（推流用）。"""
        return self._slot.peek()

    # ------------------------------------------------------------ 状态
    @property
    def fps(self):
        """滚动帧率（最近 2 秒）。

        样本太少时退回"总帧数 / 运行时长"，否则刚启动时会出现
        "4 帧算出 489 FPS" 这种无意义的数字。
        """
        with self._stats_lock:
            window = list(self._fps_window)
            frames = self._frames
        uptime = time.time() - self._started_at if self._started_at else 0.0

        if len(window) >= 5:
            span = window[-1] - window[0]
            if span > 0.2:
                return (len(window) - 1) / span
        if uptime > 0.5 and frames > 0:
            return frames / uptime
        return 0.0

    def stats(self):
        seq, _, ts = self._slot.peek()
        with self._stats_lock:
            frames = self._frames
            reconnects = self._reconnects
            last_error = self._last_error
        return {
            "name": self.name,
            "source": str(self.raw_source),
            "kind": self.kind,
            "running": self._running,
            "backend": self._cap_backend,
            "width": self.width,
            "height": self.height,
            "frames": frames,
            "fps": round(self.fps, 1),
            "source_fps": self._source_fps,
            "dropped": self._slot.dropped,
            "latest_seq": seq,
            "latest_age_ms": round((time.time() - ts) * 1000, 1) if ts else None,
            "reconnects": reconnects,
            "uptime_s": round(time.time() - self._started_at, 1) if self._started_at else 0,
            "last_error": last_error,
        }


def _api_of(name):
    for n, api in DEVICE_BACKENDS + STREAM_BACKENDS:
        if n == name:
            return api
    return None


class CameraManager:
    """已打开视频源的注册表。

    刻意做得很薄：只负责"谁开着、叫什么名字"，不掺业务逻辑。
    实时推理管线（阶段 2）会挂在 CameraSource 之上，而不是塞进这里。
    """

    def __init__(self):
        self._sources = {}                 # cam_id -> CameraSource
        self._pipelines = {}               # cam_id -> LivePipeline
        self._lock = threading.Lock()
        self._counter = 0
        self._devices_cache = None
        self._devices_at = 0.0
        self._devices_ttl = 30.0

    def open(self, source, width=640, height=480, backend=None, name=None):
        """打开一个视频源，返回 (cam_id, source)。失败时抛 RuntimeError。"""
        with self._lock:
            self._counter += 1
            cam_id = "cam%d" % self._counter

        src = CameraSource(source, width=width, height=height,
                           backend=backend, name=name or str(source))
        src.start()

        # 启动是异步的，给一点时间确认真的出帧了 —— 否则上层拿到的是
        # 一个"已注册但永远没画面"的源，问题要等到界面上才暴露
        deadline = time.time() + 5.0
        while time.time() < deadline:
            if src.peek_latest()[1] is not None:
                break
            time.sleep(0.05)
        else:
            src.stop()
            raise RuntimeError("视频源 %s 打开后 5 秒内没有出帧" % source)

        # 延迟导入：live.py 需要 camera.FrameSlot，模块顶层互相 import 会成环。
        # 这里只在真正打开摄像头时才导入，循环在加载期不会发生。
        from live import LivePipeline
        pipeline = LivePipeline(src)
        pipeline.start()

        with self._lock:
            self._sources[cam_id] = src
            self._pipelines[cam_id] = pipeline
        return cam_id, src

    def close(self, cam_id):
        with self._lock:
            src = self._sources.pop(cam_id, None)
            pipeline = self._pipelines.pop(cam_id, None)
        if src is None:
            return False
        if pipeline is not None:
            pipeline.stop()          # 先停推理，再停采集
        src.stop()
        return True

    def get(self, cam_id):
        with self._lock:
            return self._sources.get(cam_id)

    def get_pipeline(self, cam_id):
        with self._lock:
            return self._pipelines.get(cam_id)

    def list_opened(self):
        with self._lock:
            items = list(self._sources.items())
            pipes = dict(self._pipelines)
        out = []
        for cid, src in items:
            entry = dict(cam_id=cid, **src.stats())
            pipe = pipes.get(cid)
            if pipe is not None:
                entry["live"] = pipe.stats()
            out.append(entry)
        return out

    def list_devices_cached(self, ttl=30.0, error_ttl=10.0):
        """枚举本机摄像头，结果缓存若干秒。

        枚举要逐个序号试打开设备，一次好几秒。界面上刷新列表不该等这么久，
        所以缓存。

        **失败也要缓存**（用更短的 TTL）。这不是优化，是修 bug：
        只在成功时写缓存的话，一旦枚举抛异常（设备被别的进程占用、驱动报错），
        缓存永远是空的 —— 而客户端每秒轮询一次，于是每次都重新枚举，
        反复阻塞数秒并占住 GIL，把同进程的推理管线一起拖死。
        实测表现是"推流跑着跑着突然掉到 2 FPS"。
        """
        now = time.time()
        with self._lock:
            if (self._devices_cache is not None
                    and now - self._devices_at < self._devices_ttl):
                return self._devices_cache

        try:
            devices = list_devices()
            used_ttl = ttl
        except Exception:                          # noqa: BLE001
            logger.exception("枚举摄像头失败，缓存空结果以免每次轮询都重试")
            devices = []
            used_ttl = error_ttl

        with self._lock:
            self._devices_cache = devices
            self._devices_at = now
            self._devices_ttl = used_ttl
        return devices

    def close_all(self):
        with self._lock:
            items = list(self._sources.items())
            pipes = list(self._pipelines.values())
            self._sources.clear()
            self._pipelines.clear()
        for pipe in pipes:
            pipe.stop()
        for _, src in items:
            src.stop()
        return len(items)


_manager = None
_manager_lock = threading.Lock()


def get_manager():
    global _manager
    if _manager is None:
        with _manager_lock:
            if _manager is None:
                _manager = CameraManager()
    return _manager

