"""
工具助手函数单元测试
"""

import pytest
import time
import uuid
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from ai_assistant.utils.helpers import (
    truncate_text, format_error_message, safe_get, chunks,
    retry_async, ensure_directory, clean_text, mask_sensitive_info,
    get_env_bool, get_env_int, get_env_float, format_file_size, generate_request_id
)


class TestTruncateText:
    """文本截断测试"""

    def test_truncate_short_text(self):
        """测试短文本截断"""
        text = "Short text"
        result = truncate_text(text, 20)
        assert result == "Short text"

    def test_truncate_long_text(self):
        """测试长文本截断"""
        text = "This is a very long text that should be truncated"
        result = truncate_text(text, 20)
        assert len(result) <= 23  # 20 + "..."
        assert result.endswith("...")

    def test_truncate_exact_length(self):
        """测试精确长度截断"""
        text = "Exactly twenty chars!"
        result = truncate_text(text, 20)
        assert len(result) <= 23

    def test_truncate_with_suffix(self):
        """测试自定义后缀截断"""
        text = "This is a long text"
        result = truncate_text(text, 10, suffix="[...]")
        assert result.endswith("[...]")
        assert len(result) <= 14  # 10 + len("[...]")

    def test_truncate_empty_text(self):
        """测试空文本截断"""
        result = truncate_text("", 10)
        assert result == ""


class TestFormatErrorMessage:
    """错误消息格式化测试"""

    def test_format_error_message_basic(self):
        """测试基础错误消息格式化"""
        error = ValueError("Test error")
        result = format_error_message(error)
        assert "Test error" in result
        assert "ValueError" in result

    def test_format_error_message_with_traceback(self):
        """测试带追踪信息的错误消息格式化"""
        error = ValueError("Test error")
        result = format_error_message(error, include_traceback=True)
        assert "Test error" in result
        assert "ValueError" in result

    def test_format_error_message_none(self):
        """测试None错误"""
        result = format_error_message(None)
        assert result == "未知错误"


class TestSafeGet:
    """安全获取字典值测试"""

    def test_safe_get_existing_key(self):
        """测试获取存在的键"""
        data = {"key": "value"}
        result = safe_get(data, "key")
        assert result == "value"

    def test_safe_get_nonexistent_key(self):
        """测试获取不存在的键"""
        data = {"key": "value"}
        result = safe_get(data, "nonexistent")
        assert result is None

    def test_safe_get_with_default(self):
        """测试带默认值的获取"""
        data = {"key": "value"}
        result = safe_get(data, "nonexistent", "default")
        assert result == "default"

    def test_safe_get_nested_dict(self):
        """测试嵌套字典获取"""
        data = {"nested": {"key": "value"}}
        result = safe_get(data, "nested.key")
        assert result is None  # 当前实现不支持嵌套路径


