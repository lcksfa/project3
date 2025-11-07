"""
辅助工具函数模块

提供通用的辅助函数和工具类。
"""

import os
import asyncio
import functools
from typing import Any, Callable, Optional, Dict, List, Union
from pathlib import Path


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    截断文本到指定长度

    Args:
        text: 待截断的文本
        max_length: 最大长度
        suffix: 截断后的后缀

    Returns:
        截断后的文本
    """
    if not text or len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def format_error_message(error: Exception, include_traceback: bool = False) -> str:
    """
    格式化错误消息

    Args:
        error: 异常对象
        include_traceback: 是否包含堆栈跟踪

    Returns:
        格式化后的错误消息
    """
    if include_traceback:
        import traceback
        return f"{type(error).__name__}: {str(error)}\n{traceback.format_exc()}"
    return f"{type(error).__name__}: {str(error)}"


def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    安全获取字典值

    Args:
        dictionary: 字典对象
        key: 键名，支持点号分隔的嵌套键
        default: 默认值

    Returns:
        获取到的值或默认值
    """
    keys = key.split('.')
    current = dictionary

    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return default

    return current


def chunks(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    将列表分割成指定大小的块

    Args:
        lst: 待分割的列表
        chunk_size: 块大小

    Returns:
        分割后的列表块
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def retry_async(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    异步重试装饰器

    Args:
        max_attempts: 最大尝试次数
        delay: 初始延迟时间
        backoff_factor: 延迟递增因子
        exceptions: 需要重试的异常类型
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        raise e

            # 理论上不会执行到这里
            raise last_exception

        return wrapper
    return decorator


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    确保目录存在，不存在则创建

    Args:
        path: 目录路径

    Returns:
        Path对象
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def clean_text(text: str) -> str:
    """
    清理文本，移除多余的空白字符

    Args:
        text: 待清理的文本

    Returns:
        清理后的文本
    """
    if not text:
        return ""

    # 移除首尾空白
    text = text.strip()

    # 替换多个连续的空白字符为单个空格
    import re
    text = re.sub(r'\s+', ' ', text)

    return text


def mask_sensitive_info(text: str, mask_char: str = "*") -> str:
    """
    掩码敏感信息

    Args:
        text: 包含敏感信息的文本
        mask_char: 掩码字符

    Returns:
        掩码后的文本
    """
    if not text or len(text) <= 4:
        return mask_char * len(text) if text else ""

    # 保留前2位和后2位，中间用掩码替代
    return text[:2] + mask_char * (len(text) - 4) + text[-2:]


def get_env_bool(key: str, default: bool = False) -> bool:
    """
    从环境变量获取布尔值

    Args:
        key: 环境变量键
        default: 默认值

    Returns:
        布尔值
    """
    value = os.getenv(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')


def get_env_int(key: str, default: int = 0) -> int:
    """
    从环境变量获取整数值

    Args:
        key: 环境变量键
        default: 默认值

    Returns:
        整数值
    """
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def get_env_float(key: str, default: float = 0.0) -> float:
    """
    从环境变量获取浮点数值

    Args:
        key: 环境变量键
        default: 默认值

    Returns:
        浮点数值
    """
    try:
        return float(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小

    Args:
        size_bytes: 字节数

    Returns:
        格式化后的文件大小字符串
    """
    if size_bytes == 0:
        return "0B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)

    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1

    return f"{size:.1f}{size_names[i]}"


def generate_request_id() -> str:
    """
    生成请求ID

    Returns:
        唯一的请求ID
    """
    import uuid
    import time
    timestamp = str(int(time.time()))
    random_uuid = str(uuid.uuid4())[:8]
    return f"req_{timestamp}_{random_uuid}"


class Timer:
    """计时器上下文管理器"""

    def __init__(self, name: str = "操作"):
        self.name = name
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        import time
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        self.end_time = time.time()

    @property
    def elapsed(self) -> float:
        """获取经过的时间（秒）"""
        if self.start_time is None:
            return 0.0
        end_time = self.end_time or __import__('time').time()
        return end_time - self.start_time

    def __str__(self) -> str:
        return f"{self.name}耗时: {self.elapsed:.2f}秒"