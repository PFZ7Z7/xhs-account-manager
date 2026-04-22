"""
数据模型定义
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CookieData(BaseModel):
    """Cookie 数据"""
    web_session: Optional[str] = None
    a1: Optional[str] = None
    webId: Optional[str] = None
    websectiga: Optional[str] = None
    sec_poison_id: Optional[str] = None
    extra: Dict[str, str] = Field(default_factory=dict)

    def to_header(self) -> str:
        """转换为 Cookie 字符串"""
        cookies = []
        if self.web_session:
            cookies.append(f"web_session={self.web_session}")
        if self.a1:
            cookies.append(f"a1={self.a1}")
        if self.webId:
            cookies.append(f"webId={self.webId}")
        if self.websectiga:
            cookies.append(f"websectiga={self.websectiga}")
        if self.sec_poison_id:
            cookies.append(f"sec_poison_id={self.sec_poison_id}")
        for k, v in self.extra.items():
            cookies.append(f"{k}={v}")
        return "; ".join(cookies)

    @classmethod
    def from_string(cls, cookie_str: str) -> "CookieData":
        """从字符串解析"""
        data = {}
        for item in cookie_str.split(";"):
            item = item.strip()
            if "=" in item:
                k, v = item.split("=", 1)
                data[k.strip()] = v.strip()
        
        return cls(
            web_session=data.get("web_session"),
            a1=data.get("a1"),
            webId=data.get("webId"),
            websectiga=data.get("websectiga"),
            sec_poison_id=data.get("sec_poison_id"),
            extra={k: v for k, v in data.items() 
                   if k not in ["web_session", "a1", "webId", "websectiga", "sec_poison_id"]}
        )


class Account(BaseModel):
    """账号模型"""
    id: str
    name: str
    user_id: Optional[str] = None
    nickname: Optional[str] = None
    cookies: CookieData = Field(default_factory=CookieData)
    status: str = "active"  # active, expired, banned
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_used: Optional[datetime] = None

    def touch(self) -> None:
        """更新使用时间"""
        self.last_used = datetime.now()
        self.updated_at = datetime.now()


class User(BaseModel):
    """用户模型（小红书用户）"""
    user_id: str
    nickname: str
    avatar: Optional[str] = None
    desc: Optional[str] = None
    fans_count: int = 0
    following_count: int = 0
    note_count: int = 0
    is_following: bool = False


class Note(BaseModel):
    """笔记模型"""
    note_id: str
    title: str
    desc: Optional[str] = None
    type: str = "normal"  # normal, video
    author: Optional[User] = None
    images: List[str] = Field(default_factory=list)
    video_url: Optional[str] = None
    liked_count: int = 0
    collected_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    is_liked: bool = False
    is_collected: bool = False
    created_at: Optional[datetime] = None


class Following(BaseModel):
    """关注关系"""
    user_id: str
    target_user: User
    created_at: datetime = Field(default_factory=datetime.now)


class Collection(BaseModel):
    """收藏"""
    user_id: str
    note: Note
    collection_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class Like(BaseModel):
    """点赞"""
    user_id: str
    note: Note
    created_at: datetime = Field(default_factory=datetime.now)


class OperationResult(BaseModel):
    """操作结果"""
    success: bool
    message: str = ""
    data: Optional[Any] = None
    error: Optional[str] = None
