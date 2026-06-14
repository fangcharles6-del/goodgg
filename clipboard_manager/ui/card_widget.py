"""剪贴板记录卡片组件。"""

from datetime import datetime, timezone

from PySide6.QtCore import Qt, Signal, QByteArray
from PySide6.QtGui import QPixmap, QIcon, QFont
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QSizePolicy, QWidget,
)

from database.models import ClipboardItem
from .theme import COLORS


def _format_time(iso_str: str) -> str:
    """将 ISO 时间戳格式化为可读的相对时间。"""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str)
        now = datetime.now(timezone.utc)
        diff = now - dt.replace(tzinfo=timezone.utc)

        if diff.days > 0:
            if diff.days == 1:
                return "昨天"
            elif diff.days < 7:
                return f"{diff.days}天前"
            else:
                return dt.strftime("%m/%d %H:%M")
        elif diff.seconds < 60:
            return "刚刚"
        elif diff.seconds < 3600:
            return f"{diff.seconds // 60}分钟前"
        else:
            return f"{diff.seconds // 3600}小时前"
    except (ValueError, TypeError):
        return iso_str[:16]


class CardWidget(QFrame):
    """单条剪贴板记录的卡片组件。"""

    clicked = Signal(object)       # 点击卡片 → 复制到剪贴板
    pin_toggled = Signal(object)   # 置顶/取消置顶
    delete_requested = Signal(object)  # 删除

    def __init__(self, item: ClipboardItem, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._item = item
        self._pin_btn: QPushButton = None
        self._delete_btn: QPushButton = None
        self._is_hovered = False
        self._build_ui()
        self._update_style(False)

    def _build_ui(self) -> None:
        """构建卡片内部布局。"""
        self.setFixedHeight(72)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(12, 8, 8, 8)
        outer.setSpacing(10)

        # ── 左侧内容预览 ──
        if self._item.is_image and self._item.image_blob:
            # 图片缩略图
            preview = QLabel()
            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(self._item.image_blob))
            preview.setPixmap(pixmap.scaled(
                80, 54, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))
            preview.setFixedSize(80, 54)
            preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
            preview.setStyleSheet(
                f"border: 1px solid {COLORS['card_border']}; "
                "border-radius: 4px; background: #f5f5f5;"
            )
            outer.addWidget(preview)
        else:
            # 文字预览
            preview = QLabel(self._item.preview_text)
            preview.setWordWrap(True)
            preview.setMaximumHeight(54)
            preview.setFont(QFont("Microsoft YaHei", 10))
            preview.setStyleSheet(f"color: {COLORS['primary_text']}; border: none;")
            preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            outer.addWidget(preview, 1)

        # ── 右侧信息栏 ──
        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(2)

        # 时间戳
        time_label = QLabel(_format_time(self._item.created_at))
        time_label.setFont(QFont("Microsoft YaHei", 8))
        time_label.setStyleSheet(f"color: {COLORS['timestamp_text']}; border: none;")
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        right_col.addWidget(time_label)

        right_col.addStretch()

        # 操作按钮
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(4)

        # 置顶按钮
        self._pin_btn = QPushButton("📌")
        self._pin_btn.setFixedSize(26, 26)
        self._pin_btn.setToolTip("置顶" if not self._item.is_pinned else "取消置顶")
        self._pin_btn.clicked.connect(lambda e: self.pin_toggled.emit(self._item))
        if self._item.is_pinned:
            self._pin_btn.setStyleSheet(self._pin_active_style())
        else:
            self._pin_btn.setStyleSheet(self._pin_inactive_style())
        btn_row.addWidget(self._pin_btn)

        # 删除按钮
        self._delete_btn = QPushButton("🗑")
        self._delete_btn.setFixedSize(26, 26)
        self._delete_btn.setToolTip("删除")
        self._delete_btn.clicked.connect(lambda e: self.delete_requested.emit(self._item))
        self._delete_btn.setStyleSheet(self._delete_style())
        btn_row.addWidget(self._delete_btn)

        right_col.addLayout(btn_row)
        outer.addLayout(right_col)

        # 整个卡片可点击
        self.mousePressEvent = lambda e: self.clicked.emit(self._item)

    def _update_style(self, hovered: bool) -> None:
        """根据状态更新卡片样式。"""
        border_color = COLORS["accent"] if hovered else COLORS["card_border"]
        bg = COLORS["pinned_bg"] if self._item.is_pinned else COLORS["card_bg"]

        self.setStyleSheet(f"""
            CardWidget {{
                background-color: {bg};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
        """)

    def enterEvent(self, event) -> None:
        self._update_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._update_style(False)
        super().leaveEvent(event)

    # ── 按钮样式 ──

    @staticmethod
    def _pin_active_style() -> str:
        return f"""
            QPushButton {{
                background-color: #fff8e1;
                border: 1px solid #ffcc02;
                border-radius: 13px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #ffecb3;
            }}
        """

    @staticmethod
    def _pin_inactive_style() -> str:
        return f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 13px;
                font-size: 14px;
                opacity: 0.5;
            }}
            QPushButton:hover {{
                background-color: #fff8e1;
                border-color: #ffe082;
                opacity: 1.0;
            }}
        """

    @staticmethod
    def _delete_style() -> str:
        return f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 13px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #ffebee;
                border-color: {COLORS["danger"]};
            }}
        """
