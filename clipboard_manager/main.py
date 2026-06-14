"""历史粘贴板 — 入口文件。

双击运行此 .py 文件或打包后的 .exe 即可启动。
"""

import sys
import os

# 确保项目根目录在 Python 路径中
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from utils.platform_utils import try_acquire_mutex
from app import run


def main():
    # 单实例检测
    if not try_acquire_mutex():
        print("历史粘贴板已在运行中。请查看系统托盘图标。")
        sys.exit(0)

    run()


if __name__ == "__main__":
    main()
