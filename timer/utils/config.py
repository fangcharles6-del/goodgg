"""番茄钟配置读写 — JSON 格式存储在 AppData 目录下。"""

import json
import logging
import os
from dataclasses import dataclass, asdict
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

APP_NAME = "PomodoroTimer"
CONFIG_FILENAME = "config.json"


@dataclass
class TimerConfig:
    """番茄钟配置数据模型。"""
    focus_duration: int = 25          # 专注时长（分钟）
    short_break_duration: int = 5     # 短休息时长（分钟）
    always_on_top: bool = True        # 窗口默认置顶


@lru_cache(maxsize=1)
def get_config_dir() -> Path:
    """获取配置目录路径（缓存）：%APPDATA%/PomodoroTimer/"""
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    config_dir = Path(appdata) / APP_NAME
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_path() -> str:
    """获取配置文件完整路径。"""
    return str(get_config_dir() / CONFIG_FILENAME)


def load_config() -> TimerConfig:
    """从 JSON 文件加载配置，缺失或损坏时使用默认值。"""
    config = TimerConfig()
    config_path = get_config_path()

    if not os.path.exists(config_path):
        save_config(config)
        return config

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        config.focus_duration = data.get("focus_duration", 25)
        config.short_break_duration = data.get("short_break_duration", 5)
        config.always_on_top = data.get("always_on_top", True)
        logger.info("配置加载成功: %s", config_path)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("配置文件损坏，使用默认值: %s", e)
        bak_path = config_path + ".bak"
        try:
            os.replace(config_path, bak_path)
        except OSError:
            pass
        save_config(config)

    return config


def save_config(config: TimerConfig) -> None:
    """保存配置到 JSON 文件。"""
    config_path = get_config_path()
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(asdict(config), f, indent=2, ensure_ascii=False)
    logger.info("配置已保存: %s", config_path)
