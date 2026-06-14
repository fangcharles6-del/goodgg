"""主窗口 — 整合所有 UI 组件和业务逻辑。"""

import logging
from datetime import datetime, timezone

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel,
    QApplication, QStatusBar,
)

from database.models import AppConfig, ClipboardItem
from database.repository import ClipboardRepository
from clipboard.monitor import ClipboardMonitor
from clipboard.deduplicator import Deduplicator
from hotkey.hotkey_manager import HotkeyManager
from utils.config import save_config, get_db_path
from .theme import COLORS, APP_STYLESHEET
from .search_bar import SearchBar
from .history_panel import HistoryPanel
from .settings_dialog import SettingsDialog
from .system_tray import SystemTrayManager

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """历史粘贴板主窗口。"""

    def __init__(
        self,
        repo: ClipboardRepository,
        config: AppConfig,
    ) -> None:
        super().__init__()
        self._repo = repo
        self._config = config
        self._monitor: ClipboardMonitor = None
        self._deduplicator = Deduplicator(repo)
        self._hotkey_mgr = HotkeyManager(self)
        self._tray = SystemTrayManager()
        self._ignore_next_clipboard = False  # 防止回录自己复制的内容

        self._setup_window()
        self._build_ui()
        self._connect_signals()
        self._start_monitoring()
        self._setup_hotkey()

        # 启动时清理过期记录
        self._repo.delete_expired(self._config.retention_days)

        # 加载初始数据
        self._refresh_all()

        # 显示托盘图标
        self._tray.show()

    # ── 窗口设置 ─────────────────────────────────────

    def _setup_window(self) -> None:
        self.setWindowTitle("历史粘贴板")
        self.setMinimumSize(420, 400)
        self.resize(560, 600)

        # 窗口居中
        screen = QApplication.primaryScreen()
        if screen:
            center = screen.availableGeometry().center()
            frame = self.frameGeometry()
            frame.moveCenter(center)
            self.move(frame.topLeft())

        # 不显示在任务栏（通过 raise/activateWindow 控制焦点）
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMinimizeButtonHint
        )

    def _build_ui(self) -> None:
        """构建主窗口 UI。"""
        self.setStyleSheet(APP_STYLESHEET)

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 12, 16, 8)
        main_layout.setSpacing(4)

        # ── 搜索栏 ──
        self._search_bar = SearchBar()
        self._search_bar.settings_clicked.connect(self._open_settings)
        main_layout.addWidget(self._search_bar)

        # ── 置顶区域 ──
        self._pinned_panel = HistoryPanel("📌 置顶")
        self._pinned_panel.card_clicked.connect(self._on_card_clicked)
        self._pinned_panel.pin_toggled.connect(self._on_pin_toggle)
        self._pinned_panel.delete_requested.connect(self._on_delete)
        self._pinned_panel.hide()
        main_layout.addWidget(self._pinned_panel)

        # ── 历史记录区域 ──
        self._history_panel = HistoryPanel("历史记录")
        self._history_panel.card_clicked.connect(self._on_card_clicked)
        self._history_panel.pin_toggled.connect(self._on_pin_toggle)
        self._history_panel.delete_requested.connect(self._on_delete)
        main_layout.addWidget(self._history_panel, 1)

        # ── 状态栏 ──
        self._status_bar = QStatusBar()
        self._status_bar.setStyleSheet(
            f"QStatusBar {{ background: transparent; color: {COLORS['timestamp_text']}; "
            "border: none; font-size: 11px; }}"
        )
        self._status_count = QLabel("共 0 条记录")
        self._status_count.setFont(QFont("Microsoft YaHei", 9))
        self._status_count.setStyleSheet(f"color: {COLORS['timestamp_text']}; border: none;")
        self._status_bar.addWidget(self._status_count)
        self._status_bar.addPermanentWidget(
            QLabel("🟢 监听中...")
        )
        self.setStatusBar(self._status_bar)

    def _connect_signals(self) -> None:
        """连接信号槽。"""
        # 搜索
        self._search_bar.search_changed.connect(self._on_search)

        # 数据库变更 → 刷新
        self._repo.items_changed.connect(self._refresh_all)

        # 系统托盘
        self._tray.show_requested.connect(self._show_and_raise)
        self._tray.quit_requested.connect(self._quit_app)

        # 热键
        self._hotkey_mgr.activated.connect(self.toggle_visibility)

    # ── 剪贴板监听 ──────────────────────────────────

    def _start_monitoring(self) -> None:
        """启动剪贴板监听线程。"""
        self._monitor = ClipboardMonitor(self)
        self._monitor.new_content.connect(self._on_clipboard_change)
        self._monitor.start()

    def _on_clipboard_change(self) -> None:
        """剪贴板变化时由主线程调用（安全访问 QClipboard）。"""
        # 忽略应用自身复制到剪贴板触发的变化
        if self._ignore_next_clipboard:
            self._ignore_next_clipboard = False
            return

        cb = QApplication.clipboard()
        mime = cb.mimeData()

        if mime.hasText():
            text = mime.text()
            if text and text.strip():
                self._deduplicator.process_text(text)

        elif mime.hasImage():
            image = cb.image()
            if image and not image.isNull():
                self._deduplicator.process_image(
                    image, compress=self._config.compress_images
                )

    # ── 数据刷新 ─────────────────────────────────────

    def _refresh_all(self) -> None:
        """刷新所有面板数据。"""
        search_text = self._search_bar.text()

        # 置顶数据
        pinned = self._repo.get_pinned()
        if pinned:
            self._pinned_panel.set_items(pinned)
            self._pinned_panel.show()
        else:
            self._pinned_panel.hide()
            self._pinned_panel.set_items([])

        # 历史数据（排除置顶）
        items = self._repo.get_all(search=search_text, limit=500)
        self._history_panel.set_items(items)

        # 更新计数
        total = self._repo.get_count()
        self._status_count.setText(f"共 {total} 条记录")

    @property
    def _current_search(self) -> str:
        return self._search_bar.text()

    # ── 卡片交互 ─────────────────────────────────────

    def _on_card_clicked(self, item: ClipboardItem) -> None:
        """点击卡片 → 复制内容到剪贴板。"""
        self._ignore_next_clipboard = True  # 忽略即将触发的剪贴板变化

        cb = QApplication.clipboard()

        if item.is_text and item.content_text:
            cb.setText(item.content_text)
        elif item.is_image and item.image_blob:
            from PySide6.QtGui import QImage
            image = QImage()
            image.loadFromData(item.image_blob)
            cb.setImage(image)

        self._repo.mark_used(item.id)
        logger.debug("已复制到剪贴板: id=%d", item.id)

    def _on_pin_toggle(self, item: ClipboardItem) -> None:
        """切换置顶状态。"""
        new_pinned = not item.is_pinned
        self._repo.set_pinned(item.id, new_pinned)

    def _on_delete(self, item: ClipboardItem) -> None:
        """删除记录。"""
        self._repo.delete(item.id)

    # ── 搜索 ─────────────────────────────────────────

    def _on_search(self, text: str) -> None:
        """搜索文本变化时刷新历史列表。"""
        items = self._repo.get_all(search=text, limit=500)
        self._history_panel.set_items(items)

        # 置顶不参与搜索过滤
        pinned = self._repo.get_pinned()
        self._pinned_panel.set_items(pinned)

    # ── 设置 ─────────────────────────────────────────

    def _open_settings(self) -> None:
        """打开设置对话框。"""
        dialog = SettingsDialog(self._config, self)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            self._config = dialog.get_config()
            save_config(self._config)
            # 立即清理过期记录
            self._repo.delete_expired(self._config.retention_days)

    # ── 热键 / 可见性 ───────────────────────────────

    def _setup_hotkey(self) -> None:
        """注册全局热键。"""
        hwnd = int(self.winId())
        if self._hotkey_mgr.register(hwnd):
            print("[OK] Global hotkey Ctrl+Shift+V registered")
        else:
            print("[WARN] Global hotkey registration failed, use system tray to open")

    def toggle_visibility(self) -> None:
        """切换窗口显示/隐藏。"""
        if self.isVisible() and self.isActiveWindow():
            self.hide()
        else:
            self._show_and_raise()

    def _show_and_raise(self) -> None:
        """显示并置前窗口。"""
        self.show()
        self.raise_()
        self.activateWindow()
        self._search_bar.setFocus()
        self._refresh_all()

    def closeEvent(self, event) -> None:
        """关闭窗口时隐藏到托盘而非退出。"""
        event.ignore()
        self.hide()

    # ── 退出 ─────────────────────────────────────────

    def _quit_app(self) -> None:
        """完全退出应用。"""
        self._monitor.stop()
        self._hotkey_mgr.unregister()
        self._tray.hide()
        QApplication.quit()

    def show(self) -> None:
        """重写 show 确保托盘显示。"""
        super().show()
        self._tray.show()
