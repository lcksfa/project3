"""
日志系统模块

提供结构化日志记录功能。
"""

import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any
import structlog
from structlog.stdlib import LoggerFactory

from .config_simple import get_settings
from .config_adapter import get_config_adapter


class ColoredConsoleRenderer:
    """彩色控制台渲染器"""

    COLORS = {
        'debug': '\033[36m',      # 青色
        'info': '\033[32m',       # 绿色
        'warning': '\033[33m',    # 黄色
        'error': '\033[31m',      # 红色
        'critical': '\033[35m',   # 紫色
        'reset': '\033[0m'        # 重置
    }

    def __call__(self, logger, method_name: str, event_dict: Dict[str, Any]) -> str:
        """渲染日志消息"""
        level = event_dict.get('level', 'info').lower()
        color = self.COLORS.get(level, '')
        reset = self.COLORS['reset']

        timestamp = event_dict.get('timestamp', '')
        message = event_dict.get('event', '')

        # 构建基础消息
        log_msg = f"{color}[{level.upper()}]{reset} {message}"

        # 添加时间戳
        if timestamp:
            log_msg = f"{timestamp} {log_msg}"

        # 添加额外字段
        extra_fields = {k: v for k, v in event_dict.items()
                       if k not in ['level', 'timestamp', 'event', 'logger']}

        if extra_fields:
            extra_str = ' | '.join(f"{k}={v}" for k, v in extra_fields.items())
            log_msg += f" | {extra_str}"

        return log_msg


def setup_logging(config: Optional[Any] = None) -> None:
    """设置日志系统"""
    if config is None:
        config = get_config_adapter().logging

    # 确保日志目录存在
    log_file = Path(config.file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # 解析文件大小
    max_bytes = _parse_file_size(config.max_file_size)

    # 配置structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if config.format.lower() == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        if config.console_output:
            processors.append(ColoredConsoleRenderer())
        else:
            processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # 配置标准库logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, config.level),
    )

    # 添加文件处理器
    if config.file:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=config.file,
            maxBytes=max_bytes,
            backupCount=config.backup_count,
            encoding='utf-8'
        )

        if config.format.lower() == "json":
            file_formatter = logging.Formatter('%(message)s')
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(getattr(logging, config.level))

        # 添加到根logger
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)

    # 设置第三方库日志级别
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def _parse_file_size(size_str: str) -> int:
    """解析文件大小字符串"""
    size_str = size_str.upper().strip()

    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        # 默认为字节
        return int(size_str)


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """获取logger实例"""
    return structlog.get_logger(name)


class LoggerMixin:
    """Logger混入类"""

    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """获取当前类的logger"""
        return get_logger(self.__class__.__name__)


# 预定义的logger实例
app_logger = get_logger("app")
api_logger = get_logger("api")
service_logger = get_logger("service")
ui_logger = get_logger("ui")