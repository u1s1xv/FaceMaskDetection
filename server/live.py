"""
实时推理管线 —— 把 CameraSource 的最新帧变成"画好框的 JPEG"。

与单图/批量路径的区别（这一点是刻意的）：

  单图/批量：服务端只回结构化 JSON，**客户端自己画框**。
            因为带宽是主要矛盾（服务端 PNG 1565 KB vs 客户端 JSON 2 KB）。

  实时视频：**服务端画好框再推流**。因为时序一致性是主要矛盾 ——
            框和帧分两个通道传，任何抖动都会表现为"框在画面外飘"。
            而实测画框 0.12 ms + JPEG 编码 0.57 ms，代价几乎为零。

同一个系统里两条渲染路径，约束不同所以选择不同。

性能（实测 640x480，RTX 3060 Laptop）：
  推理 annotated=False   19.63 ms
  cv2 画框                0.12 ms
  JPEG 编码 (q=80)        0.57 ms
  ------------------------------------
  合计                   20.32 ms → 49.2 FPS

对比现有 _create_beautified_image（走 PNG）的 69.69 ms → 14.4 FPS，快 3.4 倍。
所以这里**不能复用**那条路径。
"""

import logging
import threading
import time

import cv2

from camera import FrameSlot
from detector import get_detector

logger = logging.getLogger(__name__)

# 类别 -> BGR 颜色。与 Qt 客户端的 DetectionItem 保持一致，
# 避免同一个目标在两个界面上是两个颜色。
CLASS_COLORS = {
    "with_mask": (80, 190, 80),              # 绿：合规
    "without_mask": (60, 60, 220),           # 红：违规
    "mask_weared_incorrect": (40, 180, 220), # 黄：警告
}
FALLBACK_COLOR = (200, 200, 200)
JPEG_QUALITY = 80


