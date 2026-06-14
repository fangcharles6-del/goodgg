"""主窗口 — 番茄钟计时器界面。"""

import logging

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QWindowStateChangeEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QCheckBox, QApplication,
)

from engine.timer_engine import TimerEngine, TimerState, SessionType, SESSION_LABELS
from utils.config import TimerConfig, save_config
from .theme import COLORS, APP_STYLESHEET
from .system_tray import SystemTrayManager

logger = logging.getLogger(__name__)

# ── 状态 → 状态文本 / 托盘文本 ──────────────────────

_IDLE_STATUS = ("准备就绪", "就绪")
_PAUSED_STATUS = ("⏸ 已暂停", "已暂停")
_BREAK_READY_STATUS = ("🟢 休息时间", "休息时间")

# ── 状态 → (按钮文字, 开始启用, 暂停启用, 重置启用) ──

_BTN_CFG = {
    TimerState.IDLE:    ("▶ 开始",     True,  False, False),
    TimerState.RUNNING: ("▶ 开始",     False, True,  True),
    TimerState.PAUSED:  ("▶ 继续",     True,  False, True),
    TimerState.BREAK:   ("▶ 开始休息", True,  False, True),
}

# ── 阶段 → 通知内容 ──────────────────────────────────

_FINISH_NOTIFICATIONS = {
    SessionType.FOCUS: ("🍅 专注完成！", "恭喜！一个番茄钟已完成，休息一下吧～"),
    SessionType.BREAK: ("☕ 休息结束", "休息时间结束，可以开始新的番茄钟了！"),
}


