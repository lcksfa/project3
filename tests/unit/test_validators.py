"""
验证器模块单元测试
"""

import pytest

from ai_assistant.utils.validators import (
    validate_text_input, validate_api_key, validate_email, validate_url,
    validate_temperature, validate_max_tokens, validate_language_code,
    validate_positive_integer, validate_file_path
)
from ai_assistant.core.exceptions import ValidationError


class TestValidateTextInput:
    """文本输入验证测试"""

    def test_valid_text_input(self):
        """测试有效文本输入"""
        text = "Hello, world!"
        result = validate_text_input(text)
        assert result == text

    def test_text_with_whitespace(self):
        """测试带空白的文本"""
        text = "  Hello, world!  "
        result = validate_text_input(text)
        assert result == "Hello, world!"

    def test_empty_text_not_allowed(self):
        """测试不允许空文本"""
        with pytest.raises(ValidationError, match="文本不能为空"):
            validate_text_input("")

    def test_empty_text_allowed(self):
        """测试允许空文本"""
        result = validate_text_input("", allow_empty=True)
        assert result == ""

    def test_whitespace_only_not_allowed(self):
        """测试只包含空白字符的文本"""
        with pytest.raises(ValidationError, match="文本不能为空"):
            validate_text_input("   ")

    def test_whitespace_only_allowed(self):
        """测试允许只包含空白字符的文本"""
        result = validate_text_input("   ", allow_empty=True)
        assert result == ""

    def test_text_too_short(self):
        """测试文本过短"""
        with pytest.raises(ValidationError, match="文本长度不能少于"):
            validate_text_input("Hi", min_length=5)

    def test_text_too_long(self):
        """测试文本过长"""
        with pytest.raises(ValidationError, match="文本长度不能超过"):
            validate_text_input("This is a very long text", max_length=10)

    def test_none_input(self):
        """测试None输入"""
        with pytest.raises(ValidationError, match="文本不能为空"):
            validate_text_input(None)

    def test_none_input_allowed(self):
        """测试允许None输入"""
        result = validate_text_input(None, allow_empty=True)
        assert result == ""


class TestValidateAPIKey:
    """API密钥验证测试"""

    def test_valid_api_key(self):
        """测试有效API密钥"""
        api_key = "sk-1234567890abcdef"
        result = validate_api_key(api_key)
        assert result == api_key

    def test_api_key_with_whitespace(self):
        """测试带空白的API密钥"""
        api_key = "  sk-1234567890abcdef  "
        result = validate_api_key(api_key)
        assert result == "sk-1234567890abcdef"

    def test_empty_api_key(self):
        """测试空API密钥"""
        with pytest.raises(ValidationError, match="API密钥不能为空"):
            validate_api_key("")

    def test_whitespace_only_api_key(self):
        """测试只包含空白字符的API密钥"""
        with pytest.raises(ValidationError, match="API密钥不能为空"):
            validate_api_key("   ")

    def test_too_short_api_key(self):
        """测试过短的API密钥"""
        with pytest.raises(ValidationError, match="API密钥长度太短"):
            validate_api_key("short")

    def test_api_key_with_invalid_chars(self):
        """测试包含非法字符的API密钥"""
        with pytest.raises(ValidationError, match="API密钥包含非法字符"):
            validate_api_key("sk-123@456")

    def test_none_api_key(self):
        """测试None API密钥"""
        with pytest.raises(ValidationError, match="API密钥不能为空"):
            validate_api_key(None)


class TestValidateEmail:
    """邮箱验证测试"""

    def test_valid_email(self):
        """测试有效邮箱"""
        email = "test@example.com"
        result = validate_email(email)
        assert result == "test@example.com"

    def test_email_with_uppercase(self):
        """测试大写邮箱"""
        email = "Test@EXAMPLE.COM"
        result = validate_email(email)
        assert result == "test@example.com"

    def test_empty_email(self):
        """测试空邮箱"""
        with pytest.raises(ValidationError, match="邮箱地址不能为空"):
            validate_email("")

    def test_invalid_email_format(self):
        """测试无效邮箱格式"""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test.example.com",
            "test@.com",
            "test@example."
        ]

        for invalid_email in invalid_emails:
            with pytest.raises(ValidationError, match="邮箱地址格式不正确"):
                validate_email(invalid_email)

    def test_email_with_whitespace(self):
        """测试带空白的邮箱"""
        email = "  test@example.com  "
        result = validate_email(email)
        assert result == "test@example.com"


class TestValidateURL:
    """URL验证测试"""

    def test_valid_http_url(self):
        """测试有效HTTP URL"""
        url = "http://example.com"
        result = validate_url(url)
        assert result == url

    def test_valid_https_url(self):
        """测试有效HTTPS URL"""
        url = "https://example.com/path"
        result = validate_url(url)
        assert result == url

    def test_empty_url(self):
        """测试空URL"""
        with pytest.raises(ValidationError, match="URL不能为空"):
            validate_url("")

    def test_invalid_url_format(self):
        """测试无效URL格式"""
        invalid_urls = [
            "example.com",
            "ftp://example.com",
            "http:/example.com",
            "://example.com"
        ]

        for invalid_url in invalid_urls:
            with pytest.raises(ValidationError, match="URL格式不正确"):
                validate_url(invalid_url)

    def test_url_with_whitespace(self):
        """测试带空白的URL"""
        url = "  https://example.com  "
        result = validate_url(url)
        assert result == "https://example.com"


