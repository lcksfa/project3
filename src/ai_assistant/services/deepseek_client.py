"""
DeepSeek API 客户端

封装与 DeepSeek API 的交互逻辑。
"""

import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
import httpx
from pydantic import BaseModel, Field

from ..core.config_simple import get_settings
from ..core.config_adapter import DeepSeekConfig as DeepSeekSettings
from ..core.logger import get_logger
from ..core.exceptions import (
    APIError, AuthenticationError, RateLimitError,
    ServerError, TimeoutError, NetworkError,
    ContentFilterError, QuotaExceededError
)
from ..utils.helpers import retry_async, generate_request_id, Timer


class Message(BaseModel):
    """聊天消息模型"""
    role: str = Field(..., description="消息角色：system/user/assistant")
    content: str = Field(..., description="消息内容")
    name: Optional[str] = Field(None, description="消息发送者名称")


class ChatCompletionRequest(BaseModel):
    """聊天完成请求模型"""
    model: str = Field(..., description="模型名称")
    messages: List[Message] = Field(..., description="消息列表")
    temperature: Optional[float] = Field(0.7, description="温度参数")
    max_tokens: Optional[int] = Field(None, description="最大token数")
    stream: bool = Field(False, description="是否流式输出")
    top_p: Optional[float] = Field(1.0, description="核采样参数")
    frequency_penalty: Optional[float] = Field(0.0, description="频率惩罚")
    presence_penalty: Optional[float] = Field(0.0, description="存在惩罚")
    stop: Optional[List[str]] = Field(None, description="停止词")


class UsageDetails(BaseModel):
    """使用统计详情模型"""
    cached_tokens: Optional[int] = Field(None, description="缓存token数")


class Usage(BaseModel):
    """使用统计模型"""
    prompt_tokens: int = Field(..., description="提示token数")
    completion_tokens: int = Field(..., description="完成token数")
    total_tokens: int = Field(..., description="总token数")
    prompt_tokens_details: Optional[UsageDetails] = Field(None, description="提示token详情")
    completion_tokens_details: Optional[UsageDetails] = Field(None, description="完成token详情")


class ChatCompletionResponse(BaseModel):
    """聊天完成响应模型"""
    id: str = Field(..., description="响应ID")
    object: str = Field(..., description="对象类型")
    created: int = Field(..., description="创建时间")
    model: str = Field(..., description="模型名称")
    choices: List[Dict[str, Any]] = Field(..., description="选择列表")
    usage: Optional[Usage] = Field(None, description="使用统计")


