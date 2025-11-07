"""
聊天服务模块

提供智能对话功能。
"""

from typing import List, Dict, Optional, AsyncGenerator
from datetime import datetime
import asyncio

from .deepseek_client import DeepSeekClient, Message, ChatCompletionRequest
from ..core.config_simple import get_settings
from ..core.logger import get_logger
from ..core.exceptions import ValidationError, ServiceError
from ..utils.validators import validate_text_input, validate_temperature, validate_max_tokens
from ..utils.helpers import truncate_text, Timer, generate_request_id


class ChatSession:
    """聊天会话"""

    def __init__(self, session_id: str, max_history: int = 20):
        self.session_id = session_id
        self.max_history = max_history
        self.messages: List[Message] = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def add_message(self, message: Message) -> None:
        """添加消息到会话"""
        self.messages.append(message)
        self.updated_at = datetime.now()

        # 保持历史记录在限制范围内
        if len(self.messages) > self.max_history:
            # 保留系统消息和最近的消息
            system_messages = [msg for msg in self.messages if msg.role == "system"]
            recent_messages = self.messages[-(self.max_history - len(system_messages)):]
            self.messages = system_messages + recent_messages

    def get_messages(self, include_system: bool = True) -> List[Message]:
        """获取消息列表"""
        if include_system:
            return self.messages.copy()
        return [msg for msg in self.messages if msg.role != "system"]

    def clear_history(self, keep_system: bool = True) -> None:
        """清空历史记录"""
        if keep_system:
            system_messages = [msg for msg in self.messages if msg.role == "system"]
            self.messages = system_messages
        else:
            self.messages = []
        self.updated_at = datetime.now()

    def set_system_message(self, content: str) -> None:
        """设置系统消息"""
        # 移除现有的系统消息
        self.messages = [msg for msg in self.messages if msg.role != "system"]
        # 添加新的系统消息
        if content.strip():
            system_msg = Message(role="system", content=content.strip())
            self.messages.insert(0, system_msg)
        self.updated_at = datetime.now()