class TestValidateTemperature:
    """温度参数验证测试"""

    def test_valid_temperature(self):
        """测试有效温度"""
        temperatures = [0.0, 0.5, 1.0, 2.0]
        for temp in temperatures:
            result = validate_temperature(temp)
            assert result == temp

    def test_invalid_temperature_too_low(self):
        """测试温度过低"""
        with pytest.raises(ValidationError, match="温度参数必须在0.0到2.0之间"):
            validate_temperature(-0.1)

    def test_invalid_temperature_too_high(self):
        """测试温度过高"""
        with pytest.raises(ValidationError, match="温度参数必须在0.0到2.0之间"):
            validate_temperature(2.1)

    def test_invalid_temperature_type(self):
        """测试无效温度类型"""
        with pytest.raises(ValidationError, match="温度参数必须是数字"):
            validate_temperature("0.5")


class TestValidateMaxTokens:
    """最大token数验证测试"""

    def test_valid_max_tokens(self):
        """测试有效最大token数"""
        tokens = [1, 100, 1000, 10000]
        for token in tokens:
            result = validate_max_tokens(token)
            assert result == token

    def test_invalid_max_tokens_negative(self):
        """测试负数token数"""
        with pytest.raises(ValidationError, match="最大token数必须大于0"):
            validate_max_tokens(-1)

    def test_invalid_max_tokens_zero(self):
        """测试零token数"""
        with pytest.raises(ValidationError, match="最大token数必须大于0"):
            validate_max_tokens(0)

    def test_invalid_max_tokens_type(self):
        """测试无效token数类型"""
        with pytest.raises(ValidationError, match="最大token数必须是整数"):
            validate_max_tokens("100")

    def test_max_tokens_too_large(self):
        """测试token数过大"""
        with pytest.raises(ValidationError, match="最大token数不能超过100000"):
            validate_max_tokens(100001)


class TestValidateLanguageCode:
    """语言代码验证测试"""

    def test_valid_language_code(self):
        """测试有效语言代码"""
        supported_languages = ["中文", "English", "日本語"]
        language = "中文"
        result = validate_language_code(language, supported_languages)
        assert result == language

    def test_empty_language_code(self):
        """测试空语言代码"""
        with pytest.raises(ValidationError, match="语言代码不能为空"):
            validate_language_code("", ["中文", "English"])

    def test_unsupported_language_code(self):
        """测试不支持的语言代码"""
        supported_languages = ["中文", "English"]
        unsupported_language = "Français"

        with pytest.raises(ValidationError, match="不支持的语言"):
            validate_language_code(unsupported_language, supported_languages)

    def test_language_code_with_whitespace(self):
        """测试带空白的语言代码"""
        supported_languages = ["中文", "English"]
        language = "  中文  "
        result = validate_language_code(language, supported_languages)
        assert result == "中文"


class TestValidatePositiveInteger:
    """正整数验证测试"""

    def test_valid_positive_integer(self):
        """测试有效正整数"""
        integers = [1, 10, 100]
        for integer in integers:
            result = validate_positive_integer(integer)
            assert result == integer

    def test_invalid_negative_integer(self):
        """测试负整数"""
        with pytest.raises(ValidationError, match="必须大于0"):
            validate_positive_integer(-1, "测试值")

    def test_invalid_zero(self):
        """测试零"""
        with pytest.raises(ValidationError, match="必须大于0"):
            validate_positive_integer(0, "测试值")

    def test_invalid_type(self):
        """测试无效类型"""
        with pytest.raises(ValidationError, match="必须是整数"):
            validate_positive_integer("10", "测试值")


class TestValidateFilePath:
    """文件路径验证测试"""

    def test_valid_file_path(self):
        """测试有效文件路径"""
        file_path = "/path/to/file.txt"
        result = validate_file_path(file_path)
        assert result == file_path

    def test_empty_file_path(self):
        """测试空文件路径"""
        with pytest.raises(ValidationError, match="文件路径不能为空"):
            validate_file_path("")

    def test_file_path_with_illegal_chars(self):
        """测试包含非法字符的文件路径"""
        illegal_paths = [
            "path<with>illegal.txt",
            "path:with:illegal.txt",
            'path"with"illegal.txt',
            "path|with|illegal.txt",
            "path?with?illegal.txt",
            "path*with*illegal.txt"
        ]

        for illegal_path in illegal_paths:
            with pytest.raises(ValidationError, match="文件路径包含非法字符"):
                validate_file_path(illegal_path)

    def test_file_path_with_whitespace(self):
        """测试带空白的文件路径"""
        file_path = "  /path/to/file.txt  "
        result = validate_file_path(file_path)
        assert result == "/path/to/file.txt"

    def test_existing_file_path(self, create_temp_file):
        """测试存在的文件路径"""
        temp_file = create_temp_file("test content")
        result = validate_file_path(str(temp_file), must_exist=True)
        assert result == str(temp_file)

    def test_nonexistent_file_path(self):
        """测试不存在的文件路径"""
        nonexistent_path = "/path/to/nonexistent/file.txt"
        with pytest.raises(ValidationError, match="文件不存在"):
            validate_file_path(nonexistent_path, must_exist=True)