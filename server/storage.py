"""
检测历史持久化 —— SQLite（Python 标准库 sqlite3，零依赖）。

替代原来 Django ORM 的 DetectionRecord / BatchDetectionSession / ModelConfig。
去掉了多用户相关的外键（桌面端单机，不需要账号体系），其余字段保持对应关系，
便于把老的 db.sqlite3 数据迁移过来。
"""

import json
import logging
import os
import sqlite3
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("FMD_DATA_DIR", ROOT_DIR / "data"))
DB_PATH = Path(os.environ.get("FMD_DB_PATH", DATA_DIR / "history.db"))
UPLOAD_DIR = DATA_DIR / "uploads"

SCHEMA = """
CREATE TABLE IF NOT EXISTS detection_records (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name            TEXT    NOT NULL,
    file_path            TEXT,
    image_width          INTEGER NOT NULL DEFAULT 0,
    image_height         INTEGER NOT NULL DEFAULT 0,
    model_name           TEXT,
    confidence           REAL    NOT NULL DEFAULT 0.25,
    iou                  REAL    NOT NULL DEFAULT 0.45,
    imgsz                INTEGER NOT NULL DEFAULT 640,
    total_detections     INTEGER NOT NULL DEFAULT 0,
    with_mask_count      INTEGER NOT NULL DEFAULT 0,
    without_mask_count   INTEGER NOT NULL DEFAULT 0,
    incorrect_mask_count INTEGER NOT NULL DEFAULT 0,
    processing_time      REAL    NOT NULL DEFAULT 0,
    queue_wait           REAL    NOT NULL DEFAULT 0,
    detections_json      TEXT,
    status               TEXT    NOT NULL DEFAULT 'completed',
    error_message        TEXT,
    image_path           TEXT,
    created_at           TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_records_created ON detection_records(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_records_status  ON detection_records(status);
"""


class HistoryStore:
    """线程安全的 SQLite 封装。HTTP 层是多线程的，所以用 thread-local 连接。"""

    def __init__(self, db_path=None):
        self.db_path = Path(db_path) if db_path else DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        with self._connect() as conn:
            conn.executescript(SCHEMA)
            self._migrate(conn)
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("历史库就绪: %s", self.db_path)

    @staticmethod
    def _migrate(conn):
        """老库补列。SQLite 的 ADD COLUMN 很便宜，重复执行也无害。"""
        existing = {row[1] for row in conn.execute("PRAGMA table_info(detection_records)")}
        for column, ddl in (("image_path", "TEXT"), ("queue_wait", "REAL NOT NULL DEFAULT 0")):
            if column not in existing:
                conn.execute(f"ALTER TABLE detection_records ADD COLUMN {column} {ddl}")
        conn.commit()

    def save_image(self, image_bytes, file_name):
        """把原图按日期分目录存盘，返回相对路径。"""
        stamp = time.strftime("%Y/%m/%d")
        target_dir = UPLOAD_DIR / stamp
        target_dir.mkdir(parents=True, exist_ok=True)

        safe = "".join(ch for ch in (file_name or "image.jpg") if ch.isalnum() or ch in "._-")
        if not safe:
            safe = "image.jpg"
        path = target_dir / f"{int(time.time() * 1000)}_{safe}"
        path.write_bytes(image_bytes)
        return str(path.relative_to(DATA_DIR)).replace("\\", "/")

    def _connect(self):
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(str(self.db_path), timeout=10)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn = conn
        return conn

    # ------------------------------------------------------------ 写入
    def add_record(self, result, file_name, file_path=None,
                   model_name=None, confidence=0.25, iou=0.45, imgsz=640,
                   image_path=None):
        """把一次推理结果落库，返回记录 id。"""
        conn = self._connect()
        cur = conn.execute(
            """INSERT INTO detection_records (
                   file_name, file_path, image_width, image_height,
                   model_name, confidence, iou, imgsz,
                   total_detections, with_mask_count, without_mask_count,
                   incorrect_mask_count, processing_time, queue_wait,
                   detections_json, status, image_path, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                file_name, file_path,
                int(result.get("image_width") or 0),
                int(result.get("image_height") or 0),
                model_name, float(confidence), float(iou), int(imgsz),
                int(result.get("total_detections") or 0),
                int(result.get("with_mask_count") or 0),
                int(result.get("without_mask_count") or 0),
                int(result.get("incorrect_mask_count") or 0),
                float(result.get("processing_time") or 0),
                float(result.get("queue_wait") or 0),
                json.dumps(result.get("detections") or [], ensure_ascii=False),
                "completed",
                image_path,
                time.strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        conn.commit()
        return cur.lastrowid

    # ------------------------------------------------------------ 查询
    def list_records(self, limit=200, offset=0, keyword=None, status=None):
        conn = self._connect()
        where, params = [], []
        if keyword:
            where.append("file_name LIKE ?")
            params.append(f"%{keyword}%")
        if status:
            where.append("status = ?")
            params.append(status)
        clause = ("WHERE " + " AND ".join(where)) if where else ""

        total = conn.execute(
            f"SELECT COUNT(*) FROM detection_records {clause}", params
        ).fetchone()[0]

        rows = conn.execute(
            f"""SELECT id, file_name, image_width, image_height, model_name,
                       confidence, iou, imgsz, total_detections,
                       with_mask_count, without_mask_count, incorrect_mask_count,
                       processing_time, queue_wait, status, image_path, created_at
                FROM detection_records {clause}
                ORDER BY id DESC LIMIT ? OFFSET ?""",
            params + [int(limit), int(offset)],
        ).fetchall()

        return {"total": total, "items": [dict(r) for r in rows]}

    def get_record(self, record_id):
        row = self._connect().execute(
            "SELECT * FROM detection_records WHERE id = ?", (int(record_id),)
        ).fetchone()
        if row is None:
            return None
        record = dict(row)
        try:
            record["detections"] = json.loads(record.pop("detections_json") or "[]")
        except (TypeError, ValueError):
            record["detections"] = []
        return record

    def delete_record(self, record_id):
        conn = self._connect()
        cur = conn.execute("DELETE FROM detection_records WHERE id = ?", (int(record_id),))
        conn.commit()
        return cur.rowcount > 0

    def clear_all(self):
        conn = self._connect()
        cur = conn.execute("DELETE FROM detection_records")
        conn.commit()
        return cur.rowcount

    def stats(self):
        conn = self._connect()
        row = conn.execute(
            """SELECT COUNT(*)                     AS total_records,
                      COALESCE(SUM(total_detections),0)     AS total_detections,
                      COALESCE(SUM(with_mask_count),0)      AS with_mask,
                      COALESCE(SUM(without_mask_count),0)   AS without_mask,
                      COALESCE(SUM(incorrect_mask_count),0) AS incorrect_mask,
                      COALESCE(AVG(processing_time),0)      AS avg_processing_time,
                      COALESCE(AVG(queue_wait),0)           AS avg_queue_wait
               FROM detection_records""",
        ).fetchone()
        return dict(row)


_store = None
_store_lock = threading.Lock()


def get_store():
    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                _store = HistoryStore()
    return _store
