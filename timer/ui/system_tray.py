"""系统托盘图标管理。"""

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QAction
from PySide6.QtWidgets import QSystemTrayIcon, QMenu


def _create_tray_icon() -> QIcon:
    """程序化绘制番茄托盘图标。"""
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor(0, 0, 0, 0))  # 透明背景

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 绘制番茄圆形主体
    painter.setBrush(QColor("#e74c3c"))
    painter.setPen(QColor("#c0392b"))
    painter.drawEllipse(4, 8, 24, 22)

    # 绘制顶部叶子
    painter.setBrush(QColor("#27ae60"))
    painter.setPen(QColor("#1e8449"))
    painter.drawEllipse(13, 1, 6, 9)

    painter.end()
    return QIcon(pixmap)


class SystemTrayManager(QObject):
    """管理系统托盘图标和菜单。"""

    show_requested = Signal()
    quit_requested = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._tray = QSystemTrayIcon()
        self._tray.setIcon(_create_tray_icon())
        self._tray.setToolTip("🍅 番茄钟 - 就绪")

        # ── 右键菜单 ──
        menu = QMenu()

        show_action = QAction("显示窗口", menu)
        show_action.triggered.connect(self.show_requested.emit)
        menu.addAction(show_action)

        menu.addSeparator()

        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)

        # 左键点击 = 显示窗口
        self._tray.activated.connect(self._on_activated)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_requested.emit()

    def show(self) -> None:
        self._tray.show()

    def hide(self) -> None:
        self._tray.hide()

    def set_timer_status(self, text: str) -> None:
        """更新托盘提示文字。"""
        self._tray.setToolTip(f"🍅 番茄钟 - {text}")

    def notify(self, title: str, message: str) -> None:
        """弹出桌面通知。"""
        self._tray.showMessage(
            title,
            message,
            QSystemTrayIcon.MessageIcon.Information,
            5000,  # 5 秒后自动消失
        )
