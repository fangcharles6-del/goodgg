"""应用入口 — QApplication 初始化，关联所有模块。"""

import sys
import logging

from PySide6.QtWidgets import QApplication

from engine.timer_engine import TimerEngine
from utils.config import load_config
from ui.main_window import MainWindow
from ui.system_tray import SystemTrayManager

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """配置日志输出。"""
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s - %(name)s: %(message)s',
        datefmt='%H:%M:%S',
    )


def run() -> None:
    """启动番茄钟应用。"""
    setup_logging()
    logger.info("🍅 番茄钟启动中...")

    # 初始化 Qt 应用
    app = QApplication(sys.argv)
    app.setApplicationName("PomodoroTimer")
    app.setOrganizationName("PomodoroTimer")
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出，托盘继续运行

    # 加载配置
    config = load_config()

    # 创建计时引擎
    engine = TimerEngine(config)

    # 创建系统托盘
    tray = SystemTrayManager()

    # 创建主窗口，传入所有依赖
    window = MainWindow(engine, config, tray)

    # 显示窗口
    window.show()
    tray.show()  # 明确在 app 层激活托盘

    # 进入 Qt 事件循环
    sys.exit(app.exec())
