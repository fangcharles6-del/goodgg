"""搜索栏组件 — 含搜索输入框和设置按钮。"""

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton,
)

from .theme import COLORS


class SearchBar(QWidget):
    """顶部搜索栏：搜索框 + 设置按钮。"""

    search_changed = Signal(str)     # 搜索文本变化（300ms 防抖后发出）
    settings_clicked = Signal()      # 点击设置按钮

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(300)
        self._debounce_timer.timeout.connect(self._emit_search)
        self._pending_text = ""
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(8)

        # 搜索输入框
        self._input = QLineEdit()
        self._input.setPlaceholderText("🔍  搜索复制内容...")
        self._input.setClearButtonEnabled(True)
        self._input.textChanged.connect(self._on_text_changed)
        self._input.setFixedHeight(40)
        layout.addWidget(self._input, 1)

        # 设置按钮
        self._settings_btn = QPushButton("⚙")
        self._settings_btn.setFixedSize(38, 38)
        self._settings_btn.setToolTip("设置")
        self._settings_btn.clicked.connect(self.settings_clicked.emit)
        self._settings_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["card_bg"]};
                border: 1px solid {COLORS["card_border"]};
                border-radius: 19px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {COLORS["window_bg"]};
                border-color: {COLORS["accent"]};
            }}
        """)
        layout.addWidget(self._settings_btn)

    def _on_text_changed(self, text: str) -> None:
        """输入变化时重启防抖计时器。"""
        self._pending_text = text
        self._debounce_timer.start()

    def _emit_search(self) -> None:
        """防抖结束后发出搜索信号。"""
        self.search_changed.emit(self._pending_text)

    def clear(self) -> None:
        """清空搜索框。"""
        self._input.clear()

    def text(self) -> str:
        """返回当前搜索文本。"""
        return self._input.text()

    def setFocus(self) -> None:
        """聚焦搜索框。"""
        self._input.setFocus()
