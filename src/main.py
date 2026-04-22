"""
更新后的 CLI 命令行工具
"""
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.core.config import init_config
from src.core.database import get_db
from src.core.logger import logger
from src.core.migration import AccountMigrator, BatchOperator
from src.core.export import DataExporter, DataImporter
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
@click.option("--yes", "-y", is_flag=True, help="跳过确认")
def following_unfollow(account_id: str, target: Optional[str], batch: bool, 
                       count: int, yes: bool):
    """取消关注"""
    account = db.get_account(account_id)
    if not account:
        console.print(f"❌ 账号不存在: {account_id}", style="red")
        return
    
    if batch:
        operator = BatchOperator(account)
        operator.unfollow_all(max_count=count, confirm=not yes)
    elif target:
        client = XHSClient(account)
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


@collection.command("uncollect")
@click.argument("account_id")
@click.option("--batch", "-b", is_flag=True, help="批量取消收藏")
@click.option("--count", "-c", default=10, help="批量数量")
@click.option("--yes", "-y", is_flag=True, help="跳过确认")
def collection_uncollect(account_id: str, batch: bool, count: int, yes: bool):
    """取消收藏"""
    account = db.get_account(account_id)
    if not account:
        console.print(f"❌ 账号不存在: {account_id}", style="red")
        return
    
    if batch:
        operator = BatchOperator(account)
        operator.uncollect_all(max_count=count, confirm=not yes)
    else:
        console.print("请指定 --batch", style="yellow")


# ========== 数据迁移 ==========

@click.group()
def migrate():
    """数据迁移"""
    pass


@migrate.command("following")
@click.argument("source_id")
@click.argument("target_id")
@click.option("--count", "-c", default=100, help="迁移数量")
@click.option("--skip-existing", is_flag=True, default=True, help="跳过已关注")
def migrate_following(source_id: str, target_id: str, count: int, skip_existing: bool):
    """迁移关注"""
    source = db.get_account(source_id)
    target = db.get_account(target_id)
    
    if not source or not target:
        console.print("❌ 账号不存在", style="red")
        return
    
    migrator = AccountMigrator(source, target)
    migrator.migrate_followings(max_count=count, skip_existing=skip_existing)


@migrate.command("collection")
@click.argument("source_id")
@click.argument("target_id")
@click.option("--count", "-c", default=100, help="迁移数量")
@click.option("--skip-existing", is_flag=True, default=True, help="跳过已收藏")
def migrate_collection(source_id: str, target_id: str, count: int, skip_existing: bool):
    """迁移收藏"""
    source = db.get_account(source_id)
    target = db.get_account(target_id)
    
    if not source or not target:
        console.print("❌ 账号不存在", style="red")
        return
    
    migrator = AccountMigrator(source, target)
    migrator.migrate_collections(max_count=count, skip_existing=skip_existing)


# ========== 数据备份 ==========

@click.group()
def backup():
    """数据备份"""
    pass


@backup.command("export")
@click.argument("account_id")
@click.option("--type", "-t", type=click.Choice(["following", "collection", "all"]), default="all")
@click.option("--format", "-f", type=click.Choice(["json", "csv"]), default="json")
@click.option("--output", "-o", default="./backup", help="输出目录")
def backup_export(account_id: str, type: str, format: str, output: str):
    """导出数据"""
    account = db.get_account(account_id)
    if not account:
        console.print(f"❌ 账号不存在: {account_id}", style="red")
        return
    
    exporter = DataExporter(account)
    output_dir = Path(output)
    
    if type == "all":
        results = exporter.export_all(output_dir, format=format)
        console.print(f"✅ 导出完成: 关注 {results['followings']}, 收藏 {results['collections']}", style="green")
    elif type == "following":
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = output_dir / f"followings_{timestamp}.{format}"
        count = exporter.export_followings(path, format=format)
        console.print(f"✅ 导出关注: {count} 个", style="green")
    elif type == "collection":
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = output_dir / f"collections_{timestamp}.{format}"
        count = exporter.export_collections(path, format=format)
        console.print(f"✅ 导出收藏: {count} 个", style="green")


@backup.command("import")
@click.argument("account_id")
@click.argument("input_file")
@click.option("--type", "-t", type=click.Choice(["following", "collection"]), required=True)
def backup_import(account_id: str, input_file: str, type: str):
    """导入数据"""
    account = db.get_account(account_id)
    if not account:
        console.print(f"❌ 账号不存在: {account_id}", style="red")
        return
    
    importer = DataImporter(account)
    input_path = Path(input_file)
    
    if type == "following":
        stats = importer.import_followings(input_path)
    elif type == "collection":
        stats = importer.import_collections(input_path)
    
    console.print(f"✅ 导入完成: 成功 {stats['success']}, 跳过 {stats['skipped']}, 失败 {stats['failed']}", style="green")


# ========== 主入口 ==========

@click.group()
def cli():
    """小红书账号管理工具"""
    init_config()


cli.add_command(account)
cli.add_command(following)
cli.add_command(collection)
cli.add_command(migrate)
cli.add_command(backup)


if __name__ == "__main__":
    cli()
