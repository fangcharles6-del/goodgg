"""Windows 平台相关工具 — 单实例互斥体、数据目录路径。"""

import ctypes
import logging
from ctypes import wintypes

logger = logging.getLogger(__name__)

MUTEX_NAME = "Global\\ClipboardManagerMutex"

kernel32 = ctypes.windll.kernel32


def try_acquire_mutex() -> bool:
    """
    尝试创建命名互斥体以检测是否已有实例在运行。
    返回 True 表示成功获取（首次启动），False 表示已有实例。
    """
    handle = kernel32.CreateMutexW(None, True, MUTEX_NAME)
    if handle == 0:
        logger.error("创建互斥体失败")
        return True  # 出错时允许启动

    last_error = kernel32.GetLastError()
    if last_error == 183:  # ERROR_ALREADY_EXISTS
        kernel32.CloseHandle(handle)
        logger.info("检测到已有实例在运行")
        return False

    return True
