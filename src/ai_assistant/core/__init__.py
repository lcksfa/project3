"""
核心模块

提供应用的核心基础设施功能，包括配置管理、日志记录和异常处理。
"""

from .config_simple import get_settings
from .logger import get_logger, setup_logging
from .exceptions import AIAssistantError, APIError, ConfigError, ValidationError

# 为了向后兼容，提供一个空的 Settings 类
class Settings:
    """向后兼容的 Settings 类（已弃用）"""
    pass

__all__ = [
    "Settings",
    "get_settings",
    "get_logger",
    "setup_logging",
    "AIAssistantError",
    "APIError",
    "ConfigError",
    "ValidationError",
]