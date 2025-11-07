"""
自定义异常类

定义了应用中使用的各种自定义异常类型。
"""

from typing import Optional, Any, Dict


class AIAssistantError(Exception):
    """AI助手基础异常类"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ConfigError(AIAssistantError):
    """配置相关异常"""
    pass


class APIError(AIAssistantError):
    """API调用相关异常"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        super().__init__(message, **kwargs)
        self.status_code = status_code
        self.response_data = response_data or {}


class ValidationError(AIAssistantError):
    """输入验证异常"""
    pass


class ServiceError(AIAssistantError):
    """服务层异常"""
    pass


class AuthenticationError(APIError):
    """认证异常"""
    def __init__(self, message: str = "Authentication failed", **kwargs) -> None:
        super().__init__(message, status_code=401, **kwargs)


class RateLimitError(APIError):
    """速率限制异常"""
    def __init__(self, message: str = "Rate limit exceeded", **kwargs) -> None:
        super().__init__(message, status_code=429, **kwargs)


class NotFoundError(APIError):
    """资源未找到异常"""
    def __init__(self, message: str = "Resource not found", **kwargs) -> None:
        super().__init__(message, status_code=404, **kwargs)


class ServerError(APIError):
    """服务器错误异常"""
    def __init__(self, message: str = "Internal server error", **kwargs) -> None:
        super().__init__(message, status_code=500, **kwargs)


class TimeoutError(AIAssistantError):
    """超时异常"""
    pass


class NetworkError(AIAssistantError):
    """网络连接异常"""
    pass


class ContentFilterError(APIError):
    """内容过滤异常"""
    def __init__(self, message: str = "Content filtered", **kwargs) -> None:
        super().__init__(message, status_code=400, **kwargs)


class QuotaExceededError(APIError):
    """配额超限异常"""
    def __init__(self, message: str = "API quota exceeded", **kwargs) -> None:
        super().__init__(message, status_code=429, **kwargs)