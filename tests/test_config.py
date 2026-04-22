"""
测试配置模块
"""
import pytest
from pathlib import Path
import tempfile
import os

from src.core.config import Config, APIConfig, AccountConfig, RequestConfig


def test_config_defaults():
    """测试默认配置"""
    config = Config()
    
    assert config.api.base_url == "https://edith.xiaohongshu.com"
    assert config.api.timeout == 30
    assert config.account.max_accounts == 10
    assert config.request.rate_limit == 1.0


def test_config_save_and_load():
    """测试配置保存和加载"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        
        config = Config(
            api=APIConfig(timeout=60),
            debug=True
        )
        config.save(config_path)
        
        loaded = Config.load(config_path)
        
        assert loaded.api.timeout == 60
        assert loaded.debug is True


def test_api_config():
    """测试 API 配置"""
    config = APIConfig(
        base_url="https://test.com",
        timeout=10,
        max_retries=5
    )
    
    assert config.base_url == "https://test.com"
    assert config.timeout == 10
    assert config.max_retries == 5


def test_request_config():
    """测试请求配置"""
    config = RequestConfig(
        rate_limit=2.0,
        random_delay=False,
        min_delay=1.0,
        max_delay=3.0
    )
    
    assert config.rate_limit == 2.0
    assert config.random_delay is False
