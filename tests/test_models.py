"""
测试数据模型
"""
import pytest
from datetime import datetime

from src.models.schema import CookieData, Account, User, Note


def test_cookie_data_from_string():
    """测试 Cookie 解析"""
    cookie_str = "web_session=abc123; a1=xyz789; webId=test123"
    cookie = CookieData.from_string(cookie_str)
    
    assert cookie.web_session == "abc123"
    assert cookie.a1 == "xyz789"
    assert cookie.webId == "test123"


def test_cookie_data_to_header():
    """测试 Cookie 转换为头部"""
    cookie = CookieData(
        web_session="abc123",
        a1="xyz789"
    )
    
    header = cookie.to_header()
    
    assert "web_session=abc123" in header
    assert "a1=xyz789" in header


def test_account_model():
    """测试账号模型"""
    account = Account(
        id="test_001",
        name="测试账号",
        cookies=CookieData(web_session="test")
    )
    
    assert account.id == "test_001"
    assert account.name == "测试账号"
    assert account.status == "active"
    assert isinstance(account.created_at, datetime)


def test_user_model():
    """测试用户模型"""
    user = User(
        user_id="user123",
        nickname="测试用户",
        fans_count=1000,
        following_count=200
    )
    
    assert user.user_id == "user123"
    assert user.nickname == "测试用户"
    assert user.fans_count == 1000
    assert user.is_following is False


def test_note_model():
    """测试笔记模型"""
    note = Note(
        note_id="note123",
        title="测试笔记",
        desc="这是一篇测试笔记",
        liked_count=100,
        collected_count=50
    )
    
    assert note.note_id == "note123"
    assert note.title == "测试笔记"
    assert note.liked_count == 100
    assert note.is_liked is False
