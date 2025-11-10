"""
聊天服务单元测试
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from ai_assistant.services.chat_service import ChatService, ChatSession
from ai_assistant.services.deepseek_client import DeepSeekClient, Message, ChatCompletionResponse
from ai_assistant.core.config_simple import SimpleSettings
from ai_assistant.core.exceptions import ValidationError, ServiceError


class TestChatSession:
    """聊天会话测试"""

    def test_chat_session_creation(self):
        """测试聊天会话创建"""
        session = ChatSession(
            session_id="test_conv_123"
        )
        assert session.session_id == "test_conv_123"
        assert session.messages == []

    def test_chat_session_add_message(self):
        """测试添加消息到会话"""
        session = ChatSession(
            session_id="test_conv_123"
        )

        # 添加消息
        message = Message(role="user", content="Hello, how are you?", name="user")
        session.add_message(message)
        assert len(session.messages) == 1
        assert session.messages[0].role == "user"
        assert session.messages[0].content == "Hello, how are you?"

    def test_chat_session_get_messages(self):
        """测试获取会话消息"""
        session = ChatSession(
            session_id="test_conv_123"
        )

        # 添加消息
        msg1 = Message(role="system", content="You are a helpful assistant", name="system")
        msg2 = Message(role="user", content="Hello", name="user")
        msg3 = Message(role="assistant", content="Hi there!", name="assistant")

        session.add_message(msg1)
        session.add_message(msg2)
        session.add_message(msg3)

        messages = session.get_messages()
        assert len(messages) == 3
        assert messages[0].role == "system"
        assert messages[1].role == "user"
        assert messages[2].role == "assistant"

    def test_chat_session_clear_history(self):
        """测试清空会话历史"""
        session = ChatSession(
            session_id="test_conv_123"
        )

        # 添加消息
        system_msg = Message(role="system", content="System", name="system")
        user_msg = Message(role="user", content="Hello", name="user")
        session.add_message(system_msg)
        session.add_message(user_msg)

        assert len(session.messages) == 2

        # 清空历史，保留系统消息
        session.clear_history(keep_system=True)
        assert len(session.messages) == 1
        assert session.messages[0].role == "system"


class TestChatService:
    """聊天服务测试"""

    @pytest.fixture
    def mock_deepseek_client(self):
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
    def chat_service(self, mock_deepseek_client):
        """聊天服务实例"""
        return ChatService(mock_deepseek_client)

    def test_chat_service_creation(self, mock_deepseek_client):
        """测试聊天服务创建"""
        service = ChatService(mock_deepseek_client)
        assert service.client == mock_deepseek_client
        assert service.sessions == {}

    def test_create_session(self, chat_service):
        """测试创建会话"""
        session = chat_service.create_session(
            session_id="test_conv_123"
        )

        assert isinstance(session, ChatSession)
        assert session.session_id == "test_conv_123"
        assert "test_conv_123" in chat_service.sessions

    def test_get_session_existing(self, chat_service):
        """测试获取存在的会话"""
        # 先创建会话
        created_session = chat_service.create_session(
            session_id="test_conv_123"
        )

        # 获取会话
        retrieved_session = chat_service.get_session("test_conv_123")
        assert retrieved_session == created_session

    def test_get_session_nonexistent(self, chat_service):
        """测试获取不存在的会话"""
        session = chat_service.get_session("nonexistent")
        assert session is None

    def test_delete_session_existing(self, chat_service):
        """测试删除存在的会话"""
        # 先创建会话
        chat_service.create_session(
            session_id="test_conv_123"
        )

        # 删除会话
        result = chat_service.delete_session("test_conv_123")
        assert result is True
        assert "test_conv_123" not in chat_service.sessions

    def test_delete_session_nonexistent(self, chat_service):
        """测试删除不存在的会话"""
        result = chat_service.delete_session("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_chat_with_new_session(self, chat_service, mock_deepseek_client):
        """测试与新会话聊天"""
        # 模拟API响应
        mock_response = Mock(spec=ChatCompletionResponse)
        mock_response.choices = [
            Mock(message=Mock(content="Hello! How can I help you?"))
        ]
        mock_deepseek_client.chat_completion.return_value = mock_response

        response = await chat_service.chat(
            message="Hello",
            session_id="new_conv_123",
            system_prompt="You are a helpful assistant"
        )

        assert response == "Hello! How can I help you?"
        assert "new_conv_123" in chat_service.sessions

        # 验证API调用
        mock_deepseek_client.chat_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_existing_session(self, chat_service, mock_deepseek_client):
        """测试与现有会话聊天"""
        # 先创建会话
        session = chat_service.create_session(
            session_id="existing_conv_123"
        )

        # 添加历史消息
        system_msg = Message(role="system", content="You are a helpful assistant", name="system")
        user_msg = Message(role="user", content="Hello", name="user")
        assistant_msg = Message(role="assistant", content="Hi there!", name="assistant")
        session.add_message(system_msg)
        session.add_message(user_msg)
        session.add_message(assistant_msg)

        # 模拟API响应
        mock_response = Mock(spec=ChatCompletionResponse)
        mock_response.choices = [
            Mock(message=Mock(content="How can I assist you today?"))
        ]
        mock_deepseek_client.chat_completion.return_value = mock_response

        response = await chat_service.chat(
            message="What can you do?",
            session_id="existing_conv_123"
        )

        assert response == "How can I assist you today?"

        # 验证消息历史被保持
        messages = session.get_messages()
        assert len(messages) >= 4  # 系统消息 + 之前的对话 + 新消息

    @pytest.mark.asyncio
    async def test_chat_stream(self, chat_service, mock_deepseek_client):
        """测试流式聊天"""
        # 模拟流式响应
        async def mock_stream():
            yield "Hello"
            yield " there"
            yield "!"

        mock_deepseek_client.chat_completion_stream.return_value = mock_stream()

        # 收集流式响应
        response_chunks = []
        async for chunk in chat_service.chat_stream(
            message="Hello",
            session_id="stream_conv_123",
            system_prompt="You are a helpful assistant"
        ):
            response_chunks.append(chunk)

        assert response_chunks == ["Hello", " there", "!"]
        assert "stream_conv_123" in chat_service.sessions

    @pytest.mark.asyncio
    async def test_chat_api_error(self, chat_service, mock_deepseek_client):
        """测试API错误处理"""
        # 模拟API错误
        mock_deepseek_client.chat_completion.side_effect = Exception("API Error")

        with pytest.raises(ServiceError, match="聊天失败"):
            await chat_service.chat(
                message="Hello",
                session_id="error_conv_123"
            )

    @pytest.mark.asyncio
    async def test_chat_empty_message(self, chat_service):
        """测试空消息处理"""
        with pytest.raises(ValidationError, match="消息不能为空"):
            await chat_service.chat(
                message="",
                session_id="test_conv_123"
            )

    @pytest.mark.asyncio
    async def test_chat_none_message(self, chat_service):
        """测试None消息处理"""
        with pytest.raises(ValidationError, match="消息不能为空"):
            await chat_service.chat(
                message=None,
                session_id="test_conv_123"
            )

    def test_list_sessions(self, chat_service):
        """测试列出所有会话"""
        # 创建多个会话
        chat_service.create_session("conv_1")
        chat_service.create_session("conv_2")
        chat_service.create_session("conv_3")

        sessions = chat_service.list_sessions()
        session_ids = [session.session_id for session in sessions]

        assert "conv_1" in session_ids
        assert "conv_2" in session_ids
        assert "conv_3" in session_ids
        assert len(sessions) == 3

    def test_clear_all_sessions(self, chat_service):
        """测试清空所有会话"""
        # 创建多个会话
        chat_service.create_session("conv_1")
        chat_service.create_session("conv_2")

        assert len(chat_service.sessions) == 2

        chat_service.clear_all_sessions()

        assert len(chat_service.sessions) == 0

    @pytest.mark.asyncio
    async def test_chat_with_temperature(self, chat_service, mock_deepseek_client):
        """测试带温度参数的聊天"""
        # 模拟API响应
        mock_response = Mock(spec=ChatCompletionResponse)
        mock_response.choices = [
            Mock(message=Mock(content="Response with temperature"))
        ]
        mock_deepseek_client.chat_completion.return_value = mock_response

        response = await chat_service.chat(
            message="Hello",
            session_id="temp_conv_123",
            temperature=0.8
        )

        assert response == "Response with temperature"

        # 验证温度参数被传递
        call_args = mock_deepseek_client.chat_completion.call_args
        assert call_args[1].get('temperature') == 0.8