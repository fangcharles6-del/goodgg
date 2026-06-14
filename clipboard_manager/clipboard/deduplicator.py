"""去重处理 — 对剪贴板内容进行哈希去重后存入数据库。"""

import logging
from typing import Optional

from PySide6.QtGui import QImage

from database.repository import ClipboardRepository
from .hash_utils import hash_text, hash_bytes
from .compressor import compress_image

logger = logging.getLogger(__name__)

# 文字内容最大字符数
MAX_TEXT_LENGTH = 100_000


class Deduplicator:
    """剪贴板内容去重处理器。"""

    def __init__(self, repo: ClipboardRepository) -> None:
        self._repo = repo

    def process_text(self, text: str, source_app: Optional[str] = None) -> bool:
        """
        处理文字内容：去重后存入数据库。
        返回 True 表示新内容，False 表示跳过（空白或重复）。
        """
        # 跳过空内容
        stripped = text.strip()
        if not stripped:
            return False

        # 截断超大文字
        if len(stripped) > MAX_TEXT_LENGTH:
            stripped = stripped[:MAX_TEXT_LENGTH]
            logger.warning("文字内容已截断至 %d 字符", MAX_TEXT_LENGTH)

        # 哈希去重
        content_hash = hash_text(stripped)
        self._repo.upsert(
            content_hash=content_hash,
            content_type='text',
            content_text=stripped,
            source_app=source_app,
        )
        return True

    def process_image(
        self,
        image: QImage,
        compress: bool = True,
        source_app: Optional[str] = None,
    ) -> bool:
        """
        处理图片内容：压缩、去重后存入数据库。
        返回 True 表示新内容，False 表示失败或重复。
        """
        if image.isNull():
            return False

        try:
            if compress:
                jpeg_bytes, width, height = compress_image(image, quality=60)
            else:
                # 不压缩，直接转 PNG
                from .compressor import qimage_to_png_bytes
                jpeg_bytes = qimage_to_png_bytes(image)
                width, height = image.width(), image.height()

            # 哈希去重
            content_hash = hash_bytes(jpeg_bytes)
            self._repo.upsert(
                content_hash=content_hash,
                content_type='image',
                image_blob=jpeg_bytes,
                image_width=width,
                image_height=height,
                source_app=source_app,
            )
            return True

        except ValueError as e:
            logger.warning("图片处理跳过: %s", e)
            return False
        except Exception as e:
            logger.error("图片处理失败: %s", e)
            return False