def draw_detections(frame, detections):
    """在帧上画检测框，返回**原地修改后**的帧。

    刻意用 cv2 原语而不是 PIL：
      - cv2.rectangle/putText 实测 0.12 ms
      - 文字是 ASCII 的类别名（with_mask 等）；中文要渲染得换 PIL + 字体文件，
        而实时画面上每帧多花十几毫秒不值得。Qt 客户端那边用系统字体渲染中文，
        没有这个限制。
    """
    for det in detections:
        x1 = int(det["x1"]); y1 = int(det["y1"])
        x2 = int(det["x2"]); y2 = int(det["y2"])
        color = CLASS_COLORS.get(det["class_name"], FALLBACK_COLOR)

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        label = "%s %.2f" % (det["class_name"], det["confidence"])
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        # 标签条；如果框顶挨着画面顶部，就把标签画到框内，避免被裁掉
        ty = y1 - th - 6 if y1 - th - 6 >= 0 else y1 + 2
        cv2.rectangle(frame, (x1, ty), (x1 + tw + 6, ty + th + 6), color, -1)
        cv2.putText(frame, label, (x1 + 3, ty + th + 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    return frame


def draw_osd(frame, fps, queue_ms, detections, extra=""):
    """画角标：帧率 / 延迟 / 目标数。上位机上这些数字是必需品，不是装饰。"""
    h = frame.shape[0]
    lines = [
        "%.1f FPS" % fps,
        "%.0f ms" % queue_ms,
        "targets %d" % len(detections),
    ]
    if extra:
        lines.append(extra)

    for i, text in enumerate(lines):
        y = 20 + i * 20
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(frame, (6, y - th - 4), (12 + tw, y + 4), (0, 0, 0), -1)
        cv2.putText(frame, text, (9, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (0, 255, 255), 1, cv2.LINE_AA)
    return frame


class LivePipeline:
    """一个视频源的实时推理：采集 -> 推理 -> 画框 -> JPEG。

    输出放在 FrameSlot 里（latest-frame-wins），推流端只取最新那帧。
    观看者慢不会拖累推理 —— 这与采集端是同一个设计理念。
    """

    def __init__(self, source, model_name=None, confidence=0.25, iou=0.45,
                 imgsz=640, target_fps=30.0, draw=True):
        self._source = source
        self._model_name = model_name
        self._confidence = confidence
        self._iou = iou
        self._imgsz = imgsz
        self._target_interval = 1.0 / target_fps if target_fps > 0 else 0.0
        self._draw = draw

        self._frames = FrameSlot()          # 输出：JPEG bytes
        self._results = FrameSlot()         # 输出：结构化结果（供统计/告警）
        self._thread = None
        self._running = False
        self._stats_lock = threading.Lock()
        self._processed = 0
        self._latest_result = None      # 最近一次结构化结果（供 stats 查询，不消费）
        self._infer_ms = 0.0
        self._e2e_ms = 0.0
        self._last_error = ""
        self._next_at = 0.0

    # ------------------------------------------------------------ 开关
    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="live-infer", daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None

    # ------------------------------------------------------------ 主循环
    def _loop(self):
        detector = get_detector()
        while self._running:
            seq, frame, ts = self._source.read_latest()
            if frame is None:
                time.sleep(0.002)          # 没有新帧，别空转烧 CPU
                continue

            # 限制推理节奏：GPU 空着也没必要超过目标帧率，
            # 留出算力给 HTTP /detect 请求（两边共用一把推理锁）
            if self._target_interval > 0:
                now = time.time()
                if now < self._next_at:
                    time.sleep(min(self._next_at - now, 0.05))
                self._next_at = max(now, self._next_at) + self._target_interval

            try:
                t0 = time.time()
                result = detector.run_inference(
                    image_data=frame, model_name=self._model_name,
                    confidence=self._confidence, iou=self._iou,
                    imgsz=self._imgsz, annotated=False,
                    quiet=True,          # 每帧都打日志会刷屏（30fps = 30 行/秒）
                )
                infer_ms = (time.time() - t0) * 1000

                detections = result.get("detections", [])
                out = frame
                if self._draw:
                    out = draw_detections(frame, detections)

                ok, buf = cv2.imencode(".jpg", out,
                                       [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
                if not ok:
                    continue

                e2e_ms = (time.time() - ts) * 1000
                with self._stats_lock:
                    self._processed += 1
                    self._infer_ms = infer_ms
                    self._e2e_ms = e2e_ms
                    self._last_error = ""

                payload = {
                    "seq": seq,
                    "ts": ts,
                    "jpeg": buf.tobytes(),
                    "fps": self._source.fps,
                    "e2e_ms": e2e_ms,
                }
                self._frames.put(payload)
                entry = {
                    "seq": seq, "ts": ts, "detections": detections,
                    "counts": result.get("counts", {}),
                    "total": result.get("total_detections", 0),
                }
                self._results.put(entry)
                with self._stats_lock:
                    self._latest_result = entry

            except Exception as exc:                   # noqa: BLE001
                with self._stats_lock:
                    self._last_error = str(exc)
                logger.exception("实时推理失败")
                time.sleep(0.1)                        # 别在异常里空转

    # ------------------------------------------------------------ 读取
    def peek_frame(self):
        """取最新标注帧（不消费）。"""
        return self._frames.peek()

    def wait_frame(self, since_seq, timeout=1.0):
        """等一帧比 since_seq 更新的标注帧。推流端用它替代轮询。"""
        return self._frames.wait_newer(since_seq, timeout)

    def read_result(self):
        """取最新结构化结果（消费）。统计/告警用。"""
        return self._results.get()

    def stats(self):
        seq, payload, _ = self._frames.peek()
        with self._stats_lock:
            return {
                "running": self._running,
                "processed": self._processed,
                "out_seq": seq,
                "infer_ms": round(self._infer_ms, 1),
                "e2e_ms": round(self._e2e_ms, 1),
                "dropped_frames": self._frames.dropped,
                "jpeg_kb": round(len(payload["jpeg"]) / 1024, 1) if payload else 0,
                "last_error": self._last_error,
                "latest": self._latest_result,
            }
