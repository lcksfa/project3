"""
DeepSeek客户端单元测试
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import httpx

from ai_assistant.services.deepseek_client import (
    DeepSeekClient, Message, ChatCompletionRequest, ChatCompletionResponse
)
from ai_assistant.core.exceptions import (
    APIError, AuthenticationError, RateLimitError, ServerError, TimeoutError
)


class TestMessage:
    """消息模型测试"""

    def test_user_message(self):
        """测试用户消息"""
        message = Message(role="user", content="Hello")
        assert message.role == "user"
        assert message.content == "Hello"
        assert message.name is None

    def test_system_message_with_name(self):
        """测试带名称的系统消息"""
        message = Message(role="system", content="System prompt", name="system")
        assert message.role == "system"
        assert message.content == "System prompt"
        assert message.name == "system"


class TestChatCompletionRequest:
    """聊天完成请求模型测试"""

    def test_basic_request(self):
        """测试基础请求"""
        messages = [
            Message(role="user", content="Hello")
        ]
        request = ChatCompletionRequest(
            model="deepseek-chat",
            messages=messages
        )
        assert request.model == "deepseek-chat"
        assert len(request.messages) == 1
        assert request.temperature == 0.7
        assert request.stream is False

    def test_request_with_options(self):
        """测试带选项的请求"""
        messages = [
            Message(role="system", content="System"),
            Message(role="user", content="Hello")
        ]
        request = ChatCompletionRequest(
            model="deepseek-chat",
            messages=messages,
            temperature=0.5,
            max_tokens=1000,
            stream=True
        )
        assert request.temperature == 0.5
        assert request.max_tokens == 1000
        assert request.stream is True


class TestDeepSeekClient:
    """DeepSeek客户端测试"""

    @pytest.fixture
    def client(self, mock_deepseek_settings):
        """创建客户端实例"""
        return DeepSeekClient(mock_deepseek_settings)

    @pytest.fixture
    def mock_httpx_client(self):
        """模拟httpx客户端"""
        mock_client = Mock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock()
        mock_client.aclose = AsyncMock()
        mock_client.stream = AsyncMock()
        return mock_client

    @pytest.mark.asyncio
    async def test_client_context_manager(self, client, mock_httpx_client):
        """测试客户端上下文管理器"""
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            async with client as c:
                assert c is client
                mock_httpx_client.post.assert_not_called()  # 不应该自动创建客户端

    def test_create_message_methods(self, client):
        """测试创建消息的方法"""
        # 测试系统消息
        system_msg = client.create_system_message("You are helpful")
        assert system_msg.role == "system"
        assert system_msg.content == "You are helpful"

        # 测试用户消息
        user_msg = client.create_user_message("Hello")
        assert user_msg.role == "user"
        assert user_msg.content == "Hello"

        # 测试助手消息
        assistant_msg = client.create_assistant_message("Hi there!")
        assert assistant_msg.role == "assistant"
        assert assistant_msg.content == "Hi there!"

        # 测试通用消息创建
        custom_msg = client.create_message("custom", "Custom message")
        assert custom_msg.role == "custom"
        assert custom_msg.content == "Custom message"

    @pytest.mark.asyncio
    async def test_chat_completion_success(
        self, client, mock_api_response, mock_httpx_client
    ):
        """测试成功的聊天完成请求"""
        # 设置模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response
        mock_httpx_client.post.return_value = mock_response

        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            async with client:
                messages = [client.create_user_message("Hello")]
                request = ChatCompletionRequest(
                    model="deepseek-chat",
                    messages=messages
                )

                response = await client.chat_completion(request)

                assert isinstance(response, ChatCompletionResponse)
                assert response.id == "chatcmpl-test123"
                assert response.model == "deepseek-chat"
                assert len(response.choices) == 1
                assert response.choices[0]["message"]["content"] == "这是一个测试回复。"

                # 验证请求参数
                mock_httpx_client.post.assert_called_once()
                call_args = mock_httpx_client.post.call_args
                assert call_args[0][0] == "/v1/chat/completions"
                assert "json" in call_args[1]
                assert call_args[1]["json"]["model"] == "deepseek-chat"

    @pytest.mark.asyncio
    async def test_chat_completion_authentication_error(
        self, client, mock_httpx_client
    ):
        """测试认证错误"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {"message": "Invalid API key", "code": "auth_001"}
        }
        mock_httpx_client.post.return_value = mock_response

        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            async with client:
                messages = [client.create_user_message("Hello")]
                request = ChatCompletionRequest(
                    model="deepseek-chat",
                    messages=messages
                )

                with pytest.raises(AuthenticationError) as exc_info:
                    await client.chat_completion(request)

                assert "Invalid API key" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_chat_completion_rate_limit_error(
        self, client, mock_httpx_client
    ):
        """测试速率限制错误"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            "error": {"message": "Rate limit exceeded", "code": "rate_001"}
        }
        mock_httpx_client.post.return_value = mock_response

        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            async with client:
                messages = [client.create_user_message("Hello")]
                request = ChatCompletionRequest(
                    model="deepseek-chat",
                    messages=messages
                )

                with pytest.raises(RateLimitError) as exc_info:
                    await client.chat_completion(request)

                assert "Rate limit exceeded" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_chat_completion_server_error(
        self, client, mock_httpx_client
    ):
        """测试服务器错误"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {
            "error": {"message": "Internal server error", "code": "server_001"}
        }
        mock_httpx_client.post.return_value = mock_response

        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            async with client:
                messages = [client.create_user_message("Hello")]
                request = ChatCompletionRequest(
                    model="deepseek-chat",
                    messages=messages
                )

                with pytest.raises(ServerError) as exc_info:
                    await client.chat_completion(request)

                assert "Internal server error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_chat_completion_timeout(self, client, mock_httpx_client):
        """测试请求超时"""
        import httpx
        mock_httpx_client.post.side_effect = httpx.TimeoutException("Request timeout")

        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            async with client:
                messages = [client.create_user_message("Hello")]
                request = ChatCompletionRequest(
                    model="deepseek-chat",
                    messages=messages
                )

                with pytest.raises(TimeoutError) as exc_info:
                    await client.chat_completion(request)

                assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_chat_completion_stream_success(
        self, client, mock_httpx_client
    ):
        """测试成功的流式聊天完成请求"""
        # 模拟流式响应
        mock_stream = AsyncMock()
        mock_stream.aiter_lines.return_value = [
            'data: {"choices": [{"delta": {"content": "Hello"}}]}',
            'data: {"choices": [{"delta": {"content": " world"}}]}',
            'data: {"choices": [{"delta": {"content": "!"}}]}',
            'data: [DONE]'
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None
        mock_httpx_client.stream.return_value.__aenter__.return_value = mock_response

        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            async with client:
                messages = [client.create_user_message("Hello")]
                request = ChatCompletionRequest(
                    model="deepseek-chat",
                    messages=messages,
                    stream=True
                )

                # 收集流式响应
                response_parts = []
                async for part in client.chat_completion_stream(request):
                    response_parts.append(part)

                assert response_parts == ["Hello", " world", "!"]

    @pytest.mark.asyncio
    async def test_chat_completion_with_custom_request_id(
        self, client, mock_api_response, mock_httpx_client
    ):
        """测试带自定义请求ID的聊天完成"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response
        mock_httpx_client.post.return_value = mock_response

        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            async with client:
                messages = [client.create_user_message("Hello")]
                request = ChatCompletionRequest(
                    model="deepseek-chat",
                    messages=messages
                )

                custom_request_id = "test_request_123"
                response = await client.chat_completion(request, custom_request_id)

                assert response.id == "chatcmpl-test123"
                # 验证请求ID被正确记录（通过日志或其他方式）

    @pytest.mark.asyncio
    async def test_close_client(self, client, mock_httpx_client):
        """测试关闭客户端"""
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            async with client:
                pass  # 自动调用 __aexit__

            # 验证客户端被关闭
            mock_httpx_client.aclose.assert_called_once()

    def test_client_initialization(self, mock_deepseek_settings):
        """测试客户端初始化"""
        client = DeepSeekClient(mock_deepseek_settings)
        assert client.config == mock_deepseek_settings
        assert client._client is None