"""剪贴板数据的 CRUD 操作。"""

import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from PySide6.QtCore import QObject, Signal

from .models import ClipboardItem

logger = logging.getLogger(__name__)


class ClipboardRepository(QObject):
    """管理 clipboard_items 表的所有读写操作。"""

    items_changed = Signal()  # 数据变更时发出，UI 刷新用

    def __init__(self, db_path: str, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    # ── 查询 ─────────────────────────────────────────────

    def get_all(
        self,
        *,
        pinned_only: bool = False,
        search: str = "",
        limit: int = 200,
        offset: int = 0,
    ) -> list['ClipboardItem']:
        """获取记录列表。默认按 created_at 降序但不包含置顶项（置顶单独查询）。"""
        conn = self._connect()
        try:
            conditions = []
            params: list = []

            if pinned_only:
                conditions.append("is_pinned = 1")
            else:
                conditions.append("is_pinned = 0")

            if search:
                conditions.append("content_text LIKE ?")
                params.append(f"%{search}%")

            where = " AND ".join(conditions)
            sql = (
                f"SELECT * FROM clipboard_items WHERE {where} "
                "ORDER BY created_at DESC LIMIT ? OFFSET ?"
            )
            params.extend([limit, offset])

            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_item(r) for r in rows]
        finally:
            conn.close()

    def get_pinned(self) -> list['ClipboardItem']:
        """获取所有置顶记录，按 last_used_at 降序排列。"""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM clipboard_items WHERE is_pinned = 1 "
                "ORDER BY last_used_at DESC"
            ).fetchall()
            return [self._row_to_item(r) for r in rows]
        finally:
            conn.close()

    def get_by_id(self, item_id: int) -> Optional['ClipboardItem']:
        """按 ID 获取单条记录。"""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM clipboard_items WHERE id = ?", (item_id,)
            ).fetchone()
            if row is None:
                return None
            return self._row_to_item(row)
        finally:
            conn.close()

    def get_count(self, search: str = "") -> int:
        """获取记录总数。"""
        conn = self._connect()
        try:
            if search:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM clipboard_items WHERE content_text LIKE ?",
                    (f"%{search}%",),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM clipboard_items"
                ).fetchone()
            return row["cnt"] if row else 0
        finally:
            conn.close()

    # ── 写入 ─────────────────────────────────────────────

    def upsert(
        self,
        content_hash: str,
        content_type: str,
        content_text: Optional[str] = None,
        image_blob: Optional[bytes] = None,
        image_width: Optional[int] = None,
        image_height: Optional[int] = None,
        source_app: Optional[str] = None,
    ) -> int:
        """
        插入或更新记录。
        - 如果哈希已存在：更新 created_at 和 last_used_at（"顶到最上面"）
        - 如果哈希不存在：插入新行
        返回记录的 id。
        """
        now = datetime.now(timezone.utc).isoformat()
        conn = self._connect()
        try:
            existing = conn.execute(
                "SELECT id, is_pinned FROM clipboard_items WHERE content_hash = ?",
                (content_hash,),
            ).fetchone()

            if existing:
                # 已存在：更新时间（顶到最上面）
                conn.execute(
                    "UPDATE clipboard_items SET created_at = ?, last_used_at = ? WHERE id = ?",
                    (now, now, existing["id"]),
                )
                conn.commit()
                self.items_changed.emit()
                return existing["id"]
            else:
                # 新记录
                cursor = conn.execute(
                    """INSERT INTO clipboard_items
                       (content_type, content_text, image_blob, image_width, image_height,
                        content_hash, created_at, last_used_at, source_app)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        content_type,
                        content_text,
                        image_blob,
                        image_width,
                        image_height,
                        content_hash,
                        now,
                        now,
                        source_app,
                    ),
                )
                conn.commit()
                self.items_changed.emit()
                return cursor.lastrowid
        finally:
            conn.close()

    # ── 更新 ─────────────────────────────────────────────

    def set_pinned(self, item_id: int, pinned: bool) -> None:
        """设置/取消置顶。"""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE clipboard_items SET is_pinned = ?, last_used_at = ? WHERE id = ?",
                (1 if pinned else 0, now, item_id),
            )
            conn.commit()
            self.items_changed.emit()
        finally:
            conn.close()

    def mark_used(self, item_id: int) -> None:
        """标记为已使用（更新 last_used_at）。"""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE clipboard_items SET last_used_at = ? WHERE id = ?",
                (now, item_id),
            )
            conn.commit()
        finally:
            conn.close()

    # ── 删除 ─────────────────────────────────────────────

    def delete(self, item_id: int) -> None:
        """删除单条记录。"""
        conn = self._connect()
        try:
            conn.execute("DELETE FROM clipboard_items WHERE id = ?", (item_id,))
            conn.commit()
            self.items_changed.emit()
        finally:
            conn.close()

    def delete_expired(self, retention_days: int) -> int:
        """
        删除过期记录（排除置顶）。
        返回删除的行数。
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        cutoff_str = cutoff.isoformat()
        conn = self._connect()
        try:
            cursor = conn.execute(
                "DELETE FROM clipboard_items WHERE is_pinned = 0 AND created_at < ?",
                (cutoff_str,),
            )
            conn.commit()
            deleted = cursor.rowcount
            if deleted > 0:
                logger.info("清理了 %d 条过期记录", deleted)
                self.items_changed.emit()
            return deleted
        finally:
            conn.close()

    # ── 设置 ─────────────────────────────────────────────

    def get_setting(self, key: str, default: str = "") -> str:
        """读取设置项。"""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else default
        finally:
            conn.close()

    def set_setting(self, key: str, value: str) -> None:
        """写入/更新设置项。"""
        conn = self._connect()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )
            conn.commit()
        finally:
            conn.close()

    # ── 内部工具 ─────────────────────────────────────────

    @staticmethod
    def _row_to_item(row: sqlite3.Row) -> 'ClipboardItem':
        return ClipboardItem(
            id=row["id"],
            content_type=row["content_type"],
            content_text=row["content_text"],
            image_blob=row["image_blob"],
            image_width=row["image_width"],
            image_height=row["image_height"],
            content_hash=row["content_hash"],
            is_pinned=bool(row["is_pinned"]),
            created_at=row["created_at"],
            last_used_at=row["last_used_at"],
            source_app=row["source_app"],
        )
