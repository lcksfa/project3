"""
聊天服务集成测试
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from ai_assistant.services.chat_service import ChatService, ChatSession
from ai_assistant.services.deepseek_client import DeepSeekClient, Message
from ai_assistant.core.exceptions import ServiceError


@pytest.mark.integration
class TestChatServiceIntegration:
    """聊天服务集成测试"""

    @pytest.fixture
    def mock_client(self):
        """模拟客户端"""
        client = Mock(spec=DeepSeekClient)
        client.chat_completion = AsyncMock()
        client.chat_completion_stream = AsyncMock()
        client.create_user_message = Mock()
        client.create_assistant_message = Mock()
        client.create_system_message = Mock()
        return client

    @pytest.fixture
    def chat_service(self, mock_client):
        """聊天服务实例"""
        return ChatService(mock_client)

    @pytest.mark.asyncio
    async def test_complete_chat_flow(self, chat_service, mock_client):
        """测试完整的聊天流程"""
        # 模拟API响应
        mock_response = Mock()
        mock_response.choices = [
            {"message": {"content": "Hello! How can I help you today?"}}
        ]
        mock_client.chat_completion.return_value = mock_response

        # 模拟消息创建
        mock_client.create_user_message.return_value = Message(role="user", content="Hello")
        mock_client.create_assistant_message.return_value = Message(role="assistant", content="Hello! How can I help you today?")

        # 执行聊天
        result = await chat_service.chat("Hello", session_id="test_session")

        # 验证结果
        assert result == "Hello! How can I help you today?"

        # 验证API调用
        mock_client.chat_completion.assert_called_once()

        # 验证会话状态
        session = chat_service.get_or_create_session("test_session")
        assert len(session.messages) >= 2  # 至少包含用户消息和助手回复

    @pytest.mark.asyncio
    async def test_stream_chat_flow(self, chat_service, mock_client):
        """测试流式聊天流程"""
        # 模拟流式响应
        async def mock_stream():
            yield "Hello"
            yield "!"
            yield " How"
            yield " can"
            yield " I"
            yield " help"
            yield " you"
            yield "?"

        mock_client.chat_completion_stream.return_value = mock_stream()
        mock_client.create_user_message.return_value = Message(role="user", content="Hello")
        mock_client.create_assistant_message.return_value = Message(role="assistant", content="Hello! How can I help you?")

        # 执行流式聊天
        response_parts = []
        async for part in chat_service.chat_stream("Hello", session_id="test_stream"):
            response_parts.append(part)

        # 验证结果
        assert "".join(response_parts) == "Hello! How can I help you?"

        # 验证会话状态
        session = chat_service.get_or_create_session("test_stream")
        assistant_messages = [msg for msg in session.messages if msg.role == "assistant"]
        assert len(assistant_messages) > 0
        assert assistant_messages[0].content == "Hello! How can I help you?"

    def test_session_management(self, chat_service):
        """测试会话管理"""
        # 创建会话
        session1 = chat_service.get_or_create_session("session1")
        session2 = chat_service.get_or_create_session("session2")

        # 验证会话独立性
        assert session1.session_id != session2.session_id
        assert session1 is not session2

        # 验证会话复用
        session1_again = chat_service.get_or_create_session("session1")
        assert session1 is session1_again

    def test_session_history(self, chat_service):
        """测试会话历史"""
        session_id = "history_test"

        # 添加消息到会话
        session = chat_service.get_or_create_session(session_id)
        session.add_message(Message(role="user", content="Hello"))
        session.add_message(Message(role="assistant", content="Hi there!"))

        # 获取历史记录
        history = chat_service.get_session_history(session_id)
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "Hi there!"

    def test_clear_session_history(self, chat_service):
        """测试清除会话历史"""
        session_id = "clear_test"

        # 创建带消息的会话
        session = chat_service.get_or_create_session(session_id)
        session.add_message(Message(role="user", content="Hello"))
        session.add_message(Message(role="assistant", content="Hi there!"))

        # 清除历史
        chat_service.clear_session_history(session_id)

        # 验证历史已清除
        history = chat_service.get_session_history(session_id)
        assert len(history) == 0

    def test_delete_session(self, chat_service):
        """测试删除会话"""
        session_id = "delete_test"

        # 创建会话
        chat_service.get_or_create_session(session_id)
        assert session_id in chat_service.sessions

        # 删除会话
        chat_service.delete_session(session_id)
        assert session_id not in chat_service.sessions

    def test_session_info(self, chat_service):
        """测试会话信息"""
        session_id = "info_test"

        # 创建会话
        session = chat_service.get_or_create_session(session_id)
        session.add_message(Message(role="user", content="Hello"))

        # 获取会话信息
        info = chat_service.get_session_info(session_id)
        assert info is not None
        assert info["session_id"] == session_id
        assert info["message_count"] == 1
        assert "created_at" in info
        assert "updated_at" in info

    def test_list_sessions(self, chat_service):
        """测试列出会话"""
        # 创建多个会话
        session_ids = ["session1", "session2", "session3"]
        for session_id in session_ids:
            chat_service.get_or_create_session(session_id)

        # 列出会话
        sessions = chat_service.list_sessions()
        assert len(sessions) >= 3
        for session_id in session_ids:
            assert session_id in sessions

    def test_set_system_message(self, chat_service):
        """测试设置系统消息"""
        session_id = "system_test"
        system_message = "You are a helpful assistant specialized in technology."

        # 设置系统消息
        chat_service.set_system_message(session_id, system_message)

        # 验证系统消息
        session = chat_service.get_or_create_session(session_id)
        system_messages = [msg for msg in session.messages if msg.role == "system"]
        assert len(system_messages) == 1
        assert system_messages[0].content == system_message

    @pytest.mark.asyncio
    async def test_chat_error_handling(self, chat_service, mock_client):
        """测试聊天错误处理"""
        # 模拟API错误
        mock_client.chat_completion.side_effect = Exception("API Error")
        mock_client.create_user_message.return_value = Message(role="user", content="Hello")

        # 执行聊天应该抛出异常
        with pytest.raises(ServiceError):
            await chat_service.chat("Hello", session_id="error_test")

        # 验证失败的用户消息被移除
        session = chat_service.get_or_create_session("error_test")
        user_messages = [msg for msg in session.messages if msg.role == "user"]
        # 应该没有用户消息，因为失败了
        assert len(user_messages) == 0

    @pytest.mark.asyncio
    async def test_chat_with_parameters(self, chat_service, mock_client):
        """测试带参数的聊天"""
        # 模拟API响应
        mock_response = Mock()
        mock_response.choices = [
            {"message": {"content": "Custom response"}}
        ]
        mock_client.chat_completion.return_value = mock_response
        mock_client.create_user_message.return_value = Message(role="user", content="Test")
        mock_client.create_assistant_message.return_value = Message(role="assistant", content="Custom response")

        # 使用自定义参数执行聊天
        result = await chat_service.chat(
            "Test",
            session_id="param_test",
            temperature=0.9,
            max_tokens=1500,
            stream=False
        )

        # 验证结果
        assert result == "Custom response"

        # 验证API调用参数
        mock_client.chat_completion.assert_called_once()
        call_args = mock_client.chat_completion.call_args
        request = call_args[0][0]
        assert request.temperature == 0.9
        assert request.max_tokens == 1500
        assert request.stream is False


@pytest.mark.integration
class TestChatSessionIntegration:
    """聊天会话集成测试"""

    def test_session_message_management(self):
        """测试会话消息管理"""
        session = ChatSession("test_session", max_history=3)

        # 添加消息
        user_msg = Message(role="user", content="Hello")
        assistant_msg = Message(role="assistant", content="Hi there!")

        session.add_message(user_msg)
        session.add_message(assistant_msg)

        # 验证消息
        messages = session.get_messages()
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"

    def test_session_history_limit(self):
        """测试会话历史限制"""
        session = ChatSession("test_session", max_history=2)

        # 设置系统消息
        system_msg = Message(role="system", content="System prompt")
        session.add_message(system_msg)

        # 添加超过限制的消息
        for i in range(5):
            msg = Message(role="user", content=f"Message {i}")
            session.add_message(msg)

        # 验证历史限制
        messages = session.get_messages()
        assert len(messages) <= 3  # 系统消息 + 2个最新消息
        assert messages[0].role == "system"  # 系统消息应该保留
        assert messages[-1].content == "Message 4"  # 最后一条消息

    def test_clear_history_with_system(self):
        """测试清除历史但保留系统消息"""
        session = ChatSession("test_session")

        # 添加各种消息
        system_msg = Message(role="system", content="System")
        user_msg = Message(role="user", content="Hello")
        assistant_msg = Message(role="assistant", content="Hi")

        session.add_message(system_msg)
        session.add_message(user_msg)
        session.add_message(assistant_msg)

        # 清除历史但保留系统消息
        session.clear_history(keep_system=True)

        messages = session.get_messages()
        assert len(messages) == 1
        assert messages[0].role == "system"

    def test_clear_all_history(self):
        """测试清除所有历史"""
        session = ChatSession("test_session")

        # 添加消息
        session.add_message(Message(role="system", content="System"))
        session.add_message(Message(role="user", content="Hello"))

        # 清除所有历史
        session.clear_history(keep_system=False)

        messages = session.get_messages()
        assert len(messages) == 0

    def test_set_system_message(self):
        """测试设置系统消息"""
        session = ChatSession("test_session")

        # 设置系统消息
        session.set_system_message("You are a helpful assistant")

        messages = session.get_messages()
        assert len(messages) == 1
        assert messages[0].role == "system"
        assert messages[0].content == "You are a helpful assistant"

        # 更新系统消息
        session.set_system_message("You are a specialized assistant")

        messages = session.get_messages()
        assert len(messages) == 1
        assert messages[0].content == "You are a specialized assistant"