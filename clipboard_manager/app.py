"""应用入口 — QApplication 子类，负责初始化所有模块。"""

import sys
import logging

from PySide6.QtWidgets import QApplication

from database.repository import ClipboardRepository
from database.schema import migrate
from utils.config import get_db_path, load_config
from ui.main_window import MainWindow

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """配置日志输出。"""
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s - %(name)s: %(message)s',
        datefmt='%H:%M:%S',
    )


def run() -> None:
    """启动应用。"""
    setup_logging()
    logger.info("历史粘贴板启动中...")

    # 初始化 Qt 应用
    app = QApplication(sys.argv)
    app.setApplicationName("ClipboardManager")
    app.setOrganizationName("ClipboardManager")
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出，托盘继续运行

    # 初始化数据库
    db_path = get_db_path()
    migrate(db_path)
    repo = ClipboardRepository(db_path)

    # 加载配置
    config = load_config()

    # 创建主窗口（系统托盘在 MainWindow 内部管理）
    window = MainWindow(repo, config)

    # 启动时显示窗口
    window.show()

    # 进入 Qt 事件循环
    sys.exit(app.exec())