class TestChunks:
    """分块函数测试"""

    def test_chunks_basic(self):
        """测试基础分块"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = list(chunks(data, 3))
        assert result == [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10]]

    def test_chunks_exact_division(self):
        """测试整除分块"""
        data = [1, 2, 3, 4, 5, 6]
        result = list(chunks(data, 2))
        assert result == [[1, 2], [3, 4], [5, 6]]

    def test_chunks_empty_list(self):
        """测试空列表分块"""
        result = list(chunks([], 3))
        assert result == []

    def test_chunks_single_element(self):
        """测试单元素分块"""
        result = list(chunks([1], 5))
        assert result == [[1]]

    def test_chunks_string_data(self):
        """测试字符串分块"""
        text = "abcdefghij"
        result = list(chunks(text, 3))
        assert result == ["abc", "def", "ghi", "j"]


class TestRetryAsync:
    """异步重试装饰器测试"""

    @pytest.mark.asyncio
    async def test_retry_async_success(self):
        """测试异步重试成功"""
        call_count = 0

        @retry_async(max_attempts=3, delay=0.01)
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Fail once")
            return "success"

        result = await failing_function()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_async_failure(self):
        """测试异步重试失败"""
        @retry_async(max_attempts=2, delay=0.01)
        async def always_failing_function():
            raise ValueError("Always fail")

        with pytest.raises(ValueError, match="Always fail"):
            await always_failing_function()


class TestEnsureDirectory:
    """确保目录存在测试"""

    def test_ensure_directory_new(self):
        """测试创建新目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = Path(temp_dir) / "new_directory"
            result = ensure_directory(new_dir)
            assert result.exists()
            assert result.is_dir()

    def test_ensure_directory_existing(self):
        """测试已存在的目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            existing_dir = Path(temp_dir)
            result = ensure_directory(existing_dir)
            assert result.exists()
            assert result.is_dir()

    def test_ensure_directory_nested(self):
        """测试嵌套目录创建"""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_dir = Path(temp_dir) / "level1" / "level2"
            result = ensure_directory(nested_dir)
            assert result.exists()
            assert result.is_dir()


class TestCleanText:
    """文本清理测试"""

    def test_clean_basic_text(self):
        """测试基础文本清理"""
        dirty_text = "  Hello   world!  \n\n  This is   a test.  "
        clean = clean_text(dirty_text)
        assert "Hello" in clean
        assert "world" in clean
        assert "test" in clean

    def test_clean_empty_text(self):
        """测试清理空文本"""
        assert clean_text("") == ""
        assert clean_text("   ") == ""
        assert clean_text("\n\n") == ""

    def test_clean_text_with_multiple_newlines(self):
        """测试清理多个换行符"""
        text_with_newlines = "Line 1\n\n\nLine 2\n\nLine 3"
        clean = clean_text(text_with_newlines)
        assert "Line 1" in clean
        assert "Line 2" in clean
        assert "Line 3" in clean


class TestMaskSensitiveInfo:
    """敏感信息掩码测试"""

    def test_mask_api_key(self):
        """测试API密钥掩码"""
        api_key = "sk-1234567890abcdef"
        result = mask_sensitive_info(api_key)
        assert "sk-" in result
        assert "*" in result
        assert "1234567890abcdef" not in result

    def test_mask_email(self):
        """测试邮箱掩码"""
        email = "user@example.com"
        result = mask_sensitive_info(email)
        assert "@" in result
        assert "*" in result

    def test_mask_short_text(self):
        """测试短文本掩码"""
        short = "abc"
        result = mask_sensitive_info(short)
        assert len(result) <= len(short)

    def test_mask_custom_char(self):
        """测试自定义掩码字符"""
        text = "sensitive"
        result = mask_sensitive_info(text, mask_char="#")
        assert "#" in result
        assert "sensitive" not in result


class TestEnvFunctions:
    """环境变量函数测试"""

    def test_get_env_bool_existing(self):
        """测试获取存在的布尔环境变量"""
        os.environ["TEST_BOOL"] = "true"
        result = get_env_bool("TEST_BOOL")
        assert result is True
        del os.environ["TEST_BOOL"]

    def test_get_env_bool_nonexistent(self):
        """测试获取不存在的布尔环境变量"""
        result = get_env_bool("NONEXISTENT_BOOL", False)
        assert result is False

    def test_get_env_int_existing(self):
        """测试获取存在的整数环境变量"""
        os.environ["TEST_INT"] = "42"
        result = get_env_int("TEST_INT")
        assert result == 42
        del os.environ["TEST_INT"]

    def test_get_env_int_nonexistent(self):
        """测试获取不存在的整数环境变量"""
        result = get_env_int("NONEXISTENT_INT", 0)
        assert result == 0

    def test_get_env_float_existing(self):
        """测试获取存在的浮点数环境变量"""
        os.environ["TEST_FLOAT"] = "3.14"
        result = get_env_float("TEST_FLOAT")
        assert result == 3.14
        del os.environ["TEST_FLOAT"]

    def test_get_env_float_nonexistent(self):
        """测试获取不存在的浮点数环境变量"""
        result = get_env_float("NONEXISTENT_FLOAT", 0.0)
        assert result == 0.0


class TestFormatFileSize:
    """文件大小格式化测试"""

    def test_format_file_size_bytes(self):
        """测试字节格式化"""
        assert format_file_size(100) == "100.0 B"
        assert format_file_size(999) == "999.0 B"

    def test_format_file_size_kilobytes(self):
        """测试千字节格式化"""
        assert format_file_size(1000) == "1.0 KB"
        assert format_file_size(1500) == "1.5 KB"

    def test_format_file_size_megabytes(self):
        """测试兆字节格式化"""
        assert format_file_size(1000 * 1000) == "1.0 MB"
        assert format_file_size(2.5 * 1000 * 1000) == "2.5 MB"

    def test_format_file_size_zero(self):
        """测试零大小格式化"""
        assert format_file_size(0) == "0.0 B"


class TestGenerateRequestId:
    """请求ID生成测试"""

    def test_generate_request_id(self):
        """测试生成请求ID"""
        request_id = generate_request_id()
        assert isinstance(request_id, str)
        assert len(request_id) > 0

    def test_generate_request_id_unique(self):
        """测试请求ID唯一性"""
        ids = [generate_request_id() for _ in range(10)]
        unique_ids = set(ids)
        assert len(unique_ids) == 10  # 所有ID都应该不同