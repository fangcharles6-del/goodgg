"""数据模型 — 剪贴板记录的数据类定义。"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ClipboardItem:
    """代表一条剪贴板记录。"""
    id: int
    content_type: str  # 'text' 或 'image'
    content_text: Optional[str] = None
    image_blob: Optional[bytes] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    content_hash: str = ""
    is_pinned: bool = False
    created_at: str = ""
    last_used_at: Optional[str] = None
    source_app: Optional[str] = None

    @property
    def is_text(self) -> bool:
        return self.content_type == 'text'

    @property
    def is_image(self) -> bool:
        return self.content_type == 'image'

    @property
    def preview_text(self) -> str:
        """返回用于卡片预览的文字（最多 120 字符）。"""
        if not self.content_text:
            return ""
        text = self.content_text.replace('\n', ' ').replace('\r', ' ')
        if len(text) > 120:
            return text[:120] + "..."
        return text


@dataclass
class AppConfig:
    """应用配置。"""
    retention_days: int = 3  # 1, 3, 5
    compress_images: bool = True
    hotkey_modifiers: int = 0x0002 | 0x0004  # MOD_CONTROL | MOD_SHIFT
    hotkey_vk: int = 0x56  # 'V'
