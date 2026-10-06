"""
FaceMaskDetection 推理服务 —— 给 Qt/C++ 客户端用的 HTTP 门面。

只用 Python 标准库（http.server + sqlite3），零第三方依赖。
设计取舍：
  * POST /detect 的 body 直接是图像原始字节，不用 multipart ——
    Qt 侧 QNetworkAccessManager 直接 post(QByteArray) 即可。
  * 参数走 query string，结果走 JSON。
  * 每次推理自动落一条历史记录（save=0 可关闭）。
"""

import argparse
import base64
import json
import logging
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import cv2
import numpy as np

from detector import get_detector, MODELS_DIR
from llm import stream_analysis, api_key_configured, AVAILABLE_MODELS, DEFAULT_MODEL
from storage import get_store, DB_PATH, UPLOAD_DIR, DATA_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("fmd.server")

API_VERSION = "0.2.0"


def _as_bool(value, default=True):
    if value is None:
        return default
    return str(value).lower() not in ("0", "false", "no", "")


class Handler(BaseHTTPRequestHandler):
    server_version = "FMD/" + API_VERSION
    protocol_version = "HTTP/1.1"

    # ---------------------------------------------------------- 工具
    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length) if length > 0 else b""

    def log_message(self, fmt, *args):
        logger.info("%s - %s", self.address_string(), fmt % args)

    @staticmethod
    def _segments(path):
        return [s for s in path.split("/") if s]

    @staticmethod
    def _one(query, name, default=None):
        values = query.get(name)
        return values[0] if values else default

    # ---------------------------------------------------------- GET
    def do_GET(self):
        parsed = urlparse(self.path)
        segs = self._segments(parsed.path)
        query = parse_qs(parsed.query)
        try:
            if segs == ["health"]:
                return self._health()
            if segs == ["models"]:
                return self._send_json({"success": True, "models": get_detector().list_models()})
            if segs == ["llm-models"]:
                return self._send_json({"success": True,
                                        "models": AVAILABLE_MODELS,
                                        "default": DEFAULT_MODEL,
                                        "api_key_configured": api_key_configured()})
            if segs == ["stats"]:
                return self._send_json({"success": True, "stats": get_store().stats()})
            if segs == ["history"]:
                data = get_store().list_records(
                    limit=int(self._one(query, "limit", 200)),
                    offset=int(self._one(query, "offset", 0)),
                    keyword=self._one(query, "keyword"),
                    status=self._one(query, "status"),
                )
                data["success"] = True
                return self._send_json(data)
            if len(segs) == 2 and segs[0] == "image":
                return self._serve_image(segs[1])
            if len(segs) == 2 and segs[0] == "history":
                record = get_store().get_record(segs[1])
                if record is None:
                    return self._send_json(
                        {"success": False, "error": "记录不存在"}, 404)
                return self._send_json({"success": True, "record": record})
            return self._send_json(
                {"success": False, "error": "未知路径: " + parsed.path}, 404)
        except Exception as exc:  # noqa: BLE001
            logger.exception("GET %s 失败", parsed.path)
            return self._send_json({"success": False, "error": str(exc)}, 500)

    def _serve_image(self, record_id):
        """按记录 id 返回原始上传图，供历史详情展示。"""
        record = get_store().get_record(record_id)
        if record is None:
            return self._send_json({"success": False, "error": "记录不存在"}, 404)

        rel = record.get("image_path")
        if not rel:
            return self._send_json({"success": False, "error": "该记录没有存图"}, 404)

        path = (DATA_DIR / rel).resolve()
        # 防目录穿越：必须落在 DATA_DIR 之内
        if not str(path).startswith(str(DATA_DIR.resolve())) or not path.exists():
            return self._send_json({"success": False, "error": "图片文件缺失"}, 404)

        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _health(self):
        info = {
            "status": "ok",
            "version": API_VERSION,
            "models_dir": str(MODELS_DIR),
            "db_path": str(DB_PATH),
        }
        try:
            import torch
            info["device"] = "cuda" if torch.cuda.is_available() else "cpu"
            info["torch"] = torch.__version__
            if torch.cuda.is_available():
                info["gpu"] = torch.cuda.get_device_name(0)
        except Exception as exc:  # noqa: BLE001
            info["device"] = "unknown"
            info["torch_error"] = str(exc)
        try:
            import ultralytics
            info["ultralytics"] = ultralytics.__version__
        except Exception:  # noqa: BLE001
            pass
        return self._send_json(info)

    # ---------------------------------------------------------- POST
    def do_POST(self):
        parsed = urlparse(self.path)
        segs = self._segments(parsed.path)
        query = parse_qs(parsed.query)
        try:
            if segs == ["detect"]:
                return self._detect(query)
            if segs == ["llm", "analyze"]:
                return self._llm_analyze()
            return self._send_json(
                {"success": False, "error": "未知路径: " + parsed.path}, 404)
        except Exception as exc:  # noqa: BLE001
            logger.exception("POST %s 失败", parsed.path)
            return self._send_json({"success": False, "error": str(exc)}, 500)

    def _detect(self, query):
        raw = self._read_body()
        if not raw:
            return self._send_json(
                {"success": False, "error": "请求体为空，需要图像原始字节"}, 400)

        image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            return self._send_json(
                {"success": False, "error": "图像解码失败（支持 jpg/png/bmp 等）"}, 400)

        model_name = self._one(query, "model")
        confidence = float(self._one(query, "conf", 0.25))
        iou        = float(self._one(query, "iou", 0.45))
        imgsz      = int(self._one(query, "imgsz", 640))
        want_image = _as_bool(self._one(query, "return_image"), True)
        save       = _as_bool(self._one(query, "save"), True)
        file_name  = self._one(query, "file_name") or "unknown"

        logger.info("推理请求: %dx%d, model=%s, conf=%s, iou=%s, imgsz=%s",
                    image.shape[1], image.shape[0], model_name, confidence, iou, imgsz)

        result = get_detector().run_inference(
            image_data=image,
            model_name=model_name,
            confidence=confidence,
            iou=iou,
            imgsz=imgsz,
            annotated=want_image,
        )

        payload = {"success": True}
        payload.update({k: v for k, v in result.items() if k != "beautified_image_data"})

        image_bytes = result.get("beautified_image_data")
        if image_bytes is not None:
            payload["annotated_image_b64"] = base64.b64encode(image_bytes).decode("ascii")
            payload["annotated_image_bytes"] = len(image_bytes)

        if save:
            try:
                store = get_store()
                image_path = store.save_image(raw, file_name)
                payload["record_id"] = store.add_record(
                    result, file_name=file_name,
                    model_name=model_name or "auto",
                    confidence=confidence, iou=iou, imgsz=imgsz,
                    image_path=image_path)
            except Exception:  # noqa: BLE001
                logger.exception("历史落库失败（不影响检测结果）")

        return self._send_json(payload)

    # ---------------------------------------------------------- LLM 流式
    def _llm_analyze(self):
        """SSE 流式返回分析文本。每帧形如： data: {"type":"content","text":"..."}\n\n"""
        raw = self._read_body()
        try:
            request = json.loads(raw.decode("utf-8")) if raw else {}
        except ValueError:
            return self._send_json({"success": False, "error": "请求体不是合法 JSON"}, 400)

        record_id = request.get("record_id")
        prompt    = request.get("prompt", "")
        model     = request.get("model") or DEFAULT_MODEL

        record = get_store().get_record(record_id) if record_id else None
        if record_id and record is None:
            return self._send_json(
                {"success": False, "error": f"记录 {record_id} 不存在"}, 404)
        if record is None:
            record = request.get("record") or {}

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()

        def send_frame(payload):
            body = ("data: " + json.dumps(payload, ensure_ascii=False) + "\n\n").encode("utf-8")
            self.wfile.write(body)
            self.wfile.flush()

        try:
            send_frame({"type": "start", "model": model,
                        "mock": not api_key_configured()})
            for piece in stream_analysis(record, prompt, model):
                send_frame({"type": "content", "text": piece})
            send_frame({"type": "done"})
        except Exception as exc:  # noqa: BLE001
            logger.exception("LLM 分析失败")
            try:
                send_frame({"type": "error", "error": str(exc)})
            except Exception:  # noqa: BLE001
                pass
        finally:
            self.close_connection = True

    # ---------------------------------------------------------- DELETE
    def do_DELETE(self):
        parsed = urlparse(self.path)
        segs = self._segments(parsed.path)
        query = parse_qs(parsed.query)
        try:
            if segs == ["history"]:
                if _as_bool(self._one(query, "all"), False):
                    removed = get_store().clear_all()
                    return self._send_json({"success": True, "removed": removed})
                return self._send_json(
                    {"success": False, "error": "需要 ?all=1 才允许清空全部记录"}, 400)
            if len(segs) == 2 and segs[0] == "history":
                ok = get_store().delete_record(segs[1])
                if not ok:
                    return self._send_json(
                        {"success": False, "error": "记录不存在"}, 404)
                return self._send_json({"success": True, "id": int(segs[1])})
            return self._send_json(
                {"success": False, "error": "未知路径: " + parsed.path}, 404)
        except Exception as exc:  # noqa: BLE001
            logger.exception("DELETE %s 失败", parsed.path)
            return self._send_json({"success": False, "error": str(exc)}, 500)


def main():
    parser = argparse.ArgumentParser(description="FaceMaskDetection 推理服务")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8756)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    logger.info("推理服务已启动: http://%s:%d", args.host, args.port)
    logger.info("模型目录: %s", MODELS_DIR)
    logger.info("历史库:   %s", DB_PATH)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("收到中断，正在关闭…")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
