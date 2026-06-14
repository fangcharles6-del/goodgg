"""应用配置文件读写 — JSON 格式存储在 AppData 目录下。"""

import json
import logging
import os
from pathlib import Path

from database.models import AppConfig

logger = logging.getLogger(__name__)

CONFIG_FILENAME = "config.json"


def get_config_dir() -> Path:
    """获取配置目录路径：%APPDATA%/ClipboardManager/"""
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    config_dir = Path(appdata) / "ClipboardManager"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_db_path() -> str:
    """获取数据库文件完整路径。"""
    return str(get_config_dir() / "clipboard.db")


def get_config_path() -> str:
    """获取配置文件完整路径。"""
    return str(get_config_dir() / CONFIG_FILENAME)


def load_config() -> AppConfig:
    """从 JSON 文件加载配置，缺失或损坏时使用默认值。"""
    config = AppConfig()
    config_path = get_config_path()

    if not os.path.exists(config_path):
        save_config(config)
        return config

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        config.retention_days = data.get("retention_days", 3)
        config.compress_images = data.get("compress_images", True)
        logger.info("配置加载成功: %s", config_path)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("配置文件损坏，使用默认值: %s", e)
        # 备份损坏的配置文件
        bak_path = config_path + ".bak"
        try:
            os.replace(config_path, bak_path)
        except OSError:
            pass
        save_config(config)

    return config


def save_config(config: AppConfig) -> None:
    """保存配置到 JSON 文件。"""
    config_path = get_config_path()
    data = {
        "retention_days": config.retention_days,
        "compress_images": config.compress_images,
    }
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info("配置已保存: %s", config_path)