class DeepSeekClient:
    """DeepSeek API 客户端"""

    def __init__(self, config: Optional[DeepSeekSettings] = None):
        self.config = config or get_settings().deepseek
        self.logger = get_logger("deepseek_client")
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    async def _ensure_client(self) -> None:
        """确保HTTP客户端已初始化"""
        if self._client is None:
            timeout = httpx.Timeout(self.config.timeout)
            limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)

            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=timeout,
                limits=limits,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "AI-Assistant/1.0.0"
                }
            )

    async def close(self) -> None:
        """关闭HTTP客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None

    @retry_async(max_attempts=3, delay=1.0)
    async def chat_completion(
        self,
        request: ChatCompletionRequest,
        request_id: Optional[str] = None
    ) -> ChatCompletionResponse:
        """
        发送聊天完成请求

        Args:
            request: 聊天完成请求
            request_id: 请求ID

        Returns:
            聊天完成响应

        Raises:
            APIError: API调用失败
        """
        request_id = request_id or generate_request_id()

        with Timer(f"DeepSeek API请求 {request_id}") as timer:
            await self._ensure_client()

            self.logger.info(
                "发送聊天完成请求",
                request_id=request_id,
                model=request.model,
                message_count=len(request.messages),
                stream=request.stream
            )

            try:
                # 构建请求数据
                data = request.dict(exclude_none=True)
                data["messages"] = [msg.dict() for msg in request.messages]

                response = await self._client.post(
                    "/v1/chat/completions",
                    json=data
                )

                self.logger.info(
                    "收到API响应",
                    request_id=request_id,
                    status_code=response.status_code,
                    response_time=timer.elapsed
                )

                # 处理响应
                await self._handle_response(response, request_id)

                response_data = response.json()
                return ChatCompletionResponse(**response_data)

            except httpx.TimeoutException as e:
                self.logger.error(
                    "请求超时",
                    request_id=request_id,
                    timeout=self.config.timeout
                )
                raise TimeoutError(f"请求超时: {self.config.timeout}秒")

            except httpx.NetworkError as e:
                self.logger.error(
                    "网络错误",
                    request_id=request_id,
                    error=str(e)
                )
                raise NetworkError(f"网络连接失败: {e}")

            except httpx.HTTPStatusError as e:
                await self._handle_http_error(e, request_id)

            except Exception as e:
                self.logger.error(
                    "未知错误",
                    request_id=request_id,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise APIError(f"API调用失败: {e}")

    async def chat_completion_stream(
        self,
        request: ChatCompletionRequest,
        request_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式聊天完成请求

        Args:
            request: 聊天完成请求
            request_id: 请求ID

        Yields:
            生成的文本片段

        Raises:
            APIError: API调用失败
        """
        request_id = request_id or generate_request_id()

        await self._ensure_client()
        request.stream = True

        self.logger.info(
            "发送流式聊天完成请求",
            request_id=request_id,
            model=request.model,
            message_count=len(request.messages)
        )

        try:
            # 构建请求数据
            data = request.dict(exclude_none=True)
            data["messages"] = [msg.dict() for msg in request.messages]

            async with self._client.stream(
                "POST",
                "/v1/chat/completions",
                json=data
            ) as response:
                await self._handle_response(response, request_id)

                buffer = ""
                async for line in response.aiter_lines():
                    if line.strip():
                        if line.startswith("data: "):
                            data_str = line[6:]  # 移除 "data: " 前缀

                            if data_str.strip() == "[DONE]":
                                break

                            try:
                                import json
                                data = json.loads(data_str)

                                if "choices" in data and data["choices"]:
                                    delta = data["choices"][0].get("delta", {})
                                    content = delta.get("content", "")

                                    if content:
                                        buffer += content
                                        yield content

                            except json.JSONDecodeError:
                                self.logger.warning(
                                    "无法解析流式响应数据",
                                    request_id=request_id,
                                    data=data_str[:100]  # 只记录前100个字符
                                )
                                continue

                self.logger.info(
                    "流式响应完成",
                    request_id=request_id,
                    total_length=len(buffer)
                )

        except httpx.TimeoutException as e:
            self.logger.error("流式请求超时", request_id=request_id)
            raise TimeoutError(f"流式请求超时: {self.config.timeout}秒")

        except httpx.NetworkError as e:
            self.logger.error("流式网络错误", request_id=request_id, error=str(e))
            raise NetworkError(f"流式网络连接失败: {e}")

        except httpx.HTTPStatusError as e:
            await self._handle_http_error(e, request_id)

        except Exception as e:
            self.logger.error("流式请求未知错误", request_id=request_id, error=str(e))
            raise APIError(f"流式API调用失败: {e}")

    async def _handle_response(self, response: httpx.Response, request_id: str) -> None:
        """处理HTTP响应"""
        if response.status_code >= 400:
            await self._handle_http_error(
                httpx.HTTPStatusError(
                    f"HTTP {response.status_code}",
                    request=response.request,
                    response=response
                ),
                request_id
            )

    async def _handle_http_error(
        self,
        error: httpx.HTTPStatusError,
        request_id: str
    ) -> None:
        """处理HTTP错误"""
        status_code = error.response.status_code
        error_data = {}

        try:
            error_data = error.response.json()
        except:
            error_data = {"message": error.response.text}

        error_message = error_data.get("error", {}).get("message", "未知错误")
        error_code = error_data.get("error", {}).get("code", "unknown")

        self.logger.error(
            "API请求失败",
            request_id=request_id,
            status_code=status_code,
            error_code=error_code,
            error_message=error_message
        )

        # 根据状态码抛出相应的异常
        if status_code == 401:
            raise AuthenticationError(error_message, error_code=error_code)
        elif status_code == 429:
            if "quota" in error_message.lower():
                raise QuotaExceededError(error_message, error_code=error_code)
            else:
                raise RateLimitError(error_message, error_code=error_code)
        elif status_code == 400:
            if "content" in error_message.lower() and "filter" in error_message.lower():
                raise ContentFilterError(error_message, error_code=error_code)
            else:
                raise APIError(error_message, status_code=status_code, error_code=error_code)
        elif status_code in (500, 502, 503, 504):
            raise ServerError(error_message, status_code=status_code, error_code=error_code)
        else:
            raise APIError(
                error_message,
                status_code=status_code,
                error_code=error_code,
                response_data=error_data
            )

    def create_message(
        self,
        role: str,
        content: str,
        name: Optional[str] = None
    ) -> Message:
        """创建消息对象"""
        return Message(role=role, content=content, name=name)

    def create_system_message(self, content: str) -> Message:
        """创建系统消息"""
        return self.create_message("system", content)

    def create_user_message(self, content: str) -> Message:
        """创建用户消息"""
        return self.create_message("user", content)

    def create_assistant_message(self, content: str) -> Message:
        """创建助手消息"""
        return self.create_message("assistant", content)