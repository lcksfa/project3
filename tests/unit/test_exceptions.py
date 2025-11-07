"""
异常模块单元测试
"""

import pytest

from ai_assistant.core.exceptions import (
    AIAssistantError, ConfigError, APIError, ValidationError,
    AuthenticationError, RateLimitError, NotFoundError,
    ServerError, ContentFilterError, QuotaExceededError
)


class TestAIAssistantError:
    """基础异常类测试"""

    def test_basic_exception(self):
        """测试基础异常"""
        error = AIAssistantError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.error_code is None
        assert error.details == {}

    def test_exception_with_error_code(self):
        """测试带错误码的异常"""
        error = AIAssistantError(
            message="Test error with code",
            error_code="TEST_001"
        )
        assert str(error) == "[TEST_001] Test error with code"
        assert error.error_code == "TEST_001"

    def test_exception_with_details(self):
        """测试带详细信息的异常"""
        details = {"field": "value", "number": 123}
        error = AIAssistantError(
            message="Test error with details",
            details=details
        )
        assert error.details == details


class TestConfigError:
    """配置异常测试"""

    def test_config_error(self):
        """测试配置异常"""
        error = ConfigError("Configuration failed")
        assert isinstance(error, AIAssistantError)
        assert str(error) == "Configuration failed"


class TestAPIError:
    """API异常测试"""

    def test_basic_api_error(self):
        """测试基础API异常"""
        error = APIError("API call failed")
        assert isinstance(error, AIAssistantError)
        assert str(error) == "API call failed"
        assert error.status_code is None
        assert error.response_data == {}

    def test_api_error_with_status_code(self):
        """测试带状态码的API异常"""
        error = APIError(
            message="Not found",
            status_code=404
        )
        assert error.status_code == 404
        assert str(error) == "Not found"

    def test_api_error_with_response_data(self):
        """测试带响应数据的API异常"""
        response_data = {"error": {"message": "Detailed error"}}
        error = APIError(
            message="API error with data",
            response_data=response_data
        )
        assert error.response_data == response_data


class TestSpecificAPIErrors:
    """特定API异常测试"""

    def test_authentication_error(self):
        """测试认证异常"""
        error = AuthenticationError("Invalid API key")
        assert isinstance(error, APIError)
        assert error.status_code == 401
        assert str(error) == "Invalid API key"

    def test_rate_limit_error(self):
        """测试速率限制异常"""
        error = RateLimitError("Too many requests")
        assert isinstance(error, APIError)
        assert error.status_code == 429
        assert str(error) == "Too many requests"

    def test_not_found_error(self):
        """测试未找到异常"""
        error = NotFoundError("Resource not found")
        assert isinstance(error, APIError)
        assert error.status_code == 404
        assert str(error) == "Resource not found"

    def test_server_error(self):
        """测试服务器错误异常"""
        error = ServerError("Internal server error")
        assert isinstance(error, APIError)
        assert error.status_code == 500
        assert str(error) == "Internal server error"

    def test_content_filter_error(self):
        """测试内容过滤异常"""
        error = ContentFilterError("Content filtered")
        assert isinstance(error, APIError)
        assert error.status_code == 400
        assert str(error) == "Content filtered"

    def test_quota_exceeded_error(self):
        """测试配额超限异常"""
        error = QuotaExceededError("API quota exceeded")
        assert isinstance(error, APIError)
        assert error.status_code == 429
        assert str(error) == "API quota exceeded"


class TestValidationError:
    """验证异常测试"""

    def test_validation_error(self):
        """测试验证异常"""
        error = ValidationError("Invalid input")
        assert isinstance(error, AIAssistantError)
        assert str(error) == "Invalid input"


class TestExceptionChaining:
    """异常链测试"""

    def test_exception_chaining(self):
        """测试异常链"""
        try:
            raise ValueError("Original error")
        except ValueError as e:
            error = APIError("Wrapped error", error_code="WRAP_001")
            assert isinstance(error, AIAssistantError)
            assert error.error_code == "WRAP_001"