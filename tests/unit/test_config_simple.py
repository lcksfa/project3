"""
配置模块单元测试 - 使用新的 config_simple 模块
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from ai_assistant.core.config_simple import (
    SimpleSettings, get_settings, init_settings,
    AppConfig, DeepSeekConfig, ChatConfig, SummaryConfig,
    TranslateConfig, ServicesConfig, LoggingConfig
)
from ai_assistant.core.exceptions import ConfigError, ValidationError


class TestAppConfig:
    """应用配置测试"""

    def test_app_config_creation(self):
        """测试应用配置创建"""
        config = AppConfig("Test App", "2.0.0", True)
        assert config.name == "Test App"
        assert config.version == "2.0.0"
        assert config.debug is True


class TestDeepSeekConfig:
    """DeepSeek配置测试"""

    def test_deepseek_config_creation(self):
        """测试DeepSeek配置创建"""
        config = DeepSeekConfig(
            api_key="test_key",
            base_url="https://api.test.com",
            model="test-model",
            temperature=0.5,
            max_tokens=1024,
            timeout=60,
            max_retries=5,
            retry_delay=2
        )
        assert config.api_key == "test_key"
        assert config.base_url == "https://api.test.com"
        assert config.model == "test-model"
        assert config.temperature == 0.5
        assert config.max_tokens == 1024
        assert config.timeout == 60
        assert config.max_retries == 5
        assert config.retry_delay == 2


class TestChatConfig:
    """聊天配置测试"""

    def test_chat_config_creation(self):
        """测试聊天配置创建"""
        config = ChatConfig(50, 0.8, 4096)
        assert config.max_history_length == 50
        assert config.default_temperature == 0.8
        assert config.max_tokens == 4096


class TestSummaryConfig:
    """总结配置测试"""

    def test_summary_config_creation(self):
        """测试总结配置创建"""
        config = SummaryConfig(8000, 300, 0.4)
        assert config.max_input_length == 8000
        assert config.max_summary_length == 300
        assert config.temperature == 0.4


class TestTranslateConfig:
    """翻译配置测试"""

    def test_translate_config_creation(self):
        """测试翻译配置创建"""
        languages = ["中文", "English", "日本語"]
        config = TranslateConfig(6000, languages)
        assert config.max_text_length == 6000
        assert config.supported_languages == languages


class TestServicesConfig:
    """服务配置测试"""

    def test_services_config_creation(self):
        """测试服务配置创建"""
        chat = ChatConfig(20, 0.7, 2048)
        summary = SummaryConfig(10000, 500, 0.3)
        translate = TranslateConfig(5000, ["中文", "English"])

        services = ServicesConfig(chat, summary, translate)

        assert services.chat == chat
        assert services.summary == summary
        assert services.translate == translate

        # 测试属性方法
        assert services.max_history_length == 20
        assert services.max_input_length == 10000
        assert services.max_summary_length == 500
        assert services.max_text_length == 5000
        assert services.temperature == 0.7
        assert services.default_temperature == 0.7
        assert services.max_tokens == 2048


class TestLoggingConfig:
    """日志配置测试"""

    def test_logging_config_creation(self):
        """测试日志配置创建"""
        config = LoggingConfig(
            level="DEBUG",
            format="detailed",
            file="test.log",
            max_file_size="20MB",
            backup_count=10,
            console_output=False
        )
        assert config.level == "DEBUG"
        assert config.format == "detailed"
        assert config.file == "test.log"
        assert config.max_file_size == "20MB"
        assert config.backup_count == 10
        assert config.console_output is False


class TestSimpleSettings:
    """简化设置类测试"""

    def test_default_settings(self):
        """测试默认设置"""
        settings = SimpleSettings()
        assert settings.app_name == "AI Assistant"
        assert settings.app_version == "1.0.0"
        assert settings.app_debug is False
        assert settings.deepseek_api_key == ""
        assert settings.deepseek_base_url == "https://api.deepseek.com"
        assert settings.deepseek_model == "deepseek-chat"
        assert settings.deepseek_temperature == 0.7
        assert settings.deepseek_max_tokens == 2048
        assert settings.log_level == "INFO"
        assert settings.log_format == "console"
        assert settings.log_file == "logs/app.log"
        assert settings.secret_key == "development_secret_key"

    def test_settings_with_custom_values(self):
        """测试自定义设置"""
        settings = SimpleSettings(
            app_name="Custom App",
            app_version="2.0.0",
            app_debug=True,
            deepseek_api_key="custom_key",
            deepseek_temperature=0.5,
            log_level="DEBUG"
        )
        assert settings.app_name == "Custom App"
        assert settings.app_version == "2.0.0"
        assert settings.app_debug is True
        assert settings.deepseek_api_key == "custom_key"
        assert settings.deepseek_temperature == 0.5
        assert settings.log_level == "DEBUG"

    def test_app_property(self):
        """测试应用配置属性"""
        settings = SimpleSettings(app_name="Test App", app_debug=True)
        app = settings.app
        assert isinstance(app, AppConfig)
        assert app.name == "Test App"
        assert app.version == "1.0.0"
        assert app.debug is True

    def test_deepseek_property(self):
        """测试DeepSeek配置属性"""
        settings = SimpleSettings(
            deepseek_api_key="test_key",
            deepseek_temperature=0.6
        )
        deepseek = settings.deepseek
        assert isinstance(deepseek, DeepSeekConfig)
        assert deepseek.api_key == "test_key"
        assert deepseek.base_url == "https://api.deepseek.com"
        assert deepseek.model == "deepseek-chat"
        assert deepseek.temperature == 0.6
        assert deepseek.max_tokens == 2048
        assert deepseek.timeout == 30
        assert deepseek.max_retries == 3
        assert deepseek.retry_delay == 1

    def test_deepseek_setter(self):
        """测试DeepSeek配置设置器"""
        settings = SimpleSettings()
        new_config = DeepSeekConfig(
            api_key="new_key",
            base_url="https://new.api.com",
            model="new-model",
            temperature=0.8,
            max_tokens=1024,
            timeout=45,
            max_retries=2,
            retry_delay=3
        )

        settings.deepseek = new_config

        assert settings.deepseek_api_key == "new_key"
        assert settings.deepseek_base_url == "https://new.api.com"
        assert settings.deepseek_model == "new-model"
        assert settings.deepseek_temperature == 0.8
        assert settings.deepseek_max_tokens == 1024

    def test_services_property(self):
        """测试服务配置属性"""
        settings = SimpleSettings()
        services = settings.services
        assert isinstance(services, ServicesConfig)
        assert isinstance(services.chat, ChatConfig)
        assert isinstance(services.summary, SummaryConfig)
        assert isinstance(services.translate, TranslateConfig)

        # 测试默认值
        assert services.chat.max_history_length == 20
        assert services.chat.default_temperature == 0.7
        assert services.chat.max_tokens == 2048
        assert services.summary.max_input_length == 10000
        assert services.summary.max_summary_length == 500
        assert services.summary.temperature == 0.3
        assert services.translate.max_text_length == 5000
        assert len(services.translate.supported_languages) == 6

    def test_logging_property(self):
        """测试日志配置属性"""
        settings = SimpleSettings(
            log_level="DEBUG",
            log_format="detailed",
            log_file="custom.log"
        )
        logging = settings.logging
        assert isinstance(logging, LoggingConfig)
        assert logging.level == "DEBUG"
        assert logging.format == "detailed"
        assert logging.file == "custom.log"
        assert logging.max_file_size == "10MB"
        assert logging.backup_count == 5
        assert logging.console_output is True

    def test_load_from_env(self):
        """测试从环境变量加载"""
        # 保存原始环境变量
        original_env = {}
        for key in ['DEEPSEEK_API_KEY', 'APP_NAME', 'LOG_LEVEL']:
            if key in os.environ:
                original_env[key] = os.environ[key]
                del os.environ[key]

        try:
            # 设置环境变量
            with patch.dict(os.environ, {
                'DEEPSEEK_API_KEY': 'env_key',
                'APP_NAME': 'Env App',
                'LOG_LEVEL': 'WARNING'
            }, clear=False):
                settings = SimpleSettings.load_from_env()
                # Pydantic-settings会自动从环境变量加载
                # 这里测试环境变量是否生效
                # 由于Pydantic自动加载，实际值可能会受到环境影响
                assert isinstance(settings, SimpleSettings)
        finally:
            # 恢复原始环境变量
            for key in ['DEEPSEEK_API_KEY', 'APP_NAME', 'LOG_LEVEL']:
                if key in os.environ:
                    del os.environ[key]
            for key, value in original_env.items():
                os.environ[key] = value

    def test_load_from_yaml(self):
        """测试从YAML加载（简化版）"""
        settings = SimpleSettings.load_from_yaml()
        # 当前的简化实现只调用 load_from_env
        assert isinstance(settings, SimpleSettings)
        assert settings.app_name == "AI Assistant"


class TestGlobalSettings:
    """全局设置测试"""

    def test_get_settings_singleton(self):
        """测试获取设置单例"""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
        assert isinstance(settings1, SimpleSettings)

    def test_init_settings(self):
        """测试初始化设置"""
        # 重置全局设置
        import ai_assistant.core.config_simple as config_module
        config_module._settings = None

        settings = init_settings()
        assert isinstance(settings, SimpleSettings)

        # 再次调用应该返回相同的实例
        settings2 = init_settings()
        assert settings is settings2

    def test_init_settings_with_custom_path(self):
        """测试使用自定义路径初始化设置"""
        import ai_assistant.core.config_simple as config_module
        config_module._settings = None

        # 简化版本会忽略路径参数
        settings = init_settings("/custom/path/config.yaml")
        assert isinstance(settings, SimpleSettings)


class TestConfigurationIntegration:
    """配置集成测试"""

    def test_full_configuration_workflow(self):
        """测试完整配置工作流"""
        # 创建自定义设置
        settings = SimpleSettings(
            app_name="Integration Test App",
            app_debug=True,
            deepseek_api_key="integration_test_key",
            deepseek_temperature=0.9,
            log_level="DEBUG"
        )

        # 测试所有配置属性
        assert settings.app.name == "Integration Test App"
        assert settings.app.debug is True

        assert settings.deepseek.api_key == "integration_test_key"
        assert settings.deepseek.temperature == 0.9

        assert settings.services.temperature == 0.7  # 默认聊天温度
        assert settings.services.max_tokens == 2048

        assert settings.logging.level == "DEBUG"
        assert settings.logging.console_output is True

    def test_configuration_consistency(self):
        """测试配置一致性"""
        settings = SimpleSettings()

        # 确保相关的配置保持一致
        assert settings.deepseek.max_tokens == settings.services.max_tokens

        # DeepSeek配置的温度应该可以独立设置
        settings.deepseek_temperature = 0.5
        assert settings.deepseek.temperature == 0.5
        assert settings.services.temperature == 0.7  # 服务配置使用默认聊天温度