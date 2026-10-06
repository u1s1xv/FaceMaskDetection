"""
推理微批处理 —— 把短时间内的多个推理请求聚成一批，用一次 predict 处理。

为什么需要它（实测，1300x956，RTX 3060 Laptop）：

    单张 predict        20 ~ 26 ms
    4 张一批             7.8 ms/张   3.4x
    8 张一批             5.8 ms/张   4.6x
    16 张一批            5.5 ms/张   4.8x

收益来自摊薄 ultralytics predict 的固定开销（source 加载器、letterbox、NMS、
Results 对象构造）。而降 imgsz 没有用 —— 320 与 640 的耗时几乎相同。

为什么只在服务端做：批量检测时客户端本来就是并发提交的（并发数可配），
请求天然聚集在很短的时间窗内。服务端聚批不需要客户端改任何东西，
也不需要为了批量而重新设计 API。

代价：单独一个请求要等一小段时间窗（默认 12 ms）才被处理。
对交互式的单图检测来说这点延迟感知不到，而换来的是批量场景 3~4 倍吞吐。
窗口大小可以用 FMD_BATCH_WAIT_MS 调整，设 0 即退化为逐张处理。
"""

import logging
import os
import threading
import time

logger = logging.getLogger(__name__)

# 总开关。保留它是为了能做干净的 A/B —— 没有开关就只能"改代码前/后各测一次"，
# 而实测同一配置在不同轮次间能差 2 倍，那种对比说明不了任何问题。
ENABLED = os.environ.get("FMD_BATCH", "1") != "0"
MAX_BATCH = int(os.environ.get("FMD_BATCH_SIZE", "8"))
# 默认 0：不主动等待合批，只做"机会性合批"。
#
# 这不是偷懒，是实测结论 —— 12ms 的等待窗口是净损失：
#
#   窗口 12ms  conc=1  15.3 张/秒   conc=4  49.9 张/秒（avg_batch 4.00）
#   窗口  0ms  conc=1  19.2 张/秒   conc=4  53.2 张/秒（avg_batch 2.00）
#
# 也就是说：即使不等，批处理器唤醒时队列里已经有请求了，avg_batch 照样到 2；
# 而等待换来的"更整齐的批"抵不过它给每个请求增加的延迟。
# 想试更激进的合批可以调 FMD_BATCH_WAIT_MS，但请先自己量一遍。
MAX_WAIT_MS = float(os.environ.get("FMD_BATCH_WAIT_MS", "0"))


class _Job:
    """一个待处理的推理请求。"""
    __slots__ = ("image", "params", "event", "result", "error")

    def __init__(self, image, params):
        self.image = image
        self.params = params
        self.event = threading.Event()
        self.result = None
        self.error = None

    @property
    def key(self):
        """只有参数完全相同的请求才能合批 —— 不同阈值的结果没有可比性。"""
        return (self.params.get("model_name"), self.params.get("confidence"),
                self.params.get("iou"), self.params.get("imgsz"))


class InferenceBatcher:
    """把并发推理请求聚成批的工作线程。"""

    def __init__(self, detector, max_batch=MAX_BATCH, max_wait_ms=MAX_WAIT_MS):
        self._detector = detector
        self._max_batch = max(1, int(max_batch))
        self._max_wait = max(0.0, float(max_wait_ms) / 1000.0)

        self._pending = []
        self._cond = threading.Condition()
        self._running = False
        self._thread = None

        self._lock = threading.Lock()
        self._batches = 0
        self._jobs = 0
        self._max_seen = 0

    # ------------------------------------------------------------ 生命周期
    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="infer-batcher",
                                        daemon=True)
        self._thread.start()
        logger.info("推理批处理已启动（最大批 %d，等待窗口 %.0f ms）",
                    self._max_batch, self._max_wait * 1000)

    def stop(self):
        self._running = False
        with self._cond:
            self._cond.notify_all()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None

    # ------------------------------------------------------------ 提交
    def submit(self, image, params, timeout=300.0):
        """提交一张图，阻塞直到本批处理完。由 HTTP 线程调用。"""
        job = _Job(image, params)
        with self._cond:
            self._pending.append(job)
            self._cond.notify()
        if not job.event.wait(timeout):
            raise TimeoutError("推理超时（%.0f 秒）" % timeout)
        if job.error is not None:
            raise job.error
        return job.result

    # ------------------------------------------------------------ 主循环
    def _loop(self):
        while self._running:
            with self._cond:
                while self._running and not self._pending:
                    self._cond.wait(0.5)
                if not self._running:
                    return
                batch = self._pending[:self._max_batch]
                del self._pending[:len(batch)]

                # 只等到一个小窗口：给"几乎同时到达"的请求一个合批的机会。
                # 窗口设得越大，合批概率越高，但单请求的延迟也越大。
                if self._max_wait > 0 and len(batch) < self._max_batch:
                    deadline = time.time() + self._max_wait
                    while len(batch) < self._max_batch:
                        remaining = deadline - time.time()
                        if remaining <= 0:
                            break
                        if not self._cond.wait(remaining):
                            break                      # 超时，就这些了
                        room = self._max_batch - len(batch)
                        extra = self._pending[:room]
                        if not extra:
                            continue
                        del self._pending[:len(extra)]
                        batch.extend(extra)

            self._run(batch)

    def _run(self, batch):
        with self._lock:
            self._batches += 1
            self._jobs += len(batch)
            self._max_seen = max(self._max_seen, len(batch))

        # 按参数分组：阈值不同的请求不能合批
        groups = {}
        for job in batch:
            groups.setdefault(job.key, []).append(job)

        for jobs in groups.values():
            images = [j.image for j in jobs]
            params = dict(jobs[0].params)
            try:
                results = self._detector.run_inference_batch(images, **params)
                for job, res in zip(jobs, results):
                    res["batch_size"] = len(jobs)    # 观测用：这一批实际几张
                    job.result = res
                    job.event.set()
            except Exception as exc:                       # noqa: BLE001
                logger.exception("批处理失败（本批 %d 张）", len(jobs))
                for job in jobs:
                    job.error = exc
                    job.event.set()

    # ------------------------------------------------------------ 统计
    def stats(self):
        with self._lock:
            batches, jobs, peak = self._batches, self._jobs, self._max_seen
        with self._cond:
            waiting = len(self._pending)
        return {
            "batches": batches,
            "jobs": jobs,
            "avg_batch": round(jobs / batches, 2) if batches else 0.0,
            "peak_batch": peak,
            "max_batch": self._max_batch,
            "wait_ms": self._max_wait * 1000,
            "waiting": waiting,
        }


_batcher = None
_batcher_lock = threading.Lock()


def get_batcher():
    global _batcher
    if _batcher is None:
        with _batcher_lock:
            if _batcher is None:
                from detector import get_detector
                _batcher = InferenceBatcher(get_detector())
    return _batcher
