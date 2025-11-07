"""
配置适配器

为服务层提供统一的配置接口。
"""

from typing import Dict, Any
from .config_simple import get_settings as get_simple_settings


class ConfigAdapter:
    """配置适配器，将简化配置转换为服务所需的格式"""

    def __init__(self):
        self._simple_settings = get_simple_settings()

    @property
    def deepseek(self) -> 'DeepSeekConfig':
        """获取DeepSeek配置"""
        return DeepSeekConfig(
            api_key=self._simple_settings.deepseek_api_key,
            base_url=self._simple_settings.deepseek_base_url,
            model=self._simple_settings.deepseek_model,
            temperature=self._simple_settings.deepseek_temperature,
            max_tokens=self._simple_settings.deepseek_max_tokens,
            timeout=30,
            max_retries=3,
            retry_delay=1
        )

    @property
    def logging(self) -> 'LoggingConfig':
        """获取日志配置"""
        return LoggingConfig(
            level=getattr(self._simple_settings, 'log_level', 'INFO'),
            format=getattr(self._simple_settings, 'log_format', 'console'),
            file=getattr(self._simple_settings, 'log_file', 'logs/app.log'),
            max_file_size="10MB",
            backup_count=5,
            console_output=True
        )

    @property
    def services(self) -> 'ServicesConfig':
        """获取服务配置"""
        return ServicesConfig(
            chat=ChatConfig(
                max_history_length=20,
                default_temperature=0.7,
                max_tokens=2048
            ),
            summary=SummaryConfig(
                max_input_length=10000,
                max_summary_length=500,
                temperature=0.3
            ),
            translate=TranslateConfig(
                max_text_length=5000,
                supported_languages=[
                    "中文", "English", "日本語", "Español", "Français",
                    "Deutsch", "한국어"
                ]
            )
        )


class DeepSeekConfig:
    """DeepSeek配置"""
    def __init__(self, api_key: str, base_url: str, model: str, temperature: float,
                 max_tokens: int, timeout: int, max_retries: int, retry_delay: int):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay


class LoggingConfig:
    """日志配置"""
    def __init__(self, level: str, format: str, file: str, max_file_size: str,
                 backup_count: int, console_output: bool):
        self.level = level
        self.format = format
        self.file = file
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.console_output = console_output


class ChatConfig:
    """聊天配置"""
    def __init__(self, max_history_length: int, default_temperature: float, max_tokens: int):
        self.max_history_length = max_history_length
        self.default_temperature = default_temperature
        self.max_tokens = max_tokens


class SummaryConfig:
    """总结配置"""
    def __init__(self, max_input_length: int, max_summary_length: int, temperature: float):
        self.max_input_length = max_input_length
        self.max_summary_length = max_summary_length
        self.temperature = temperature


class TranslateConfig:
    """翻译配置"""
    def __init__(self, max_text_length: int, supported_languages: list):
        self.max_text_length = max_text_length
        self.supported_languages = supported_languages


class ServicesConfig:
    """服务配置"""
    def __init__(self, chat: ChatConfig, summary: SummaryConfig, translate: TranslateConfig):
        self.chat = chat
        self.summary = summary
        self.translate = translate


# 全局适配器实例
_adapter = None


def get_config_adapter() -> ConfigAdapter:
    """获取配置适配器实例"""
    global _adapter
    if _adapter is None:
        _adapter = ConfigAdapter()
    return _adapter