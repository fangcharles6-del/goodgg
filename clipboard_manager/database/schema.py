"""数据库表结构定义与迁移。"""

import sqlite3
import logging

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA auto_vacuum = FULL;

CREATE TABLE IF NOT EXISTS clipboard_items (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    content_type  TEXT NOT NULL CHECK (content_type IN ('text', 'image')),
    content_text  TEXT,
    image_blob    BLOB,
    image_width   INTEGER,
    image_height  INTEGER,
    content_hash  TEXT NOT NULL UNIQUE,
    is_pinned     INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL,
    last_used_at  TEXT,
    source_app    TEXT
);

CREATE INDEX IF NOT EXISTS idx_items_created
    ON clipboard_items (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_items_pinned
    ON clipboard_items (is_pinned) WHERE is_pinned = 1;

CREATE INDEX IF NOT EXISTS idx_items_content_type
    ON clipboard_items (content_type);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


def migrate(db_path: str) -> None:
    """确保数据库表存在。首次运行时创建，后续运行无影响。"""
    try:
        conn = sqlite3.connect(db_path)
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        conn.close()
        logger.info("数据库迁移完成: %s", db_path)
    except sqlite3.DatabaseError as e:
        logger.error("数据库迁移失败: %s", e)
        # 尝试重命名损坏的数据库
        import os
        bak_path = db_path + ".bak"
        os.replace(db_path, bak_path)
        logger.warning("已损坏的数据库已重命名为 %s，将创建新数据库", bak_path)
        conn = sqlite3.connect(db_path)
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        conn.close()
