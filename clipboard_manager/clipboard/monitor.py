"""剪贴板监听线程 — 轮询检测剪贴板变化，通过信号通知主线程读取。"""

import ctypes
import logging
from ctypes import wintypes

from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)

# Windows API
user32 = ctypes.windll.user32


def get_clipboard_sequence_number() -> int:
    """获取 Windows 剪贴板序列号，每次内容变化时递增。"""
    return user32.GetClipboardSequenceNumber()


class ClipboardMonitor(QThread):
    """
    剪贴板监听线程。
    每 500ms 轮询 Windows 剪贴板序列号。
    检测到变化时通过信号通知主线程（主线程负责读取剪贴板）。
    """

    new_content = Signal()  # 通知主线程剪贴板有变化

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._running = False

    def run(self) -> None:
        """主循环：轮询序列号。"""
        self._running = True
        last_seq = get_clipboard_sequence_number()

        while self._running:
            self.msleep(500)  # 500ms 轮询间隔

            try:
                seq = get_clipboard_sequence_number()
            except Exception:
                continue

            if seq != last_seq:
                last_seq = seq
                self.new_content.emit()

    def stop(self) -> None:
        """停止监听线程。"""
        self._running = False
        self.wait(1000)  # 等待最多 1 秒
