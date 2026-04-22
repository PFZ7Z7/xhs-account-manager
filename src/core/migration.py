"""
账号迁移模块
"""
from typing import List, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from src.models.schema import Account, User, Note
from src.api.client import XHSClient
from src.core.database import get_db
from src.core.logger import logger
from src.utils.helpers import random_delay, ProgressTracker


console = Console()
db = get_db()


class AccountMigrator:
    """账号迁移器"""
    
    def __init__(self, source_account: Account, target_account: Account):
        """
        Args:
            source_account: 源账号
            target_account: 目标账号
        """
        self.source = XHSClient(source_account)
        self.target = XHSClient(target_account)
    
    def migrate_followings(self, max_count: int = 1000, skip_existing: bool = True) -> dict:
        """
        迁移关注
        
        Args:
            max_count: 最大迁移数量
            skip_existing: 是否跳过已关注的用户
        
        Returns:
            迁移结果统计
        """
        stats = {
            "total": 0,
            "success": 0,
            "skipped": 0,
            "failed": 0
        }
        
        console.print(f"[cyan]开始迁移关注列表...[/cyan]")
        
        # 获取源账号关注列表
        followings = list(self.source.get_all_followings(max_count=max_count))
        stats["total"] = len(followings)
        
        # 获取目标账号已关注列表
        existing_ids = set()
        if skip_existing:
            existing = list(self.target.get_all_followings(max_count=5000))
            existing_ids = {u.user_id for u in existing}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task("迁移关注...", total=len(followings))
            
            for user in followings:
                progress.update(task, advance=1)
                
                # 跳过已关注
                if user.user_id in existing_ids:
                    stats["skipped"] += 1
                    continue
                
                # 关注用户
                if self.target.follow_user(user.user_id):
                    stats["success"] += 1
                    console.print(f"  ✅ 关注成功: {user.nickname}", style="green")
                else:
                    stats["failed"] += 1
                    console.print(f"  ❌ 关注失败: {user.nickname}", style="red")
                
                # 随机延迟
                random_delay(0.5, 2.0)
        
        console.print(f"\n[bold]迁移完成:[/bold]")
        console.print(f"  总数: {stats['total']}")
        console.print(f"  成功: {stats['success']}")
        console.print(f"  跳过: {stats['skipped']}")
        console.print(f"  失败: {stats['failed']}")
        
        return stats
    
    def migrate_collections(self, max_count: int = 1000, skip_existing: bool = True) -> dict:
        """
        迁移收藏
        
        Args:
            max_count: 最大迁移数量
            skip_existing: 是否跳过已收藏的笔记
        
        Returns:
            迁移结果统计
        """
        stats = {
            "total": 0,
            "success": 0,
            "skipped": 0,
            "failed": 0
        }
        
        console.print(f"[cyan]开始迁移收藏列表...[/cyan]")
        
        # 获取源账号收藏列表
        collections = list(self.source.get_all_collections(max_count=max_count))
        stats["total"] = len(collections)
        
        # 获取目标账号已收藏列表
        existing_ids = set()
        if skip_existing:
            existing = list(self.target.get_all_collections(max_count=5000))
            existing_ids = {n.note_id for n in existing}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task("迁移收藏...", total=len(collections))
            
            for note in collections:
                progress.update(task, advance=1)
                
                # 跳过已收藏
                if note.note_id in existing_ids:
                    stats["skipped"] += 1
                    continue
                
                # 收藏笔记
                if self.target.collect_note(note.note_id):
                    stats["success"] += 1
                    console.print(f"  ✅ 收藏成功: {note.title[:30]}...", style="green")
                else:
                    stats["failed"] += 1
                    console.print(f"  ❌ 收藏失败: {note.title[:30]}...", style="red")
                
                random_delay(0.5, 2.0)
        
        console.print(f"\n[bold]迁移完成:[/bold]")
        console.print(f"  总数: {stats['total']}")
        console.print(f"  成功: {stats['success']}")
        console.print(f"  跳过: {stats['skipped']}")
        console.print(f"  失败: {stats['failed']}")
        
        return stats
    
    def migrate_all(self, max_followings: int = 1000, max_collections: int = 1000) -> dict:
        """
        迁移所有数据
        
        Returns:
            迁移结果统计
        """
        results = {}
        
        # 迁移关注
        results["followings"] = self.migrate_followings(max_count=max_followings)
        
        # 迁移收藏
        results["collections"] = self.migrate_collections(max_count=max_collections)
        
        return results


class BatchOperator:
    """批量操作器"""
    
    def __init__(self, account: Account):
        self.client = XHSClient(account)
    
    def unfollow_all(self, max_count: int = 1000, confirm: bool = True) -> dict:
        """
        批量取关
        
        Args:
            max_count: 最大取关数量
            confirm: 是否需要确认
        
        Returns:
            操作结果统计
        """
        stats = {
            "total": 0,
            "success": 0,
            "failed": 0
        }
        
        # 获取关注列表
        followings = list(self.client.get_all_followings(max_count=max_count))
        stats["total"] = len(followings)
        
        if confirm:
            console.print(f"[yellow]即将取关 {stats['total']} 个用户[/yellow]")
            if not console.input("确认继续？[y/N]: ").lower() == 'y':
                console.print("已取消")
                return stats
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task("批量取关...", total=len(followings))
            
            for user in followings:
                progress.update(task, advance=1)
                
                if self.client.unfollow_user(user.user_id):
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
                
                random_delay(0.5, 2.0)
        
        console.print(f"\n[bold]取关完成:[/bold] 成功 {stats['success']}, 失败 {stats['failed']}")
        return stats
    
    def uncollect_all(self, max_count: int = 1000, confirm: bool = True) -> dict:
        """
        批量取消收藏
        
        Args:
            max_count: 最大数量
            confirm: 是否需要确认
        
        Returns:
            操作结果统计
        """
        stats = {
            "total": 0,
            "success": 0,
            "failed": 0
        }
        
        # 获取收藏列表
        collections = list(self.client.get_all_collections(max_count=max_count))
        stats["total"] = len(collections)
        
        if confirm:
            console.print(f"[yellow]即将取消收藏 {stats['total']} 个笔记[/yellow]")
            if not console.input("确认继续？[y/N]: ").lower() == 'y':
                console.print("已取消")
                return stats
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task("批量取消收藏...", total=len(collections))
            
            for note in collections:
                progress.update(task, advance=1)
                
                if self.client.uncollect_note(note.note_id):
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
                
                random_delay(0.5, 2.0)
        
        console.print(f"\n[bold]取消收藏完成:[/bold] 成功 {stats['success']}, 失败 {stats['failed']}")
        return stats