class ChatService:
    """聊天服务"""

    def __init__(self, client: Optional[DeepSeekClient] = None):
        self.client = client or DeepSeekClient()
        self.settings = get_settings()
        self.logger = get_logger("chat_service")
        self.sessions: Dict[str, ChatSession] = {}

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    def get_or_create_session(
        self,
        session_id: str,
        system_message: Optional[str] = None
    ) -> ChatSession:
        """获取或创建会话"""
        if session_id not in self.sessions:
            max_history = self.settings.services.max_history_length
            session = ChatSession(session_id, max_history)

            # 设置默认系统消息
            if system_message:
                session.set_system_message(system_message)
            else:
                default_system = (
                    "你是一个有用的AI助手。请用简洁、准确、友好的方式回答用户的问题。"
                    "如果遇到不确定的问题，请诚实地表示。"
                )
                session.set_system_message(default_system)

            self.sessions[session_id] = session
            self.logger.info(
                "创建新聊天会话",
                session_id=session_id,
                max_history=max_history
            )

        return self.sessions[session_id]

    async def chat(
        self,
        message: str,
        session_id: str = "default",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> str:
        """
        发送聊天消息

        Args:
            message: 用户消息
            session_id: 会话ID
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出

        Returns:
            AI回复内容

        Raises:
            ValidationError: 输入验证失败
            ServiceError: 服务处理失败
        """
        # 验证输入
        message = validate_text_input(
            message,
            min_length=1,
            max_length=self.settings.services.max_input_length
        )

        if temperature is not None:
            temperature = validate_temperature(temperature)

        if max_tokens is not None:
            max_tokens = validate_max_tokens(max_tokens)

        request_id = generate_request_id()
        session = self.get_or_create_session(session_id)

        self.logger.info(
            "处理聊天请求",
            request_id=request_id,
            session_id=session_id,
            message_length=len(message),
            stream=stream
        )

        try:
            with Timer(f"聊天处理 {request_id}"):
                # 添加用户消息到会话
                user_msg = self.client.create_user_message(message)
                session.add_message(user_msg)

                # 准备API请求
                request = ChatCompletionRequest(
                    model=self.settings.deepseek.model,
                    messages=session.get_messages(),
                    temperature=temperature or self.settings.services.default_temperature,
                    max_tokens=max_tokens or self.settings.services.max_tokens,
                    stream=stream
                )

                if stream:
                    # 流式处理
                    response_parts = []
                    async for part in self._stream_chat(request, request_id):
                        response_parts.append(part)

                    response = "".join(response_parts)
                else:
                    # 非流式处理
                    response = await self._single_chat(request, request_id)

                # 添加助手回复到会话
                assistant_msg = self.client.create_assistant_message(response)
                session.add_message(assistant_msg)

                self.logger.info(
                    "聊天处理完成",
                    request_id=request_id,
                    session_id=session_id,
                    response_length=len(response)
                )

                return response

        except Exception as e:
            self.logger.error(
                "聊天处理失败",
                request_id=request_id,
                session_id=session_id,
                error=str(e),
                error_type=type(e).__name__
            )
            # 移除失败的用户消息
            if session.messages and session.messages[-1].role == "user":
                session.messages.pop()
            raise ServiceError(f"聊天处理失败: {e}")

    async def _single_chat(self, request: ChatCompletionRequest, request_id: str) -> str:
        """处理单次聊天请求"""
        response = await self.client.chat_completion(request, request_id)

        if not response.choices or not response.choices[0]["message"]:
            raise ServiceError("API返回空响应")

        return response.choices[0]["message"]["content"]

    async def _stream_chat(
        self,
        request: ChatCompletionRequest,
        request_id: str
    ) -> AsyncGenerator[str, None]:
        """处理流式聊天请求"""
        async for part in self.client.chat_completion_stream(request, request_id):
            yield part

    async def chat_stream(
        self,
        message: str,
        session_id: str = "default",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式聊天

        Args:
            message: 用户消息
            session_id: 会话ID
            temperature: 温度参数
            max_tokens: 最大token数

        Yields:
            AI回复的文本片段
        """
        # 验证输入
        message = validate_text_input(
            message,
            min_length=1,
            max_length=self.settings.services.max_input_length
        )

        if temperature is not None:
            temperature = validate_temperature(temperature)

        if max_tokens is not None:
            max_tokens = validate_max_tokens(max_tokens)

        request_id = generate_request_id()
        session = self.get_or_create_session(session_id)

        self.logger.info(
            "开始流式聊天",
            request_id=request_id,
            session_id=session_id,
            message_length=len(message)
        )

        try:
            # 添加用户消息到会话
            user_msg = self.client.create_user_message(message)
            session.add_message(user_msg)

            # 准备API请求
            request = ChatCompletionRequest(
                model=self.settings.deepseek.model,
                messages=session.get_messages(),
                temperature=temperature or self.settings.services.default_temperature,
                max_tokens=max_tokens or self.settings.services.max_tokens,
                stream=True
            )

            # 流式处理并收集完整回复
            response_parts = []
            async for part in self.client.chat_completion_stream(request, request_id):
                response_parts.append(part)
                yield part

            # 添加完整回复到会话
            full_response = "".join(response_parts)
            assistant_msg = self.client.create_assistant_message(full_response)
            session.add_message(assistant_msg)

            self.logger.info(
                "流式聊天完成",
                request_id=request_id,
                session_id=session_id,
                total_response_length=len(full_response)
            )

        except Exception as e:
            self.logger.error(
                "流式聊天失败",
                request_id=request_id,
                session_id=session_id,
                error=str(e)
            )
            # 移除失败的用户消息
            if session.messages and session.messages[-1].role == "user":
                session.messages.pop()
            raise ServiceError(f"流式聊天失败: {e}")

    def get_session_history(
        self,
        session_id: str,
        include_system: bool = False
    ) -> List[Dict[str, str]]:
        """
        获取会话历史

        Args:
            session_id: 会话ID
            include_system: 是否包含系统消息

        Returns:
            消息历史列表
        """
        if session_id not in self.sessions:
            return []

        session = self.sessions[session_id]
        messages = session.get_messages(include_system=include_system)

        return [
            {
                "role": msg.role,
                "content": msg.content,
                "name": msg.name
            }
            for msg in messages
        ]

    def clear_session_history(
        self,
        session_id: str,
        keep_system: bool = True
    ) -> None:
        """
        清空会话历史

        Args:
            session_id: 会话ID
            keep_system: 是否保留系统消息
        """
        if session_id in self.sessions:
            self.sessions[session_id].clear_history(keep_system)
            self.logger.info(
                "清空会话历史",
                session_id=session_id,
                keep_system=keep_system
            )

    def delete_session(self, session_id: str) -> None:
        """
        删除会话

        Args:
            session_id: 会话ID
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.logger.info("删除会话", session_id=session_id)

    def get_session_info(self, session_id: str) -> Optional[Dict[str, any]]:
        """
        获取会话信息

        Args:
            session_id: 会话ID

        Returns:
            会话信息字典
        """
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        return {
            "session_id": session.session_id,
            "message_count": len(session.messages),
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "max_history": session.max_history
        }

    def list_sessions(self) -> List[str]:
        """
        列出所有会话ID

        Returns:
            会话ID列表
        """
        return list(self.sessions.keys())

    def set_system_message(self, session_id: str, content: str) -> None:
        """
        设置系统消息

        Args:
            session_id: 会话ID
            content: 系统消息内容
        """
        content = validate_text_input(content, allow_empty=True)
        session = self.get_or_create_session(session_id)
        session.set_system_message(content)

        self.logger.info(
            "设置系统消息",
            session_id=session_id,
            content_length=len(content)
        )