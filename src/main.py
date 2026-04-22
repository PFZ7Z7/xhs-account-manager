"""
CLI 命令行工具
"""
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from datetime import datetime
from typing import Optional

from src.core.config import init_config
from src.core.database import get_db, Database
from src.core.logger import logger
from src.models.schema import Account, CookieData
from src.api.client import XHSClient

console = Console()
db = get_db()


# ========== 账号管理 ==========

@click.group()
def account():
    """账号管理"""
    pass


@account.command("add")
@click.option("--name", "-n", prompt="账号名称", help="账号名称")
@click.option("--cookie", "-c", prompt="Cookie", help="Cookie 字符串")
def account_add(name: str, cookie: str):
    """添加账号"""
    account_id = f"acc_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    cookies = CookieData.from_string(cookie)
    
    account = Account(
        id=account_id,
        name=name,
        cookies=cookies
    )
    
    db.save_account(account)
    console.print(f"✅ 账号添加成功: {name}", style="green")


@account.command("list")
def account_list():
    """列出所有账号"""
    accounts = db.list_accounts()
    
    if not accounts:
        console.print("暂无账号", style="yellow")
        return
    
    table = Table(title="账号列表")
    table.add_column("ID", style="cyan")
    table.add_column("名称", style="green")
    table.add_column("用户ID", style="blue")
    table.add_column("状态", style="magenta")
    table.add_column("创建时间", style="dim")
    
    for acc in accounts:
        table.add_row(
            acc.id,
            acc.name,
            acc.user_id or "-",
            acc.status,
            acc.created_at.strftime("%Y-%m-%d %H:%M")
        )
    
    console.print(table)


@account.command("delete")
@click.argument("account_id")
def account_delete(account_id: str):
    """删除账号"""
    if db.delete_account(account_id):
        console.print(f"✅ 账号删除成功: {account_id}", style="green")
    else:
        console.print(f"❌ 账号不存在: {account_id}", style="red")


# ========== 关注管理 ==========

@click.group()
def following():
    """关注管理"""
    pass


@following.command("list")
@click.argument("account_id")
@click.option("--limit", "-l", default=50, help="显示数量")
def following_list(account_id: str, limit: int):
    """获取关注列表"""
    account = db.get_account(account_id)
    if not account:
        console.print(f"❌ 账号不存在: {account_id}", style="red")
        return
    
    client = XHSClient(account)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("获取关注列表...", total=None)
        
        users = list(client.get_all_followings(max_count=limit))
    
    table = Table(title=f"关注列表 ({len(users)} 个)")
    table.add_column("#", style="dim")
    table.add_column("用户ID", style="cyan")
    table.add_column("昵称", style="green")
    table.add_column("粉丝数", style="blue")
    
    for i, user in enumerate(users, 1):
        table.add_row(
            str(i),
            user.user_id,
            user.nickname,
            str(user.fans_count)
        )
    
    console.print(table)


@following.command("unfollow")
@click.argument("account_id")
@click.option("--target", "-t", help="目标用户ID")
@click.option("--batch", "-b", is_flag=True, help="批量取关")
@click.option("--count", "-c", default=10, help="批量取关数量")
def following_unfollow(account_id: str, target: Optional[str], batch: bool, count: int):
    """取消关注"""
    account = db.get_account(account_id)
    if not account:
        console.print(f"❌ 账号不存在: {account_id}", style="red")
        return
    
    client = XHSClient(account)
    
    if batch:
        # 批量取关
        followings = db.get_followings(account_id, limit=count)
        
        success = 0
        failed = 0
        
        for user in followings:
            if client.unfollow_user(user.user_id):
                success += 1
                console.print(f"✅ 取关成功: {user.nickname}", style="green")
            else:
                failed += 1
                console.print(f"❌ 取关失败: {user.nickname}", style="red")
        
        console.print(f"\n批量取关完成: 成功 {success}, 失败 {failed}")
    
    elif target:
        # 单个取关
        if client.unfollow_user(target):
            console.print(f"✅ 取关成功: {target}", style="green")
        else:
            console.print(f"❌ 取关失败: {target}", style="red")
    
    else:
        console.print("请指定 --target 或 --batch", style="yellow")


# ========== 收藏管理 ==========

@click.group()
def collection():
    """收藏管理"""
    pass


@collection.command("list")
@click.argument("account_id")
@click.option("--limit", "-l", default=50, help="显示数量")
def collection_list(account_id: str, limit: int):
    """获取收藏列表"""
    account = db.get_account(account_id)
    if not account:
        console.print(f"❌ 账号不存在: {account_id}", style="red")
        return
    
    client = XHSClient(account)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("获取收藏列表...", total=None)
        
        notes = list(client.get_all_collections(max_count=limit))
    
    table = Table(title=f"收藏列表 ({len(notes)} 个)")
    table.add_column("#", style="dim")
    table.add_column("笔记ID", style="cyan")
    table.add_column("标题", style="green")
    table.add_column("作者", style="blue")
    table.add_column("点赞", style="magenta")
    
    for i, note in enumerate(notes, 1):
        table.add_row(
            str(i),
            note.note_id[:20] + "...",
            note.title[:30] + ("..." if len(note.title) > 30 else ""),
            note.author.nickname if note.author else "-",
            str(note.liked_count)
        )
    
    console.print(table)


# ========== 数据备份 ==========

@click.group()
def backup():
    """数据备份"""
    pass


@backup.command("export")
@click.argument("account_id")
@click.option("--type", "-t", type=click.Choice(["following", "collection", "all"]), default="all")
@click.option("--output", "-o", default="backup.json", help="输出文件")
def backup_export(account_id: str, type: str, output: str):
    """导出数据"""
    import json
    
    account = db.get_account(account_id)
    if not account:
        console.print(f"❌ 账号不存在: {account_id}", style="red")
        return
    
    client = XHSClient(account)
    data = {"account": account.name, "exported_at": datetime.now().isoformat()}
    
    if type in ["following", "all"]:
        console.print("导出关注列表...")
        followings = list(client.get_all_followings())
        data["followings"] = [f.model_dump() for f in followings]
    
    if type in ["collection", "all"]:
        console.print("导出收藏列表...")
        collections = list(client.get_all_collections())
        data["collections"] = [c.model_dump() for c in collections]
    
    with open(output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    console.print(f"✅ 导出完成: {output}", style="green")


# ========== 主入口 ==========

@click.group()
def cli():
    """小红书账号管理工具"""
    init_config()


cli.add_command(account)
cli.add_command(following)
cli.add_command(collection)
cli.add_command(backup)


if __name__ == "__main__":
    cli()
