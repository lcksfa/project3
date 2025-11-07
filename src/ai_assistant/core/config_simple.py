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


class DeepSeekConfig:
    """DeepSeek配置类"""
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


class ChatConfig:
    """聊天配置类"""
    def __init__(self, max_history_length: int, default_temperature: float, max_tokens: int):
        self.max_history_length = max_history_length
        self.default_temperature = default_temperature
        self.max_tokens = max_tokens


class SummaryConfig:
    """总结配置类"""
    def __init__(self, max_input_length: int, max_summary_length: int, temperature: float):
        self.max_input_length = max_input_length
        self.max_summary_length = max_summary_length
        self.temperature = temperature


class TranslateConfig:
    """翻译配置类"""
    def __init__(self, max_text_length: int, supported_languages: list):
        self.max_text_length = max_text_length
        self.supported_languages = supported_languages


class ServicesConfig:
    """服务配置类（兼容性）"""
    def __init__(self, chat: ChatConfig, summary: SummaryConfig, translate: TranslateConfig):
        self.chat = chat
        self.summary = summary
        self.translate = translate

    @property
    def max_history_length(self) -> int:
        """获取聊天历史最大长度"""
        return self.chat.max_history_length

    @property
    def max_input_length(self) -> int:
        """获取输入最大长度（使用总结服务的配置）"""
        return self.summary.max_input_length

    @property
    def max_summary_length(self) -> int:
        """获取总结最大长度"""
        return self.summary.max_summary_length

    @property
    def max_text_length(self) -> int:
        """获取翻译文本最大长度"""
        return self.translate.max_text_length

    @property
    def temperature(self) -> float:
        """获取默认温度（使用聊天的默认温度）"""
        return self.chat.default_temperature

    @property
    def default_temperature(self) -> float:
        """获取默认温度"""
        return self.chat.default_temperature

    @property
    def max_tokens(self) -> int:
        """获取最大token数（使用聊天的配置）"""
        return self.chat.max_tokens


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

    # 动态配置缓存
    _deepseek_config: Optional["DeepSeekConfig"] = None
    _services_config: Optional["ServicesConfig"] = None

    @property
    def services(self) -> "ServicesConfig":
        """获取服务配置对象（兼容性）"""
        if self._services_config is None:
            self._services_config = ServicesConfig(
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
        return self._services_config

    @property
    def deepseek(self) -> "DeepSeekConfig":
        """获取DeepSeek配置对象（兼容性）"""
        if self._deepseek_config is None:
            self._deepseek_config = DeepSeekConfig(
                api_key=self.deepseek_api_key,
                base_url=self.deepseek_base_url,
                model=self.deepseek_model,
                temperature=self.deepseek_temperature,
                max_tokens=self.deepseek_max_tokens,
                timeout=30,
                max_retries=3,
                retry_delay=1
            )
        return self._deepseek_config

    @deepseek.setter
    def deepseek(self, value: "DeepSeekConfig"):
        """设置DeepSeek配置对象"""
        self._deepseek_config = value
        # 同时更新底层配置
        self.deepseek_api_key = value.api_key
        self.deepseek_base_url = value.base_url
        self.deepseek_model = value.model
        self.deepseek_temperature = value.temperature
        self.deepseek_max_tokens = value.max_tokens

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