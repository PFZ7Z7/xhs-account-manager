"""
数据导出模块
"""
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.models.schema import Account, User, Note
from src.api.client import XHSClient
from src.core.database import get_db
from src.core.logger import logger


class DataExporter:
    """数据导出器"""
    
    def __init__(self, account: Account):
        self.client = XHSClient(account)
        self.account = account
        self.db = get_db()
    
    def export_followings(self, output_path: Path, format: str = "json", 
                          max_count: int = 5000) -> int:
        """
        导出关注列表
        
        Args:
            output_path: 输出路径
            format: 格式 (json/csv)
            max_count: 最大数量
        
        Returns:
            导出数量
        """
        followings = list(self.client.get_all_followings(max_count=max_count))
        
        if format == "json":
            data = {
                "account": self.account.name,
                "exported_at": datetime.now().isoformat(),
                "total": len(followings),
                "followings": [f.model_dump() for f in followings]
            }
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        elif format == "csv":
            with open(output_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["用户ID", "昵称", "粉丝数", "关注数", "笔记数", "简介"])
                for user in followings:
                    writer.writerow([
                        user.user_id,
                        user.nickname,
                        user.fans_count,
                        user.following_count,
                        user.note_count,
                        user.desc or ""
                    ])
        
        logger.info(f"导出关注列表: {len(followings)} 个")
        return len(followings)
    
    def export_collections(self, output_path: Path, format: str = "json",
                           max_count: int = 5000) -> int:
        """
        导出收藏列表
        
        Args:
            output_path: 输出路径
            format: 格式
            max_count: 最大数量
        
        Returns:
            导出数量
        """
        collections = list(self.client.get_all_collections(max_count=max_count))
        
        if format == "json":
            data = {
                "account": self.account.name,
                "exported_at": datetime.now().isoformat(),
                "total": len(collections),
                "collections": [c.model_dump() for c in collections]
            }
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        elif format == "csv":
            with open(output_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["笔记ID", "标题", "作者", "点赞数", "收藏数", "评论数", "类型"])
                for note in collections:
                    writer.writerow([
                        note.note_id,
                        note.title,
                        note.author.nickname if note.author else "",
                        note.liked_count,
                        note.collected_count,
                        note.comment_count,
                        note.type
                    ])
        
        logger.info(f"导出收藏列表: {len(collections)} 个")
        return len(collections)
    
    def export_all(self, output_dir: Path, format: str = "json",
                   max_followings: int = 5000, max_collections: int = 5000) -> Dict[str, int]:
        """
        导出所有数据
        
        Args:
            output_dir: 输出目录
            format: 格式
            max_followings: 关注最大数量
            max_collections: 收藏最大数量
        
        Returns:
            导出统计
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results = {}
        
        # 导出关注
        followings_path = output_dir / f"followings_{timestamp}.{format}"
        results["followings"] = self.export_followings(
            followings_path, format, max_followings
        )
        
        # 导出收藏
        collections_path = output_dir / f"collections_{timestamp}.{format}"
        results["collections"] = self.export_collections(
            collections_path, format, max_collections
        )
        
        return results


class DataImporter:
    """数据导入器"""
    
    def __init__(self, account: Account):
        self.client = XHSClient(account)
        self.account = account
    
    def import_followings(self, input_path: Path, skip_existing: bool = True) -> Dict[str, int]:
        """
        导入关注列表
        
        Args:
            input_path: 输入文件路径
            skip_existing: 是否跳过已关注
        
        Returns:
            导入统计
        """
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        followings = data.get("followings", [])
        
        stats = {
            "total": len(followings),
            "success": 0,
            "skipped": 0,
            "failed": 0
        }
        
        # 获取已关注列表
        existing_ids = set()
        if skip_existing:
            existing = list(self.client.get_all_followings(max_count=5000))
            existing_ids = {u.user_id for u in existing}
        
        for user_data in followings:
            user_id = user_data.get("user_id")
            
            if user_id in existing_ids:
                stats["skipped"] += 1
                continue
            
            if self.client.follow_user(user_id):
                stats["success"] += 1
            else:
                stats["failed"] += 1
        
        return stats
    
    def import_collections(self, input_path: Path, skip_existing: bool = True) -> Dict[str, int]:
        """
        导入收藏列表
        
        Args:
            input_path: 输入文件路径
            skip_existing: 是否跳过已收藏
        
        Returns:
            导入统计
        """
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        collections = data.get("collections", [])
        
        stats = {
            "total": len(collections),
            "success": 0,
            "skipped": 0,
            "failed": 0
        }
        
        # 获取已收藏列表
        existing_ids = set()
        if skip_existing:
            existing = list(self.client.get_all_collections(max_count=5000))
            existing_ids = {n.note_id for n in existing}
        
        for note_data in collections:
            note_id = note_data.get("note_id")
            
            if note_id in existing_ids:
                stats["skipped"] += 1
                continue
            
            if self.client.collect_note(note_id):
                stats["success"] += 1
            else:
                stats["failed"] += 1
        
        return stats
