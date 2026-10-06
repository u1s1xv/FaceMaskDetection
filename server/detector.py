"""
YOLO 推理内核 —— 从 django_frontend/detection/services.py:290-616 移植。

相对原版的改动（仅此三处）：
  1. Django settings.YOLO_* 路径 -> 本模块的路径常量（可用环境变量覆盖）
  2. 移除 Django cache 的缓存读写（桌面端同一张图不会重复推理）
  3. 类别名不再硬编码，改为从加载的 checkpoint 自带 names 读取（单一来源）

推理逻辑本身（ultralytics predict + cv2 画框）与原版完全一致。
"""

import hashlib
import io
import logging
import os
import threading
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------- 路径
# server/ 的上一级就是仓库根目录，零硬编码绝对路径
ROOT_DIR = Path(__file__).resolve().parent.parent
YOLO_ROOT = Path(os.environ.get("FMD_YOLO_ROOT", ROOT_DIR / "yoloserver"))
MODELS_DIR = Path(os.environ.get("FMD_MODELS_DIR", YOLO_ROOT / "models" / "checkpoints"))

# 类别名 -> 旧数据模型的计数字段（保持与 Django 版 DetectionRecord 列名一致）
COUNT_FIELDS = {
    "with_mask": "with_mask_count",
    "without_mask": "without_mask_count",
    "mask_weared_incorrect": "incorrect_mask_count",
}

# 类别名 -> 画框颜色 (BGR)。按名字而不是按 id，避免类别顺序变化导致颜色错乱
CLASS_COLORS = {
    "with_mask": (0, 255, 0),              # 绿 - 正确佩戴
    "without_mask": (0, 0, 255),           # 红 - 未佩戴
    "mask_weared_incorrect": (0, 255, 255),  # 黄 - 佩戴不规范
}
DEFAULT_COLOR = (255, 255, 255)


