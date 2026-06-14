"""番茄钟 — 入口文件。

双击运行此 .py 文件即可启动。
"""

import sys
import os
import ctypes
import logging

# 确保项目根目录在 Python 路径中
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

logger = logging.getLogger(__name__)

MUTEX_NAME = "Global\\PomodoroTimerMutex"
kernel32 = ctypes.windll.kernel32


def try_acquire_mutex() -> bool:
    """尝试创建命名互斥体，检测是否已有实例在运行。"""
    handle = kernel32.CreateMutexW(None, True, MUTEX_NAME)
    if handle == 0:
        logger.error("创建互斥体失败")
        return True

    last_error = kernel32.GetLastError()
    if last_error == 183:  # ERROR_ALREADY_EXISTS
        kernel32.CloseHandle(handle)
        logger.info("检测到已有实例在运行")
        return False

    return True


def main():
    # 单实例检测
    if not try_acquire_mutex():
        print("[PomodoroTimer] Application is already running. Check system tray.")
        sys.exit(0)

    from app import run
    run()


if __name__ == "__main__":
    main()
