"""
小红书 API 客户端
"""
import time
import random
from typing import Optional, Dict, Any, Generator
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.api.signature import XHSSignature, XHSAPIBuilder
from src.models.schema import CookieData, User, Note, Account
from src.core.config import get_config
from src.core.logger import logger
from src.core.database import get_db


class XHSClient:
    """小红书 API 客户端"""
    
    def __init__(self, account: Account):
        self.account = account
        self.config = get_config()
        self.session = self._create_session()
        self.db = get_db()
    
    def _create_session(self) -> requests.Session:
        """创建请求会话"""
        session = requests.Session()
        
        # 重试策略
        retry = Retry(
            total=self.config.api.max_retries,
            backoff_factor=self.config.api.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 默认请求头
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Origin": "https://www.xiaohongshu.com",
            "Referer": "https://www.xiaohongshu.com/",
            "Content-Type": "application/json;charset=UTF-8",
        })
        
        # 设置 Cookie
        if self.account.cookies:
            session.headers["Cookie"] = self.account.cookies.to_header()
        
        return session
    
    def _delay(self) -> None:
        """请求延迟"""
        if self.config.request.random_delay:
            delay = random.uniform(
                self.config.request.min_delay,
                self.config.request.max_delay
            )
        else:
            delay = 1.0 / self.config.request.rate_limit
        
        time.sleep(delay)
    
    def _request(self, method: str, endpoint: str, 
                 params: Optional[Dict] = None,
                 data: Optional[Dict] = None,
                 use_app_api: bool = False) -> Dict[str, Any]:
        """
        发送请求
        
        Args:
            method: HTTP 方法
            endpoint: API 端点名称或路径
            params: URL 参数
            data: 请求体数据
            use_app_api: 是否使用 App API
        
        Returns:
            响应数据
        """
        url = XHSAPIBuilder.get_url(endpoint, use_app_api)
        
        # 生成签名
        sign_headers = XHSSignature.sign_request(method, url, params, data)
        
        headers = self.session.headers.copy()
        headers.update(sign_headers)
        
        self._delay()
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers,
                timeout=self.config.api.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            # 记录操作
            self.db.log_operation(
                account_id=self.account.id,
                operation=f"{method} {endpoint}",
                target=url,
                status="success" if result.get("success") else "failed",
                message=str(result.get("msg", ""))
            )
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {e}")
            self.db.log_operation(
                account_id=self.account.id,
                operation=f"{method} {endpoint}",
                target=url,
                status="error",
                message=str(e)
            )
            raise
    
    # ========== 用户信息 ==========
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """获取当前用户信息"""
        try:
            result = self._request("GET", "user_info")
            if result.get("success"):
                return result.get("data")
            return None
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return None
    
    # ========== 关注管理 ==========
    
    def get_following_list(self, cursor: str = "", count: int = 30) -> Dict[str, Any]:
        """
        获取关注列表
        
        Args:
            cursor: 分页游标
            count: 每页数量
        
        Returns:
            关注列表数据
        """
        data = {
            "cursor": cursor,
            "num": count,
            "image_formats": ["jpg", "webp", "avif"]
        }
        
        result = self._request("POST", "following_list", data=data)
        return result
    
    def get_all_followings(self, max_count: int = 1000) -> Generator[User, None, None]:
        """
        获取所有关注（自动翻页）
        
        Args:
            max_count: 最大获取数量
        
        Yields:
            User 对象
        """
        cursor = ""
        total = 0
        
        while total < max_count:
            result = self.get_following_list(cursor=cursor)
            
            if not result.get("success"):
                logger.error(f"获取关注列表失败: {result.get('msg')}")
                break
            
            data = result.get("data", {})
            users = data.get("users", [])
            
            for user_data in users:
                user = User(
                    user_id=user_data.get("userid", ""),
                    nickname=user_data.get("nickname", ""),
                    avatar=user_data.get("image"),
                    desc=user_data.get("desc"),
                    fans_count=user_data.get("fansCount", 0),
                    following_count=user_data.get("followsCount", 0),
                    note_count=user_data.get("noteCount", 0),
                    is_following=True
                )
                
                # 保存到数据库
                self.db.save_following(self.account.id, user)
                
                yield user
                total += 1
                
                if total >= max_count:
                    break
            
            # 下一页
            cursor = data.get("cursor", "")
            has_more = data.get("has_more", False)
            
            if not has_more or not cursor:
                break
        
        logger.info(f"获取关注列表完成，共 {total} 个")
    
    def follow_user(self, user_id: str) -> bool:
        """关注用户"""
        data = {
            "target_user_id": user_id,
            "type": "follow"
        }
        
        try:
            result = self._request("POST", "follow", data=data)
            success = result.get("success", False)
            
            if success:
                logger.info(f"关注成功: {user_id}")
            else:
                logger.warning(f"关注失败: {result.get('msg')}")
            
            return success
        except Exception as e:
            logger.error(f"关注失败: {e}")
            return False
    
    def unfollow_user(self, user_id: str) -> bool:
        """取消关注"""
        data = {
            "target_user_id": user_id,
            "type": "unfollow"
        }
        
        try:
            result = self._request("POST", "unfollow", data=data)
            success = result.get("success", False)
            
            if success:
                logger.info(f"取关成功: {user_id}")
                # 从数据库删除
                self.db.delete_following(self.account.id, user_id)
            else:
                logger.warning(f"取关失败: {result.get('msg')}")
            
            return success
        except Exception as e:
            logger.error(f"取关失败: {e}")
            return False
    
    # ========== 收藏管理 ==========
    
    def get_collection_list(self, cursor: str = "", count: int = 30) -> Dict[str, Any]:
        """获取收藏列表"""
        data = {
            "cursor": cursor,
            "num": count,
            "image_formats": ["jpg", "webp", "avif"]
        }
        
        result = self._request("POST", "collection_list", data=data)
        return result
    
    def get_all_collections(self, max_count: int = 1000) -> Generator[Note, None, None]:
        """获取所有收藏"""
        cursor = ""
        total = 0
        
        while total < max_count:
            result = self.get_collection_list(cursor=cursor)
            
            if not result.get("success"):
                logger.error(f"获取收藏列表失败: {result.get('msg')}")
                break
            
            data = result.get("data", {})
            notes = data.get("notes", [])
            
            for note_data in notes:
                note = self._parse_note(note_data)
                
                # 保存到数据库
                self.db.save_collection(self.account.id, note)
                
                yield note
                total += 1
                
                if total >= max_count:
                    break
            
            cursor = data.get("cursor", "")
            has_more = data.get("has_more", False)
            
            if not has_more or not cursor:
                break
        
        logger.info(f"获取收藏列表完成，共 {total} 个")
    
    def collect_note(self, note_id: str) -> bool:
        """收藏笔记"""
        data = {
            "note_id": note_id,
            "type": "collect"
        }
        
        try:
            result = self._request("POST", "collect", data=data)
            return result.get("success", False)
        except Exception as e:
            logger.error(f"收藏失败: {e}")
            return False
    
    def uncollect_note(self, note_id: str) -> bool:
        """取消收藏"""
        data = {
            "note_id": note_id,
            "type": "uncollect"
        }
        
        try:
            result = self._request("POST", "uncollect", data=data)
            return result.get("success", False)
        except Exception as e:
            logger.error(f"取消收藏失败: {e}")
            return False
    
    # ========== 点赞管理 ==========
    
    def get_like_list(self, cursor: str = "", count: int = 30) -> Dict[str, Any]:
        """获取点赞列表"""
        data = {
            "cursor": cursor,
            "num": count
        }
        
        result = self._request("POST", "like_list", data=data)
        return result
    
    def like_note(self, note_id: str) -> bool:
        """点赞笔记"""
        data = {
            "note_id": note_id,
            "type": "like"
        }
        
        try:
            result = self._request("POST", "like", data=data)
            return result.get("success", False)
        except Exception as e:
            logger.error(f"点赞失败: {e}")
            return False
    
    def unlike_note(self, note_id: str) -> bool:
        """取消点赞"""
        data = {
            "note_id": note_id,
            "type": "unlike"
        }
        
        try:
            result = self._request("POST", "unlike", data=data)
            return result.get("success", False)
        except Exception as e:
            logger.error(f"取消点赞失败: {e}")
            return False
    
    # ========== 辅助方法 ==========
    
    def _parse_note(self, data: Dict) -> Note:
        """解析笔记数据"""
        user_data = data.get("user", {})
        
        return Note(
            note_id=data.get("noteId", ""),
            title=data.get("displayTitle", ""),
            desc=data.get("desc", ""),
            type=data.get("type", "normal"),
            author=User(
                user_id=user_data.get("userId", ""),
                nickname=user_data.get("nickname", ""),
                avatar=user_data.get("image")
            ) if user_data else None,
            images=data.get("imagesList", []),
            liked_count=data.get("likedCount", 0),
            collected_count=data.get("collectedCount", 0),
            comment_count=data.get("commentCount", 0),
            share_count=data.get("shareCount", 0),
            is_liked=data.get("isLiked", False),
            is_collected=data.get("isCollected", False)
        )
