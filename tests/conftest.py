"""
pytest配置文件

提供测试夹具和全局配置。
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from typing import Generator, AsyncGenerator
import tempfile
import os
from pathlib import Path

from ai_assistant.core.config import Settings, DeepSeekSettings, LoggingSettings
from ai_assistant.services.deepseek_client import DeepSeekClient
from ai_assistant.services.chat_service import ChatService
from ai_assistant.services.summary_service import SummaryService
from ai_assistant.services.translate_service import TranslationService


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_deepseek_settings():
    """模拟DeepSeek设置"""
    return DeepSeekSettings(
        api_key="test_api_key",
        base_url="https://api.deepseek.com",
        timeout=30,
        max_retries=3,
        model="deepseek-chat",
        max_tokens=4096,
        temperature=0.7
    )


@pytest.fixture
def mock_settings(mock_deepseek_settings):
    """模拟应用设置"""
    return Settings(
        deepseek=mock_deepseek_settings,
        logging=LoggingSettings(level="DEBUG", console_output=False)
    )


@pytest.fixture
def temp_config_dir():
    """临时配置目录"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_deepseek_client():
    """模拟DeepSeek客户端"""
    client = Mock(spec=DeepSeekClient)
    client.chat_completion = AsyncMock()
    client.chat_completion_stream = AsyncMock()
    client.create_message = Mock()
    client.create_system_message = Mock()
    client.create_user_message = Mock()
    client.create_assistant_message = Mock()

    # 模拟流式响应
    async def mock_stream():
        yield "Hello"
        yield " world"
        yield "!"

    client.chat_completion_stream.return_value = mock_stream()

    return client


@pytest.fixture
def chat_service(mock_deepseek_client):
    """聊天服务实例"""
    return ChatService(mock_deepseek_client)


@pytest.fixture
def summary_service(mock_deepseek_client):
    """总结服务实例"""
    return SummaryService(mock_deepseek_client)


@pytest.fixture
def translate_service(mock_deepseek_client):
    """翻译服务实例"""
    return TranslationService(mock_deepseek_client)


@pytest.fixture
def sample_text():
    """示例文本"""
    return """
    人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，它致力于创建能够执行通常需要人类智能的任务的系统。
    这些任务包括学习、推理、问题解决、感知和语言理解。AI技术包括机器学习、深度学习、自然语言处理、计算机视觉等。
    近年来，AI在医疗诊断、自动驾驶、金融分析等领域取得了重大突破，正在改变我们的生活方式和工作模式。
    然而，AI发展也面临着挑战，如数据隐私、算法偏见、就业影响等问题需要我们认真思考和解决。
    """


@pytest.fixture
def sample_chat_messages():
    """示例聊天消息"""
    return [
        {"role": "system", "content": "你是一个有用的AI助手。"},
        {"role": "user", "content": "你好，请介绍一下人工智能。"},
        {"role": "assistant", "content": "你好！人工智能是计算机科学的一个分支..."}
    ]


@pytest.fixture
def mock_api_response():
    """模拟API响应"""
    return {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "deepseek-chat",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "这是一个测试回复。"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
    }


@pytest.fixture
def mock_translation_response():
    """模拟翻译响应"""
    return {
        "id": "translate-test123",
        "object": "translation",
        "created": 1234567890,
        "model": "deepseek-chat",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Hello, this is a test translation."
                },
                "finish_reason": "stop"
            }
        ]
    }


@pytest.fixture
def mock_summary_response():
    """模拟总结响应"""
    return {
        "id": "summary-test123",
        "object": "summary",
        "created": 1234567890,
        "model": "deepseek-chat",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "AI是计算机科学分支，致力于创建智能系统。包括机器学习、深度学习等技术，在医疗、自动驾驶等领域应用广泛。"
                },
                "finish_reason": "stop"
            }
        ]
    }


class MockResponse:
    """模拟HTTP响应"""

    def __init__(self, status_code: int, json_data: dict):
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


@pytest.fixture
def mock_httpx_response():
    """模拟httpx响应"""
    def _create_response(status_code: int = 200, json_data: dict = None):
        return MockResponse(status_code, json_data or {})
    return _create_response


@pytest.fixture
def mock_logger():
    """模拟日志记录器"""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.debug = Mock()
    return logger


# 标记定义
pytest_plugins = []

# 自定义标记
def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line(
        "markers", "unit: 单元测试"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试"
    )


# 测试数据
@pytest.fixture
def test_data_dir():
    """测试数据目录"""
    return Path(__file__).parent / "test_data"


@pytest.fixture
def create_temp_file():
    """创建临时文件的辅助函数"""
    def _create_temp_file(content: str, suffix: str = ".txt") -> Path:
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            f.write(content)
            return Path(f.name)
    return _create_temp_file


@pytest.fixture
def async_test():
    """异步测试辅助装饰器"""
    def _run_async(coro):
        return asyncio.run(coro)
    return _run_async


# 环境变量设置
@pytest.fixture(autouse=True)
def set_test_env():
    """设置测试环境变量"""
    os.environ["APP_ENV"] = "testing"
    os.environ["LOG_LEVEL"] = "DEBUG"

    yield

    # 清理环境变量
    for key in ["APP_ENV", "LOG_LEVEL"]:
        if key in os.environ:
            del os.environ[key]