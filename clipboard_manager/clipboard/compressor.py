"""图片压缩 — QImage → JPEG 字节。"""

import logging
from io import BytesIO

from PySide6.QtGui import QImage
from PySide6.QtCore import QBuffer, QByteArray, QIODevice

logger = logging.getLogger(__name__)

# 最大尺寸阈值
MAX_WIDTH = 1920
MAX_HEIGHT = 1080
# 最大原始大小 (50MB)
MAX_RAW_SIZE = 50 * 1024 * 1024


def qimage_to_png_bytes(image: QImage) -> bytes:
    """将 QImage 转为 PNG 字节（中间步骤）。"""
    byte_array = QByteArray()
    buffer = QBuffer(byte_array)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    buffer.close()
    return bytes(byte_array)


def compress_image(
    image: QImage,
    quality: int = 60,
) -> tuple[bytes, int, int]:
    """
    压缩图片：QImage → PNG 中间态 → PIL 压缩为 JPEG。

    返回 (jpeg_bytes, width, height)。
    """
    from PIL import Image

    # 先转为 PNG 字节
    png_bytes = qimage_to_png_bytes(image)

    # 检查大小上限
    if len(png_bytes) > MAX_RAW_SIZE:
        raise ValueError(f"图片原始大小 {len(png_bytes) / 1024 / 1024:.1f}MB 超过 50MB 上限，已跳过")

    # 用 PIL 打开
    pil_image = Image.open(BytesIO(png_bytes))

    # 如果尺寸过大，等比例缩放
    if pil_image.width > MAX_WIDTH or pil_image.height > MAX_HEIGHT:
        pil_image.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.Resampling.LANCZOS)
        logger.debug("图片已缩放至 %dx%d", pil_image.width, pil_image.height)

    # 转为 RGB（JPEG 不支持 RGBA）
    if pil_image.mode in ('RGBA', 'P', 'LA'):
        background = Image.new('RGB', pil_image.size, (255, 255, 255))
        if pil_image.mode == 'P':
            pil_image = pil_image.convert('RGBA')
        background.paste(pil_image, mask=pil_image.split()[-1] if pil_image.mode == 'RGBA' else None)
        pil_image = background
    elif pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')

    # 保存为 JPEG
    out_buffer = BytesIO()
    pil_image.save(out_buffer, format='JPEG', quality=quality, optimize=True)
    jpeg_bytes = out_buffer.getvalue()

    return jpeg_bytes, pil_image.width, pil_image.height


def qimage_to_pil_thumbnail(image: QImage, size: tuple[int, int] = (160, 120)) -> bytes:
    """
    生成缩略图（用于卡片显示）。
    返回 JPEG 字节。
    """
    from PIL import Image

    png_bytes = qimage_to_png_bytes(image)
    pil_image = Image.open(BytesIO(png_bytes))

    # 居中裁剪为 4:3 再缩放到目标尺寸
    target_ratio = size[0] / size[1]
    img_ratio = pil_image.width / pil_image.height

    if img_ratio > target_ratio:
        # 图片更宽，裁左右
        new_width = int(pil_image.height * target_ratio)
        left = (pil_image.width - new_width) // 2
        pil_image = pil_image.crop((left, 0, left + new_width, pil_image.height))
    elif img_ratio < target_ratio:
        # 图片更高，裁上下
        new_height = int(pil_image.width / target_ratio)
        top = (pil_image.height - new_height) // 2
        pil_image = pil_image.crop((0, top, pil_image.width, top + new_height))

    pil_image = pil_image.resize(size, Image.Resampling.LANCZOS)

    if pil_image.mode in ('RGBA', 'P', 'LA'):
        background = Image.new('RGB', pil_image.size, (255, 255, 255))
        if pil_image.mode == 'P':
            pil_image = pil_image.convert('RGBA')
        background.paste(pil_image, mask=pil_image.split()[-1] if pil_image.mode == 'RGBA' else None)
        pil_image = background
    elif pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')

    out_buffer = BytesIO()
    pil_image.save(out_buffer, format='JPEG', quality=75, optimize=True)
    return out_buffer.getvalue()
