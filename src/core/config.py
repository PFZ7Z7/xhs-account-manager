"""
配置管理模块
"""
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
import yaml
import os

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"


class APIConfig(BaseModel):
    """API 配置"""
    base_url: str = "https://edith.xiaohongshu.com"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


class AccountConfig(BaseModel):
    """账号配置"""
    cookie_expire_hours: int = 24
    auto_refresh: bool = False
    max_accounts: int = 10


class RequestConfig(BaseModel):
    """请求配置"""
    rate_limit: float = 1.0  # 每秒请求数
    random_delay: bool = True
    min_delay: float = 0.5
    max_delay: float = 2.0


class Config(BaseModel):
    """主配置"""
    api: APIConfig = Field(default_factory=APIConfig)
    account: AccountConfig = Field(default_factory=AccountConfig)
    request: RequestConfig = Field(default_factory=RequestConfig)
    debug: bool = False

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "Config":
        """加载配置文件"""
        if path is None:
            path = CONFIG_DIR / "config.yaml"
        
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return cls(**data)
        
        return cls()

    def save(self, path: Optional[Path] = None) -> None:
        """保存配置文件"""
        if path is None:
            path = CONFIG_DIR / "config.yaml"
        
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(self.model_dump(), f, allow_unicode=True, default_flow_style=False)


# 全局配置实例
_config: Optional[Config] = None


def get_config() -> Config:
    """获取全局配置"""
    global _config
    if _config is None:
        _config = Config.load()
    return _config


def init_config(config_path: Optional[Path] = None) -> Config:
    """初始化配置"""
    global _config
    _config = Config.load(config_path)
    return _config
