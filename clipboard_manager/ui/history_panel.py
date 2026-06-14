"""历史记录面板 — 可滚动卡片列表。"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QSizePolicy,
)

from database.models import ClipboardItem
from .card_widget import CardWidget
from .theme import COLORS


class HistoryPanel(QWidget):
    """滚动式卡片列表，按时间降序显示剪贴板历史。"""

    card_clicked = Signal(object)
    pin_toggled = Signal(object)
    delete_requested = Signal(object)

    def __init__(self, title: str = "历史记录", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title = title
        self._cards: list[CardWidget] = []
        self._empty_label: QLabel = None
        self._card_container: QWidget = None
        self._card_layout: QVBoxLayout = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题
        title_label = QLabel(self._title)
        title_label.setStyleSheet(
            f"color: {COLORS['secondary_text']}; font-size: 12px; "
            f"font-weight: bold; padding: 8px 0; border: none;"
        )
        layout.addWidget(title_label)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        # 卡片容器
        self._card_container = QWidget()
        self._card_layout = QVBoxLayout(self._card_container)
        self._card_layout.setContentsMargins(0, 0, 0, 0)
        self._card_layout.setSpacing(6)
        self._card_layout.addStretch()

        scroll.setWidget(self._card_container)
        layout.addWidget(scroll, 1)

        # 空状态提示
        self._empty_label = QLabel("还没有复制记录\n试试 Ctrl+C 吧！")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(
            f"color: {COLORS['timestamp_text']}; font-size: 16px; "
            "border: none; padding: 40px;"
        )
        self._empty_label.hide()
        layout.addWidget(self._empty_label)

    def set_items(self, items: list[ClipboardItem]) -> None:
        """刷新卡片列表。"""
        # 清除旧卡片
        for card in self._cards:
            card.deleteLater()
        self._cards.clear()

        # 移除 stretch（如果存在）
        while self._card_layout.count():
            item = self._card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not items:
            self._card_container.hide()
            self._empty_label.show()
            return

        self._empty_label.hide()
        self._card_container.show()

        # 创建新卡片
        for item in items:
            card = CardWidget(item)
            card.clicked.connect(self.card_clicked.emit)
            card.pin_toggled.connect(self.pin_toggled.emit)
            card.delete_requested.connect(self.delete_requested.emit)
            self._card_layout.addWidget(card)
            self._cards.append(card)

        self._card_layout.addStretch()
