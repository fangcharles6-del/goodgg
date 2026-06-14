"""内容哈希计算 — 用于去重检测。"""

import hashlib


def hash_text(text: str) -> str:
    """计算文字内容的 SHA-256 哈希值。"""
    return hashlib.sha256(text.encode('utf-8', errors='replace')).hexdigest()


def hash_bytes(data: bytes) -> str:
    """计算字节内容的 SHA-256 哈希值。"""
    return hashlib.sha256(data).hexdigest()
