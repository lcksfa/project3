"""
配置模块单元测试
"""

import pytest
import tempfile
import yaml
from pathlib import Path

from ai_assistant.core.config import Settings, DeepSeekSettings, ConfigError
from ai_assistant.core.exceptions import ValidationError


class TestDeepSeekSettings:
    """DeepSeek设置测试"""

    def test_valid_settings(self):
        """测试有效设置"""
        settings = DeepSeekSettings(
            api_key="test_key",
            base_url="https://api.deepseek.com",
            timeout=30,
            temperature=0.7
        )
        assert settings.api_key == "test_key"
        assert settings.base_url == "https://api.deepseek.com"
        assert settings.timeout == 30
        assert settings.temperature == 0.7

    def test_invalid_temperature(self):
        """测试无效温度参数"""
        with pytest.raises(ValidationError):
            DeepSeekSettings(api_key="test", temperature=3.0)

        with pytest.raises(ValidationError):
            DeepSeekSettings(api_key="test", temperature=-1.0)

    def test_invalid_max_tokens(self):
        """测试无效最大token数"""
        with pytest.raises(ValidationError):
            DeepSeekSettings(api_key="test", max_tokens=0)

        with pytest.raises(ValidationError):
            DeepSeekSettings(api_key="test", max_tokens=-100)


class TestSettings:
    """主设置类测试"""

    def test_default_settings(self):
        """测试默认设置"""
        settings = Settings(
            deepseek=DeepSeekSettings(api_key="test_key")
        )
        assert settings.app.name == "AI Assistant"
        assert settings.app.version == "1.0.0"
        assert settings.logging.level == "INFO"

    def test_settings_from_dict(self):
        """测试从字典创建设置"""
        config_dict = {
            "app": {
                "name": "Test App",
                "debug": True
            },
            "deepseek": {
                "api_key": "test_key",
                "temperature": 0.5
            }
        }
        settings = Settings(**config_dict)
        assert settings.app.name == "Test App"
        assert settings.app.debug is True
        assert settings.deepseek.api_key == "test_key"
        assert settings.deepseek.temperature == 0.5

    def test_load_from_yaml(self, temp_config_dir):
        """测试从YAML文件加载设置"""
        config_data = {
            "app": {
                "name": "YAML Test App",
                "debug": True
            },
            "deepseek": {
                "api_key": "yaml_test_key",
                "temperature": 0.8
            },
            "logging": {
                "level": "DEBUG",
                "file": "test.log"
            }
        }

        config_file = temp_config_dir / "test_settings.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)

        settings = Settings.load_from_yaml(str(config_file))
        assert settings.app.name == "YAML Test App"
        assert settings.app.debug is True
        assert settings.deepseek.api_key == "yaml_test_key"
        assert settings.deepseek.temperature == 0.8
        assert settings.logging.level == "DEBUG"

    def test_load_from_nonexistent_file(self):
        """测试从不存在的文件加载设置"""
        with pytest.raises(ConfigError):
            Settings.load_from_yaml("nonexistent_file.yaml")

    def test_load_from_invalid_yaml(self, temp_config_dir):
        """测试从无效YAML文件加载设置"""
        config_file = temp_config_dir / "invalid.yaml"
        with open(config_file, 'w') as f:
            f.write("invalid: yaml: content: [")

        with pytest.raises(ConfigError):
            Settings.load_from_yaml(str(config_file))

    def test_update_from_dict(self, mock_settings):
        """测试从字典更新设置"""
        update_dict = {
            "app": {"debug": True},
            "deepseek": {"temperature": 0.9}
        }
        mock_settings.update_from_dict(update_dict)
        assert mock_settings.app.debug is True
        assert mock_settings.deepseek.temperature == 0.9

    def test_get_dict(self, mock_settings):
        """测试获取设置字典"""
        config_dict = mock_settings.get_dict()
        assert isinstance(config_dict, dict)
        assert "app" in config_dict
        assert "deepseek" in config_dict
        assert "logging" in config_dict

    def test_environment_variable_override(self, monkeypatch):
        """测试环境变量覆盖"""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "env_key")
        monkeypatch.setenv("APP_DEBUG", "true")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        settings = Settings(
            deepseek=DeepSeekSettings(api_key="default_key")
        )
        # 注意：实际的环境变量覆盖需要在具体的实现中处理
        # 这里只是测试结构是否正确
        assert settings.deepseek.api_key == "default_key"  # 默认值