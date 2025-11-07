"""
简化的配置管理模块

解决 Pydantic v2 兼容性问题。
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class AppConfig:
    """应用配置类"""
    def __init__(self, name: str, version: str, debug: bool):
        self.name = name
        self.version = version
        self.debug = debug


class LoggingConfig:
    """日志配置类"""
    def __init__(self, level: str, format: str, file: str, max_file_size: str,
                 backup_count: int, console_output: bool):
        self.level = level
        self.format = format
        self.file = file
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.console_output = console_output


class SimpleSettings(BaseSettings):
    """简化的配置类"""

    model_config = {"extra": "allow"}

    # 应用配置
    app_name: str = "AI Assistant"
    app_version: str = "1.0.0"
    app_debug: bool = False

    # DeepSeek API配置
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    deepseek_temperature: float = 0.7
    deepseek_max_tokens: int = 2048

    # 日志配置
    log_level: str = "INFO"
    log_format: str = "console"
    log_file: str = "logs/app.log"

    # 安全配置
    secret_key: str = "development_secret_key"

    @property
    def app(self) -> "AppConfig":
        """获取应用配置对象（兼容性）"""
        return AppConfig(
            name=self.app_name,
            version=self.app_version,
            debug=self.app_debug
        )

    @property
    def logging(self) -> "LoggingConfig":
        """获取日志配置对象（兼容性）"""
        return LoggingConfig(
            level=self.log_level,
            format=self.log_format,
            file=self.log_file,
            max_file_size="10MB",
            backup_count=5,
            console_output=True
        )

    @classmethod
    def load_from_env(cls) -> "SimpleSettings":
        """从环境变量加载配置"""
        return cls()

    @classmethod
    def load_from_yaml(cls, config_path: Optional[str] = None) -> "SimpleSettings":
        """从YAML文件加载配置（简化版，暂时只从环境变量加载）"""
        return cls.load_from_env()


# 全局配置实例
_settings: Optional[SimpleSettings] = None


def get_settings() -> SimpleSettings:
    """获取全局配置实例"""
    global _settings
    if _settings is None:
        _settings = SimpleSettings.load_from_env()
    return _settings


def init_settings(config_path: Optional[str] = None) -> SimpleSettings:
    """初始化配置"""
    global _settings
    _settings = SimpleSettings.load_from_yaml(config_path)
    return _settings