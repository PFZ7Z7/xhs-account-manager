"""
工具函数模块
"""
import time
import random
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime


def generate_id(prefix: str = "") -> str:
    """生成唯一 ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = hashlib.md5(str(random.random()).encode()).hexdigest()[:6]
    return f"{prefix}{timestamp}{random_str}"


def random_delay(min_delay: float = 0.5, max_delay: float = 2.0) -> None:
    """随机延迟"""
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)


def format_number(num: int) -> str:
    """格式化数字（如 1.2万）"""
    if num >= 10000:
        return f"{num / 10000:.1f}万"
    elif num >= 1000:
        return f"{num / 1000:.1f}k"
    return str(num)


def parse_timestamp(ts: Optional[int]) -> Optional[datetime]:
    """解析时间戳"""
    if ts is None:
        return None
    
    # 毫秒转秒
    if ts > 10000000000:
        ts = ts // 1000
    
    return datetime.fromtimestamp(ts)


def mask_string(s: str, show_len: int = 4) -> str:
    """遮蔽字符串（用于日志）"""
    if len(s) <= show_len * 2:
        return s[:show_len] + "*" * (len(s) - show_len)
    return s[:show_len] + "*" * (len(s) - show_len * 2) + s[-show_len:]


def chunk_list(lst: list, chunk_size: int) -> list:
    """分块列表"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def retry_on_failure(func, max_retries: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """
    失败重试装饰器
    
    Usage:
        @retry_on_failure(max_retries=3, delay=1.0)
        def my_function():
            ...
    """
    def wrapper(*args, **kwargs):
        last_exception = None
        for i in range(max_retries):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                if i < max_retries - 1:
                    time.sleep(delay * (i + 1))  # 指数退避
        raise last_exception
    return wrapper


class RateLimiter:
    """速率限制器"""
    
    def __init__(self, rate: float = 1.0):
        """
        Args:
            rate: 每秒请求数
        """
        self.rate = rate
        self.min_interval = 1.0 / rate
        self.last_time = 0
    
    def wait(self) -> None:
        """等待直到可以发送下一个请求"""
        current = time.time()
        elapsed = current - self.last_time
        
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        
        self.last_time = time.time()


class ProgressTracker:
    """进度追踪器"""
    
    def __init__(self, total: int, desc: str = "Processing"):
        self.total = total
        self.desc = desc
        self.current = 0
        self.start_time = time.time()
    
    def update(self, n: int = 1) -> None:
        """更新进度"""
        self.current += n
    
    def get_progress(self) -> float:
        """获取进度百分比"""
        if self.total == 0:
            return 0
        return min(100, self.current / self.total * 100)
    
    def get_eta(self) -> float:
        """获取预计剩余时间（秒）"""
        if self.current == 0:
            return 0
        
        elapsed = time.time() - self.start_time
        rate = self.current / elapsed
        remaining = self.total - self.current
        
        return remaining / rate if rate > 0 else 0
    
    def __str__(self) -> str:
        progress = self.get_progress()
        eta = self.get_eta()
        return f"{self.desc}: {self.current}/{self.total} ({progress:.1f}%) ETA: {eta:.0f}s"
