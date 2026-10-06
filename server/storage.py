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
from datetime import date, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("FMD_DATA_DIR", ROOT_DIR / "data"))
DB_PATH = Path(os.environ.get("FMD_DB_PATH", DATA_DIR / "history.db"))
UPLOAD_DIR = DATA_DIR / "uploads"

# 上传原图的保留策略。
#
# 背景：每检测一次就存一份原图，如果没有上限，跑几千次就能撑到 GB 级
# （实测 2653 次检测累积了 985 MB）。这里给两道闸：
#   1. 按天数：超过 RETENTION_DAYS 的原图删掉
#   2. 按容量：删完天数后如果仍超过 MAX_MB，从最旧的开始继续删
# 只删原图，不动数据库记录 —— 检测结果（框、类别、耗时）比原图有价值，
# 原图丢了只是详情页看不到图，统计数据不受影响。
UPLOAD_RETENTION_DAYS = int(os.environ.get("FMD_UPLOAD_RETENTION_DAYS", "30"))
UPLOAD_MAX_MB = int(os.environ.get("FMD_UPLOAD_MAX_MB", "2048"))

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

    def _remove_image(self, rel_path):
        """删除 uploads 下的一张原图。rel_path 是相对 DATA_DIR 的路径。"""
        if not rel_path:
            return False
        try:
            target = (DATA_DIR / rel_path).resolve()
            # 防目录穿越：只允许删 uploads 之内的文件
            if UPLOAD_DIR.resolve() not in target.parents:
                logger.warning("拒绝删除 uploads 之外的路径: %s", target)
                return False
            if target.is_file():
                target.unlink()
                return True
        except OSError as exc:
            logger.warning("删除原图失败 %s: %s", rel_path, exc)
        return False

    def delete_record(self, record_id):
        conn = self._connect()
        row = conn.execute(
            "SELECT image_path FROM detection_records WHERE id = ?", (int(record_id),)
        ).fetchone()
        cur = conn.execute("DELETE FROM detection_records WHERE id = ?", (int(record_id),))
        conn.commit()
        # 同步删掉原图 —— 此前只删数据库行，图片会永久留在磁盘上
        if cur.rowcount > 0 and row is not None:
            self._remove_image(row["image_path"])
        return cur.rowcount > 0

    def clear_all(self):
        conn = self._connect()
        cur = conn.execute("DELETE FROM detection_records")
        conn.commit()
        self._prune_upload_dir()
        return cur.rowcount

    def _prune_upload_dir(self):
        """删光 uploads 下的所有文件与空目录。"""
        if not UPLOAD_DIR.exists():
            return 0
        removed = 0
        for path in UPLOAD_DIR.rglob("*"):
            if path.is_file():
                try:
                    path.unlink()
                    removed += 1
                except OSError as exc:
                    logger.warning("删除 %s 失败: %s", path, exc)
        self._prune_empty_dirs()
        logger.info("已清空 uploads，删除 %d 个文件", removed)
        return removed

    def _prune_empty_dirs(self):
        """删掉 uploads 下的空日期目录。不删的话 YYYY/MM/DD 骨架会越积越多。"""
        if not UPLOAD_DIR.exists():
            return
        for path in sorted(UPLOAD_DIR.rglob("*"), key=lambda p: len(p.parts), reverse=True):
            if path.is_dir():
                try:
                    path.rmdir()
                except OSError:
                    pass   # 非空，留着

    def _dated_dirs(self):
        """列出 uploads/YYYY/MM/DD 形式的日期目录，返回 [(date, Path), ...]。"""
        found = []
        for year in UPLOAD_DIR.glob("*"):
            if not (year.is_dir() and len(year.name) == 4 and year.name.isdigit()):
                continue
            for month in year.glob("*"):
                if not (month.is_dir() and len(month.name) == 2 and month.name.isdigit()):
                    continue
                for day in month.glob("*"):
                    if not (day.is_dir() and len(day.name) == 2 and day.name.isdigit()):
                        continue
                    try:
                        found.append((date(int(year.name), int(month.name), int(day.name)), day))
                    except ValueError:
                        continue   # 目录名不是合法日期，跳过
        return found

    @staticmethod
    def _remove_tree(path):
        """删除整个目录树，返回 (文件数, 总字节)。

        用 os.scandir 单次遍历同时完成统计与删除：
        DirEntry 在 Windows 上直接携带文件大小（来自 FindFirstFile/FindNextFile），
        所以 entry.stat() 不需要额外系统调用；而 Path.rglob() 产出的 Path 对象
        再调 .stat() 会多问一次内核。（实测 scandir 枚举 2000 个文件 < 1 ms，
        真正的开销在 unlink —— 见 cleanup_uploads 的说明。）
        """
        count = 0
        size = 0
        stack = [Path(path)]
        visited_dirs = []

        while stack:
            current = stack.pop()
            visited_dirs.append(current)
            try:
                with os.scandir(current) as it:
                    for entry in it:
                        try:
                            if entry.is_dir(follow_symlinks=False):
                                stack.append(Path(entry.path))
                            elif entry.is_file(follow_symlinks=False):
                                size += entry.stat(follow_symlinks=False).st_size
                                count += 1
                                os.unlink(entry.path)
                        except OSError:
                            pass
            except OSError:
                pass

        # 自底向上删空目录
        for item in sorted(visited_dirs, key=lambda p: len(p.parts), reverse=True):
            try:
                os.rmdir(item)
            except OSError:
                pass
        return count, size

    def cleanup_uploads(self, retention_days=None, max_mb=None):
        """按保留策略清理原图，返回 (删除文件数, 释放字节数)。

        服务启动时在后台线程调用（见 app.py）。
        
        实现要点：uploads 的目录结构是 YYYY/MM/DD，**目录名本身就是内容日期**，
        所以判断"是否过期"不需要读文件时间 —— 整个日期目录过期就整体删掉。
        这比逐文件判断 mtime 少一轮遍历。

        ⚠ 性能实测（重要，避免后人误判）：
        删除速度**由运行环境决定，不是这段代码决定的**。实测 2000 个小文件：
          %TEMP% 下          约 1.2 ms/个（约 2.4 秒）
          普通目录下          约 15 ms/个 （约 31 秒）
        同一个脚本、同一块 C 盘，只有 %TEMP% 快 —— 差异来自 Windows Defender
        的实时扫描（TEMP 通常在排除列表里）。项目目录、data/uploads、
        甚至 C 盘根目录，速度完全一致。

        因此：
          1. 不要试图用"改算法"来消掉这 15 ms/个，它是环境开销
          2. 清理必须放在后台线程（见 app.py），否则启动会被拖住几十秒
          3. 中断是安全的：删除按目录从旧到新推进，下次启动接着删
        """
        if not UPLOAD_DIR.exists():
            return (0, 0)

        days = UPLOAD_RETENTION_DAYS if retention_days is None else int(retention_days)
        limit_bytes = (UPLOAD_MAX_MB if max_mb is None else int(max_mb)) * 1024 * 1024
        deadline = date.today() - timedelta(days=days)

        removed = 0
        freed = 0

        # ---- 第一道闸：按日期，整目录删 ----
        for day_date, day_dir in self._dated_dirs():
            if day_date >= deadline:
                continue
            count, size = self._remove_tree(day_dir)
            removed += count
            freed += size

        # ---- 第二道闸：仍超容量时，从最旧的目录继续删 ----
        survivors = sorted(self._dated_dirs(), key=lambda item: item[0])
        total = 0
        for _, day_dir in survivors:
            try:
                with os.scandir(day_dir) as it:
                    for entry in it:
                        if entry.is_file(follow_symlinks=False):
                            total += entry.stat(follow_symlinks=False).st_size
            except OSError:
                pass

        for _, day_dir in survivors:
            if total <= limit_bytes:
                break
            count, actual = self._remove_tree(day_dir)
            removed += count
            freed += actual
            total -= actual

        if removed:
            self._prune_empty_dirs()
            logger.info("原图保留策略：删除 %d 个文件，释放 %.1f MB（保留 %d 天 / 上限 %d MB）",
                        removed, freed / 1024 / 1024, days, UPLOAD_MAX_MB)
        return (removed, freed)

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
