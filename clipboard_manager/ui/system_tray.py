"""系统托盘图标管理。"""

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QAction
from PySide6.QtWidgets import QSystemTrayIcon, QMenu


def _create_tray_icon() -> QIcon:
    """生成简单的剪贴板托盘图标（程序化绘制）。"""
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor(0, 0, 0, 0))  # 透明背景

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 绘制剪贴板形状
    painter.setBrush(QColor("#42a5f5"))
    painter.setPen(QColor("#1e88e5"))
    painter.drawRoundedRect(4, 6, 24, 22, 4, 4)

    # 绘制顶部夹子
    painter.setBrush(QColor("#90caf9"))
    painter.drawRoundedRect(12, 1, 8, 10, 2, 2)

    # 绘制文字标识
    painter.setPen(QColor("#ffffff"))
    painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
    painter.drawText(pixmap.rect(), 0x0084 | 0x0010, "CP")

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
        self._tray.setToolTip("历史粘贴板 - 监听中...")

        # 右键菜单
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

    def set_monitoring_status(self, active: bool) -> None:
        """更新托盘提示文字。"""
        if active:
            self._tray.setToolTip("历史粘贴板 - 监听中...")
        else:
            self._tray.setToolTip("历史粘贴板 - 已暂停")