class Detector:
    """在内存中常驻 YOLO 模型的推理服务。"""

    def __init__(self, models_dir=None):
        self.models_dir = Path(models_dir) if models_dir else MODELS_DIR
        # 模型缓存：普通 dict，不是 Django cache
        self._models = {}
        self._model_lock = threading.Lock()

        # 推理串行锁。
        # ultralytics 的 YOLO 实例不是线程安全的，而且单张 GPU 本来也只能
        # 一次跑一个推理。HTTP 层是多线程的（ThreadingHTTPServer），
        # 如果不在这里串行化，并发请求会互相踩踏导致推理失败。
        # 客户端的高并发因此只体现为"排队"，而不是真并行 —— 排队耗时会被
        # 记进结果的 queue_wait 字段，便于做并发调优的实测对比。
        self._infer_lock = threading.Lock()
        logger.info("推理服务初始化完成，模型目录: %s", self.models_dir)

    # ------------------------------------------------------------ 模型管理
    def list_models(self):
        """扫描模型目录，返回可用权重列表。"""
        models = []
        if not self.models_dir.exists():
            logger.warning("模型目录不存在: %s", self.models_dir)
            return models

        for path in sorted(self.models_dir.glob("*.pt")):
            stat = path.stat()
            models.append({
                "name": path.name,
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / 1024 / 1024, 2),
                "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
            })
        return models

    def _resolve_model_path(self, model_name):
        """把模型名解析成绝对路径；已经是绝对路径则直接用。"""
        if not model_name:
            candidates = sorted(self.models_dir.glob("*.pt"))
            preferred = [p for p in candidates if p.name.endswith("_best.pt")]
            if preferred:
                return preferred[0]
            if candidates:
                return candidates[0]
            raise FileNotFoundError(f"模型目录中没有 .pt 文件: {self.models_dir}")

        path = Path(model_name)
        if path.is_absolute():
            return path
        return self.models_dir / model_name

    def _load_model(self, model_name):
        """加载并缓存模型（线程安全）。"""
        model_path = self._resolve_model_path(model_name)
        key = str(model_path)

        with self._model_lock:
            if key not in self._models:
                from ultralytics import YOLO

                if not model_path.exists():
                    raise FileNotFoundError(f"模型文件不存在: {model_path}")

                logger.info("加载模型: %s", model_path)
                t0 = time.time()
                model = YOLO(str(model_path))
                self._models[key] = model
                logger.info("模型加载完成，耗时 %.2fs，类别: %s", time.time() - t0, model.names)

            return self._models[key]

    # ------------------------------------------------------------ 推理
    def run_inference(self, image_path=None, image_data=None, model_name=None,
                      confidence=0.25, iou=0.45, imgsz=640, annotated=True,
                      quiet=False):
        """执行一次推理。

        Args:
            image_path: 图像路径（与 image_data 二选一）
            image_data: 内存图像（numpy 数组或 PIL Image）
            model_name: 权重文件名；留空则自动挑 *_best.pt
            annotated:  是否生成标注图（批量时可关掉省时间）
            quiet:      不写日志。实时路径每帧都调，默认日志会刷屏（30fps 下 30 行/秒）

        Returns:
            dict: 结构化结果
        """
        start_time = time.time()

        if image_path:
            source = str(image_path)
        elif image_data is not None:
            source = image_data
        else:
            raise ValueError("必须提供 image_path 或 image_data 参数")

        model = self._load_model(model_name)

        # 排队等待时间：并发越高这个值越大，是并发调优的直接依据
        wait_start = time.time()
        with self._infer_lock:
            queue_wait = time.time() - wait_start
            infer_start = time.time()

            results = model.predict(
                source=source,
                imgsz=imgsz,
                conf=confidence,
                iou=iou,
                save=False,
                verbose=False,
            )

            result = self._process_results(results, source, infer_start,
                                           model.names, annotated)

        result["queue_wait"] = queue_wait
        result["total_time"] = time.time() - start_time
        if not quiet:
            logger.info("推理完成: 排队 %.0f ms, 推理 %.0f ms",
                        queue_wait * 1000, result["processing_time"] * 1000)
        return result

    # ------------------------------------------------------------ 结果处理
    def _process_results(self, results, image_path, start_time, class_names, annotated=True):
        """把 ultralytics 的结果对象转成可序列化的 dict。"""
        result_data = {
            "processing_time": time.time() - start_time,
            "total_detections": 0,
            "with_mask_count": 0,
            "without_mask_count": 0,
            "incorrect_mask_count": 0,
            "counts": {},
            "detections": [],
            "model_classes": {str(k): v for k, v in (class_names or {}).items()},
        }

        if results and len(results) > 0:
            result = results[0]
            height, width = result.orig_shape
            result_data["image_width"] = width
            result_data["image_height"] = height

            if result.boxes is not None and len(result.boxes) > 0:
                boxes = result.boxes
                for i in range(len(boxes)):
                    class_id = int(boxes.cls[i].item())
                    confidence = float(boxes.conf[i].item())
                    x1, y1, x2, y2 = boxes.xyxy[i].tolist()
                    class_name = (class_names or {}).get(class_id, "unknown")

                    result_data["detections"].append({
                        "class_id": class_id,
                        "class_name": class_name,
                        # 像素坐标（Qt 端直接用来画框）
                        "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                        # 归一化的 YOLO 格式（兼容旧数据）
                        "x_center": (x1 + x2) / 2 / width,
                        "y_center": (y1 + y2) / 2 / height,
                        "width": (x2 - x1) / width,
                        "height": (y2 - y1) / height,
                        "confidence": confidence,
                    })

                    result_data["counts"][class_name] = result_data["counts"].get(class_name, 0) + 1
                    field = COUNT_FIELDS.get(class_name)
                    if field:
                        result_data[field] += 1

            result_data["total_detections"] = len(result_data["detections"])

            if annotated:
                image_bytes = self._create_beautified_image(result, result_data["detections"])
                if image_bytes is not None:
                    result_data["beautified_image_data"] = image_bytes

        return result_data

    def _create_beautified_image(self, result, detections):
        """在原图上画框和标签，返回 PNG 字节。按类别名取色。"""
        img = result.orig_img.copy()
        img_height, img_width = img.shape[:2]

        for detection in detections:
            class_name = detection["class_name"]
            confidence = detection["confidence"]

            x1 = int(detection["x1"])
            y1 = int(detection["y1"])
            x2 = int(detection["x2"])
            y2 = int(detection["y2"])
            color = CLASS_COLORS.get(class_name, DEFAULT_COLOR)

            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

            label = f"{class_name}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(img, (x1, y1 - label_size[1] - 10),
                          (x1 + label_size[0], y1), color, -1)
            cv2.putText(img, label, (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        return buf.getvalue()


# ---------------------------------------------------------------- 单例
_instance = None
_instance_lock = threading.Lock()


def get_detector():
    """进程内单例，保证模型只加载一次。"""
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = Detector()
    return _instance
