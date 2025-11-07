"""
配置管理模块

提供应用配置的加载、验证和管理功能。
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import Field, validator
from pydantic_settings import BaseSettings

from .exceptions import ConfigError


class DatabaseSettings(BaseSettings):
    """数据库配置"""
    url: str = Field(default="sqlite:///./app.db", description="数据库连接URL")
    echo: bool = Field(default=False, description="是否打印SQL语句")


class DeepSeekSettings(BaseSettings):
    """DeepSeek API配置"""
    base_url: str = Field(default="https://api.deepseek.com", description="API基础URL")
    api_key: str = Field(..., description="API密钥")
    timeout: int = Field(default=30, description="请求超时时间(秒)")
    max_retries: int = Field(default=3, description="最大重试次数")
    retry_delay: int = Field(default=1, description="重试延迟(秒)")
    model: str = Field(default="deepseek-chat", description="默认模型")
    max_tokens: int = Field(default=4096, description="最大token数")
    temperature: float = Field(default=0.7, description="默认温度参数")

    @validator('temperature')
    def validate_temperature(cls, v: float) -> float:
        if not 0.0 <= v <= 2.0:
            raise ValueError('Temperature must be between 0.0 and 2.0')
        return v

    @validator('max_tokens')
    def validate_max_tokens(cls, v: int) -> int:
        if v <= 0:
            raise ValueError('Max tokens must be positive')
        return v


class LoggingSettings(BaseSettings):
    """日志配置"""
    level: str = Field(default="INFO", description="日志级别")
    format: str = Field(default="json", description="日志格式")
    file: str = Field(default="logs/app.log", description="日志文件路径")
    max_file_size: str = Field(default="10MB", description="日志文件最大大小")
    backup_count: int = Field(default=5, description="日志备份数量")
    console_output: bool = Field(default=True, description="是否输出到控制台")

    @validator('level')
    def validate_level(cls, v: str) -> str:
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of {valid_levels}')
        return v.upper()


class ServiceSettings(BaseSettings):
    """服务配置"""
    max_history_length: int = Field(default=20, description="最大历史记录长度")
    default_temperature: float = Field(default=0.7, description="默认温度")
    max_tokens: int = Field(default=2048, description="最大token数")
    max_input_length: int = Field(default=10000, description="最大输入长度")
    max_summary_length: int = Field(default=500, description="最大总结长度")
    max_text_length: int = Field(default=5000, description="最大文本长度")


class SecuritySettings(BaseSettings):
    """安全配置"""
    max_request_size: str = Field(default="10MB", description="最大请求大小")
    requests_per_minute: int = Field(default=60, description="每分钟最大请求数")
    burst_size: int = Field(default=10, description="突发请求数")
    secret_key: str = Field(..., description="会话密钥")


class CacheSettings(BaseSettings):
    """缓存配置"""
    enabled: bool = Field(default=True, description="是否启用缓存")
    ttl: int = Field(default=3600, description="缓存生存时间(秒)")
    max_size: int = Field(default=1000, description="最大缓存条目数")


class PerformanceSettings(BaseSettings):
    """性能配置"""
    connection_pool_size: int = Field(default=10, description="连接池大小")
    request_timeout: int = Field(default=30, description="请求超时时间")
    max_concurrent_requests: int = Field(default=5, description="最大并发请求数")


class AppSettings(BaseSettings):
    """应用配置"""
    model_config = {"extra": "allow"}

    name: str = Field(default="AI Assistant", description="应用名称")
    version: str = Field(default="1.0.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    host: str = Field(default="0.0.0.0", description="服务器主机")
    port: int = Field(default=8501, description="服务器端口")
    environment: str = Field(default="development", description="运行环境")

    @validator('port')
    def validate_port(cls, v: int) -> int:
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v


class Settings(BaseSettings):
    """主配置类"""
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "env_nested_delimiter": "_",
        "extra": "allow"  # 允许额外字段
    }

    app: AppSettings = Field(default_factory=AppSettings)
    deepseek: DeepSeekSettings = Field(default_factory=DeepSeekSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    services: ServiceSettings = Field(default_factory=ServiceSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    performance: PerformanceSettings = Field(default_factory=PerformanceSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)

    @classmethod
    def load_from_yaml(cls, config_path: Optional[str] = None) -> "Settings":
        """从YAML文件加载配置"""
        if config_path is None:
            config_path = os.getenv("CONFIG_PATH", "config/settings.yaml")

        config_file = Path(config_path)
        if not config_file.exists():
            raise ConfigError(f"配置文件不存在: {config_path}")

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"配置文件格式错误: {e}")
        except Exception as e:
            raise ConfigError(f"读取配置文件失败: {e}")

        return cls(**config_data)

    def get_dict(self) -> Dict[str, Any]:
        """获取配置字典"""
        return self.dict()

    def update_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """从字典更新配置"""
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取全局配置实例"""
    global _settings
    if _settings is None:
        try:
            # 优先尝试从YAML文件加载
            _settings = Settings.load_from_yaml()
        except ConfigError:
            # 如果YAML文件不存在或加载失败，使用环境变量
            _settings = Settings()
    return _settings


def init_settings(config_path: Optional[str] = None) -> Settings:
    """初始化配置"""
    global _settings
    _settings = Settings.load_from_yaml(config_path)
    return _settings


def reload_settings() -> Settings:
    """重新加载配置"""
    global _settings
    _settings = None
    return get_settings()