"""番茄钟核心计时引擎 — 状态机 + QTimer 驱动。"""

import logging
from enum import Enum, auto

from PySide6.QtCore import QObject, QTimer, Signal

from utils.config import TimerConfig

logger = logging.getLogger(__name__)


class TimerState(Enum):
    """计时器状态枚举。"""
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    BREAK = auto()


class SessionType(Enum):
    """阶段类型枚举。"""
    FOCUS = "focus"
    BREAK = "break"


# ── 标签映射（供 UI 层使用）─────────────────────────

SESSION_LABELS = {
    SessionType.FOCUS: ("🔴 专注中", "专注中..."),
    SessionType.BREAK: ("🟢 休息中", "休息中..."),
}


class TimerEngine(QObject):
    """番茄钟计时引擎，管理状态转换和秒级倒计时。"""

    # ── 信号 ──────────────────────────────────────────

    tick = Signal(int)                 # 每秒发射剩余秒数
    state_changed = Signal(TimerState) # 状态变化
    session_finished = Signal(SessionType)  # 阶段完成

    def __init__(self, config: TimerConfig, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._config = config

        # ── 内部状态 ──
        self._state = TimerState.IDLE
        self._remaining = 0
        self._session_type: SessionType = SessionType.FOCUS
        self._completed_pomodoros = 0
        self._total_seconds = self._config.focus_duration * 60

        # ── 定时器 ──
        self._timer = QTimer(self)
        self._timer.setInterval(1000)       # 1 秒
        self._timer.timeout.connect(self._on_timer_tick)

    # ── 属性 ─────────────────────────────────────────

    @property
    def state(self) -> TimerState:
        return self._state

    @property
    def remaining_seconds(self) -> int:
        return self._remaining

    @property
    def session_type(self) -> SessionType:
        return self._session_type

    @property
    def completed_pomodoros(self) -> int:
        return self._completed_pomodoros

    @property
    def total_seconds(self) -> int:
        """当前阶段的总秒数（缓存值，阶段内不变）。"""
        return self._total_seconds

    # ── 公共方法 ─────────────────────────────────────

    def start(self) -> None:
        """开始或恢复计时。"""
        if self._state == TimerState.IDLE:
            self._session_type = SessionType.FOCUS
            self._remaining = self._config.focus_duration * 60
            self._total_seconds = self._remaining
            logger.info("番茄钟开始: 专注 %d 分钟", self._config.focus_duration)

        elif self._state == TimerState.PAUSED:
            logger.info("番茄钟恢复计时")

        elif self._state == TimerState.BREAK:
            self._session_type = SessionType.BREAK
            self._remaining = self._config.short_break_duration * 60
            self._total_seconds = self._remaining
            logger.info("休息开始: %d 分钟", self._config.short_break_duration)

        else:
            return  # RUNNING 状态下无效

        self._set_state(TimerState.RUNNING)
        self._timer.start()

    def pause(self) -> None:
        """暂停计时。"""
        if self._state == TimerState.RUNNING:
            self._timer.stop()
            self._set_state(TimerState.PAUSED)
            logger.info("番茄钟已暂停")

    def reset(self) -> None:
        """重置计时器回到空闲状态。"""
        self._timer.stop()
        self._remaining = 0
        self._session_type = SessionType.FOCUS
        self._total_seconds = self._config.focus_duration * 60
        self._set_state(TimerState.IDLE)
        logger.info("番茄钟已重置")

    # ── 内部逻辑 ─────────────────────────────────────

    def _set_state(self, new_state: TimerState) -> None:
        """更新状态并发射信号。"""
        if self._state != new_state:
            self._state = new_state
            self.state_changed.emit(new_state)
            logger.debug("状态变更: %s", new_state.name)

    def _on_timer_tick(self) -> None:
        """每秒回调：递减并检查是否完成。"""
        self._remaining -= 1
        self.tick.emit(self._remaining)

        if self._remaining <= 0:
            self._complete_session()

    def _complete_session(self) -> None:
        """当前阶段完成。"""
        self._timer.stop()

        if self._session_type == SessionType.FOCUS:
            self._completed_pomodoros += 1
            self.session_finished.emit(SessionType.FOCUS)
            logger.info("专注阶段完成，总计完成 %d 个番茄", self._completed_pomodoros)
            self._set_state(TimerState.BREAK)

        else:
            self.session_finished.emit(SessionType.BREAK)
            logger.info("休息阶段完成")
            self._session_type = SessionType.FOCUS
            self._remaining = 0
            self._total_seconds = self._config.focus_duration * 60
            self._set_state(TimerState.IDLE)
