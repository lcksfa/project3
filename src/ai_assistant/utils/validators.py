"""
输入验证模块

提供各种输入数据的验证功能。
"""

import re
from typing import Optional, List
from ..core.exceptions import ValidationError


def validate_text_input(
    text: str,
    min_length: int = 1,
    max_length: int = 10000,
    allow_empty: bool = False
) -> str:
    """
    验证文本输入

    Args:
        text: 待验证的文本
        min_length: 最小长度
        max_length: 最大长度
        allow_empty: 是否允许空文本

    Returns:
        验证后的文本

    Raises:
        ValidationError: 验证失败时抛出
    """
    if text is None:
        if allow_empty:
            return ""
        raise ValidationError("文本不能为空")

    # 清理文本
    text = text.strip()

    if not text and not allow_empty:
        raise ValidationError("文本不能为空")

    if len(text) < min_length:
        raise ValidationError(f"文本长度不能少于 {min_length} 个字符")

    if len(text) > max_length:
        raise ValidationError(f"文本长度不能超过 {max_length} 个字符")

    return text


def validate_api_key(api_key: str) -> str:
    """
    验证API密钥格式

    Args:
        api_key: API密钥

    Returns:
        验证后的API密钥

    Raises:
        ValidationError: 验证失败时抛出
    """
    if not api_key:
        raise ValidationError("API密钥不能为空")

    # 清理API密钥
    api_key = api_key.strip()

    if not api_key:
        raise ValidationError("API密钥不能为空")

    # 基本格式验证（可以根据实际API要求调整）
    if len(api_key) < 10:
        raise ValidationError("API密钥长度太短")

    # 检查是否包含非法字符
    if re.search(r'[^\w\-]', api_key):
        raise ValidationError("API密钥包含非法字符")

    return api_key


def validate_email(email: str) -> str:
    """
    验证邮箱地址

    Args:
        email: 邮箱地址

    Returns:
        验证后的邮箱地址

    Raises:
        ValidationError: 验证失败时抛出
    """
    if not email:
        raise ValidationError("邮箱地址不能为空")

    email = email.strip().lower()

    # 简单的邮箱格式验证
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError("邮箱地址格式不正确")

    return email


def validate_url(url: str) -> str:
    """
    验证URL格式

    Args:
        url: URL地址

    Returns:
        验证后的URL地址

    Raises:
        ValidationError: 验证失败时抛出
    """
    if not url:
        raise ValidationError("URL不能为空")

    url = url.strip()

    # 简单的URL格式验证
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    if not re.match(pattern, url):
        raise ValidationError("URL格式不正确")

    return url


def validate_temperature(temperature: float) -> float:
    """
    验证温度参数

    Args:
        temperature: 温度参数

    Returns:
        验证后的温度参数

    Raises:
        ValidationError: 验证失败时抛出
    """
    if not isinstance(temperature, (int, float)):
        raise ValidationError("温度参数必须是数字")

    if not 0.0 <= temperature <= 2.0:
        raise ValidationError("温度参数必须在0.0到2.0之间")

    return float(temperature)


def validate_max_tokens(max_tokens: int) -> int:
    """
    验证最大token数

    Args:
        max_tokens: 最大token数

    Returns:
        验证后的最大token数

    Raises:
        ValidationError: 验证失败时抛出
    """
    if not isinstance(max_tokens, int):
        raise ValidationError("最大token数必须是整数")

    if max_tokens <= 0:
        raise ValidationError("最大token数必须大于0")

    if max_tokens > 100000:  # 设置一个合理的上限
        raise ValidationError("最大token数不能超过100000")

    return max_tokens


def validate_language_code(language: str, supported_languages: List[str]) -> str:
    """
    验证语言代码

    Args:
        language: 语言代码
        supported_languages: 支持的语言列表

    Returns:
        验证后的语言代码

    Raises:
        ValidationError: 验证失败时抛出
    """
    if not language:
        raise ValidationError("语言代码不能为空")

    language = language.strip()

    if language not in supported_languages:
        raise ValidationError(
            f"不支持的语言: {language}。支持的语言: {', '.join(supported_languages)}"
        )

    return language


def validate_positive_integer(value: int, name: str = "数值") -> int:
    """
    验证正整数

    Args:
        value: 待验证的值
        name: 值的名称

    Returns:
        验证后的值

    Raises:
        ValidationError: 验证失败时抛出
    """
    if not isinstance(value, int):
        raise ValidationError(f"{name}必须是整数")

    if value <= 0:
        raise ValidationError(f"{name}必须大于0")

    return value


def validate_file_path(file_path: str, must_exist: bool = False) -> str:
    """
    验证文件路径

    Args:
        file_path: 文件路径
        must_exist: 是否必须存在

    Returns:
        验证后的文件路径

    Raises:
        ValidationError: 验证失败时抛出
    """
    if not file_path:
        raise ValidationError("文件路径不能为空")

    file_path = file_path.strip()

    # 检查路径格式
    if not file_path:
        raise ValidationError("文件路径不能为空")

    # 检查是否包含非法字符
    illegal_chars = ['<', '>', ':', '"', '|', '?', '*']
    if any(char in file_path for char in illegal_chars):
        raise ValidationError("文件路径包含非法字符")

    if must_exist:
        from pathlib import Path
        if not Path(file_path).exists():
            raise ValidationError(f"文件不存在: {file_path}")

    return file_path