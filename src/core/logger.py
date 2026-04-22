"""
日志模块
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console

# 全局 Console
console = Console()


def setup_logger(
    name: str = "xhs",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    rich_format: bool = True
) -> logging.Logger:
    """设置日志器"""
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 清除已有 handlers
    logger.handlers.clear()
    
    if rich_format:
        # Rich 格式化输出
        handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            markup=True
        )
        handler.setLevel(level)
        logger.addHandler(handler)
    else:
        # 普通格式
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    # 文件日志
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# 全局日志器
logger = setup_logger()