class MainWindow(QWidget):
    """番茄钟主窗口。"""

    def __init__(
        self,
        engine: TimerEngine,
        config: TimerConfig,
        tray: SystemTrayManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._engine = engine
        self._config = config
        self._tray = tray

        # ── 配置保存防抖 ──
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(300)
        self._save_timer.timeout.connect(self._do_save_config)

        self._setup_window()
        self._build_ui()
        self._connect_signals()

        # 初始 UI 状态
        self._update_display(self._engine.total_seconds)
        self._update_button_states(TimerState.IDLE)

    # ── 窗口设置 ─────────────────────────────────────

    def _setup_window(self) -> None:
        """设置窗口属性。"""
        self.setWindowTitle("🍅 番茄钟")
        self.setFixedSize(360, 400)

        # 置顶
        if self._config.always_on_top:
            self.setWindowFlags(
                Qt.WindowType.Window |
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.WindowCloseButtonHint |
                Qt.WindowType.WindowMinimizeButtonHint
            )
        else:
            self.setWindowFlags(
                Qt.WindowType.Window |
                Qt.WindowType.WindowCloseButtonHint |
                Qt.WindowType.WindowMinimizeButtonHint
            )

        # 窗口居中
        screen = QApplication.primaryScreen()
        if screen:
            center = screen.availableGeometry().center()
            frame = self.frameGeometry()
            frame.moveCenter(center)
            self.move(frame.topLeft())

    def _build_ui(self) -> None:
        """构建界面布局。"""
        self.setStyleSheet(APP_STYLESHEET)
        self.setObjectName("mainWindow")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(12)

        # ── 番茄图标与标题 ──
        title_label = QLabel("🍅 番茄钟")
        title_label.setObjectName("labelSession")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # ── 阶段指示 ──
        self._session_label = QLabel("准备就绪")
        self._session_label.setObjectName("labelSession")
        self._session_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self._session_label)

        # ── 倒计时显示 ──
        self._countdown_label = QLabel("25:00")
        self._countdown_label.setObjectName("labelCountdown")
        self._countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self._countdown_label)

        # ── 进度条 ──
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(100)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(8)
        main_layout.addWidget(self._progress_bar)

        # ── 按钮栏 ──
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self._btn_start = QPushButton("▶ 开始")
        self._btn_start.setObjectName("btnStart")
        self._btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_layout.addWidget(self._btn_start)

        self._btn_pause = QPushButton("⏸ 暂停")
        self._btn_pause.setObjectName("btnPause")
        self._btn_pause.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_pause.setEnabled(False)
        btn_layout.addWidget(self._btn_pause)

        self._btn_reset = QPushButton("↺ 重置")
        self._btn_reset.setObjectName("btnReset")
        self._btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_layout.addWidget(self._btn_reset)

        main_layout.addLayout(btn_layout)

        # ── 完成计数 ──
        self._pomodoro_label = QLabel("已完成: 0 个番茄")
        self._pomodoro_label.setObjectName("labelPomodoro")
        self._pomodoro_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self._pomodoro_label)

        # ── 置顶开关 ──
        self._always_on_top_cb = QCheckBox("窗口始终置顶")
        self._always_on_top_cb.setChecked(self._config.always_on_top)
        self._always_on_top_cb.setCursor(Qt.CursorShape.PointingHandCursor)
        main_layout.addWidget(self._always_on_top_cb, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addStretch()

    def _connect_signals(self) -> None:
        """连接信号与槽。"""
        # 引擎信号
        self._engine.tick.connect(self._on_tick)
        self._engine.state_changed.connect(self._on_state_changed)
        self._engine.session_finished.connect(self._on_session_finished)

        # 按钮
        self._btn_start.clicked.connect(self._on_start_clicked)
        self._btn_pause.clicked.connect(self._on_pause_clicked)
        self._btn_reset.clicked.connect(self._on_reset_clicked)

        # 置顶开关
        self._always_on_top_cb.toggled.connect(self._on_always_on_top_toggled)

        # 系统托盘
        self._tray.show_requested.connect(self._show_and_raise)
        self._tray.quit_requested.connect(self._quit_app)

    # ── 槽函数 ───────────────────────────────────────

    def _on_tick(self, remaining: int) -> None:
        """每秒更新显示。"""
        self._update_display(remaining)

    def _on_state_changed(self, state: TimerState) -> None:
        """状态变化时更新按钮和标签。"""
        self._update_button_states(state)

        if state == TimerState.RUNNING:
            label, tray_text = SESSION_LABELS[self._engine.session_type]
            self._session_label.setText(label)
            self._tray.set_timer_status(tray_text)
        elif state == TimerState.IDLE:
            self._session_label.setText(_IDLE_STATUS[0])
            self._tray.set_timer_status(_IDLE_STATUS[1])
        elif state == TimerState.PAUSED:
            self._session_label.setText(_PAUSED_STATUS[0])
            self._tray.set_timer_status(_PAUSED_STATUS[1])
        elif state == TimerState.BREAK:
            self._session_label.setText(_BREAK_READY_STATUS[0])
            self._tray.set_timer_status(_BREAK_READY_STATUS[1])

    def _on_session_finished(self, session_type: SessionType) -> None:
        """阶段完成时弹出通知。"""
        title, message = _FINISH_NOTIFICATIONS[session_type]
        self._tray.notify(title, message)

        # 更新完成计数
        self._pomodoro_label.setText(
            f"已完成: {self._engine.completed_pomodoros} 个番茄"
        )

    def _on_start_clicked(self) -> None:
        """点击开始按钮。"""
        self._engine.start()

    def _on_pause_clicked(self) -> None:
        """点击暂停按钮。"""
        self._engine.pause()

    def _on_reset_clicked(self) -> None:
        """点击重置按钮。"""
        self._engine.reset()
        self._update_display(self._engine.total_seconds)

    def _on_always_on_top_toggled(self, checked: bool) -> None:
        """切换始终置顶。"""
        self._config.always_on_top = checked
        self._save_timer.start()  # 防抖 300ms 后保存

        # 重建窗口标志
        flags = self.windowFlags()
        if checked:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()  # 重新设置标志后需要 show

    def _do_save_config(self) -> None:
        """防抖后的配置保存。"""
        save_config(self._config)

    # ── UI 更新 ───────────────────────────────────────

    def _update_display(self, remaining: int) -> None:
        """更新倒计时和进度条。"""
        total = self._engine.total_seconds
        minutes = remaining // 60
        seconds = remaining % 60
        self._countdown_label.setText(f"{minutes:02d}:{seconds:02d}")

        if total > 0:
            progress = int(remaining / total * 100)
        else:
            progress = 100
        self._progress_bar.setValue(progress)

    def _update_button_states(self, state: TimerState) -> None:
        """根据状态启用/禁用按钮。"""
        txt, start_en, pause_en, reset_en = _BTN_CFG[state]
        self._btn_start.setText(txt)
        self._btn_start.setEnabled(start_en)
        self._btn_pause.setEnabled(pause_en)
        self._btn_reset.setEnabled(reset_en)

    # ── 窗口可见性 ───────────────────────────────────

    def _show_and_raise(self) -> None:
        """显示并置前窗口。"""
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def changeEvent(self, event) -> None:
        """拦截最小化事件 — 最小化时隐藏到托盘。"""
        if isinstance(event, QWindowStateChangeEvent) and self.isMinimized():
            self.hide()
            return
        super().changeEvent(event)

    def closeEvent(self, event) -> None:
        """关闭窗口时隐藏到托盘而非退出。"""
        event.ignore()
        self.hide()

    # ── 退出 ─────────────────────────────────────────

    def _quit_app(self) -> None:
        """完全退出应用。"""
        self._engine.reset()
        self._tray.hide()
        QApplication.quit()

    def show(self) -> None:
        """重写 show，托盘由 app 层管理。"""
        super().show()
