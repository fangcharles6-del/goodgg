"""设置对话框 — 保留天数、压缩开关。"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, QCheckBox,
    QDialogButtonBox, QLabel,
)

from database.models import AppConfig
from .theme import COLORS


class SettingsDialog(QDialog):
    """设置对话框。"""

    def __init__(self, config: AppConfig, parent=None) -> None:
        super().__init__(parent)
        self._config = config
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("设置")
        self.setFixedSize(320, 220)
        self.setStyleSheet(f"background-color: {COLORS['window_bg']};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # 标题
        title = QLabel("⚙  偏好设置")
        title.setStyleSheet(
            f"color: {COLORS['primary_text']}; font-size: 16px; "
            "font-weight: bold; border: none;"
        )
        layout.addWidget(title)

        # 表单
        form = QFormLayout()
        form.setSpacing(12)

        # 保留天数
        self._retention_combo = QComboBox()
        self._retention_combo.addItems(["1 天", "3 天", "5 天"])
        days_map = {1: 0, 3: 1, 5: 2}
        self._retention_combo.setCurrentIndex(days_map.get(self._config.retention_days, 1))
        form.addRow("保留天数:", self._retention_combo)

        # 图片压缩
        self._compress_check = QCheckBox("启用图片压缩（推荐）")
        self._compress_check.setChecked(self._config.compress_images)
        form.addRow("图片:", self._compress_check)

        layout.addLayout(form)
        layout.addStretch()

        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("保存")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        """保存设置并关闭。"""
        days_text = self._retention_combo.currentText()
        self._config.retention_days = int(days_text[0])
        self._config.compress_images = self._compress_check.isChecked()
        self.accept()

    def get_config(self) -> AppConfig:
        return self._config
