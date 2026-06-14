"""全局热键管理 — Windows RegisterHotKey API + Qt 原生事件过滤。"""

import ctypes
import logging
from ctypes import wintypes

from PySide6.QtCore import QObject, Signal, QAbstractNativeEventFilter
from PySide6.QtWidgets import QApplication

logger = logging.getLogger(__name__)

# Windows 常量
WM_HOTKEY = 0x0312
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
VK_V = 0x56
HOTKEY_ID = 1

user32 = ctypes.windll.user32


class _NativeEventFilter(QAbstractNativeEventFilter):
    """过滤 Windows WM_HOTKEY 消息。"""

    def __init__(self, manager: 'HotkeyManager') -> None:
        super().__init__()
        self._manager = manager

    def nativeEventFilter(self, event_type: bytes, message: int) -> tuple[bool, int]:
        # event_type == b"windows_generic_MSG" on Windows
        try:
            msg = ctypes.cast(message, ctypes.POINTER(wintypes.MSG)).contents
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                self._manager.activated.emit()
                return True, 0
        except Exception:
            pass
        return False, 0


class HotkeyManager(QObject):
    """管理全局热键的注册与注销。"""

    activated = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._filter = _NativeEventFilter(self)
        self._registered = False
        self._hwnd = 0

    def register(self, hwnd: int) -> bool:
        """注册全局热键 Ctrl+Shift+V。返回是否注册成功。"""
        self._hwnd = int(hwnd)
        result = user32.RegisterHotKey(
            wintypes.HWND(self._hwnd),
            HOTKEY_ID,
            MOD_CONTROL | MOD_SHIFT,
            VK_V,
        )
        if result:
            self._registered = True
            QApplication.instance().installNativeEventFilter(self._filter)
            logger.info("全局热键 Ctrl+Shift+V 注册成功")
            return True
        else:
            logger.warning("全局热键注册失败（可能被其他程序占用）")
            return False

    def unregister(self) -> None:
        """注销热键。"""
        if self._registered and self._hwnd:
            user32.UnregisterHotKey(wintypes.HWND(self._hwnd), HOTKEY_ID)
            self._registered = False
            QApplication.instance().removeNativeEventFilter(self._filter)
            logger.info("全局热键已注销")

    def is_registered(self) -> bool:
        return self._registered
