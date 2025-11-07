"""
多功能AI助手

一个企业级的Python AI助手应用，集成DeepSeek API，
提供聊天、文本总结、翻译等多种AI功能。
"""

__version__ = "1.0.0"
__author__ = "AI Assistant Team"
__email__ = "team@ai-assistant.com"

from .core.config import Settings
from .core.logger import get_logger
from .core.exceptions import AIAssistantError, APIError, ConfigError

__all__ = [
    "Settings",
    "get_logger",
    "AIAssistantError",
    "APIError",
    "ConfigError",
    "__version__",
]