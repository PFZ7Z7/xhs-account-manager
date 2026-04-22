"""
数据存储模块 - SQLite
"""
import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Any, Dict
from datetime import datetime
from contextlib import contextmanager

from src.models.schema import Account, CookieData, User, Note, Following, Collection, Like
from src.core.logger import logger


class Database:
    """数据库管理"""
    
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "data" / "xhs.db"
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()
    
    @contextmanager
    def connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_tables(self):
        """初始化表结构"""
        with self.connection() as conn:
            cursor = conn.cursor()
            
            # 账号表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    user_id TEXT,
                    nickname TEXT,
                    cookies TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    last_used TIMESTAMP
                )
            """)
            
            # 关注表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS followings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT NOT NULL,
                    target_user_id TEXT NOT NULL,
                    target_nickname TEXT,
                    target_avatar TEXT,
                    target_desc TEXT,
                    created_at TIMESTAMP,
                    UNIQUE(account_id, target_user_id)
                )
            """)
            
            # 收藏表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS collections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT NOT NULL,
                    note_id TEXT NOT NULL,
                    note_title TEXT,
                    note_desc TEXT,
                    note_type TEXT,
                    author_id TEXT,
                    author_nickname TEXT,
                    note_data TEXT,
                    created_at TIMESTAMP,
                    UNIQUE(account_id, note_id)
                )
            """)
            
            # 点赞表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS likes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT NOT NULL,
                    note_id TEXT NOT NULL,
                    note_title TEXT,
                    note_data TEXT,
                    created_at TIMESTAMP,
                    UNIQUE(account_id, note_id)
                )
            """)
            
            # 操作日志表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS operation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT,
                    operation TEXT,
                    target TEXT,
                    status TEXT,
                    message TEXT,
                    created_at TIMESTAMP
                )
            """)
            
            logger.info("数据库初始化完成")
    
    # ========== 账号管理 ==========
    
    def save_account(self, account: Account) -> None:
        """保存账号"""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO accounts 
                (id, name, user_id, nickname, cookies, status, created_at, updated_at, last_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                account.id,
                account.name,
                account.user_id,
                account.nickname,
                account.cookies.model_dump_json(),
                account.status,
                account.created_at.isoformat(),
                account.updated_at.isoformat(),
                account.last_used.isoformat() if account.last_used else None
            ))
            logger.info(f"账号保存成功: {account.name}")
    
    def get_account(self, account_id: str) -> Optional[Account]:
        """获取账号"""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_account(row)
            return None
    
    def list_accounts(self) -> List[Account]:
        """列出所有账号"""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts ORDER BY created_at DESC")
            return [self._row_to_account(row) for row in cursor.fetchall()]
    
    def delete_account(self, account_id: str) -> bool:
        """删除账号"""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
            return cursor.rowcount > 0
    
    def _row_to_account(self, row: sqlite3.Row) -> Account:
        """行转账号对象"""
        cookies = CookieData.model_validate_json(row["cookies"]) if row["cookies"] else CookieData()
        return Account(
            id=row["id"],
            name=row["name"],
            user_id=row["user_id"],
            nickname=row["nickname"],
            cookies=cookies,
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.now(),
            last_used=datetime.fromisoformat(row["last_used"]) if row["last_used"] else None
        )
    
    # ========== 关注管理 ==========
    
    def save_following(self, account_id: str, user: User) -> None:
        """保存关注"""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO followings
                (account_id, target_user_id, target_nickname, target_avatar, target_desc, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                account_id,
                user.user_id,
                user.nickname,
                user.avatar,
                user.desc,
                datetime.now().isoformat()
            ))
    
    def get_followings(self, account_id: str, limit: int = 100, offset: int = 0) -> List[User]:
        """获取关注列表"""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM followings 
                WHERE account_id = ? 
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (account_id, limit, offset))
            
            return [
                User(
                    user_id=row["target_user_id"],
                    nickname=row["target_nickname"] or "",
                    avatar=row["target_avatar"],
                    desc=row["target_desc"]
                )
                for row in cursor.fetchall()
            ]
    
    def get_following_count(self, account_id: str) -> int:
        """获取关注数量"""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM followings WHERE account_id = ?", (account_id,))
            return cursor.fetchone()[0]
    
    def delete_following(self, account_id: str, target_user_id: str) -> bool:
        """删除关注"""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM followings 
                WHERE account_id = ? AND target_user_id = ?
            """, (account_id, target_user_id))
            return cursor.rowcount > 0
    
    # ========== 收藏管理 ==========
    
    def save_collection(self, account_id: str, note: Note) -> None:
        """保存收藏"""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO collections
                (account_id, note_id, note_title, note_desc, note_type, 
                 author_id, author_nickname, note_data, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                account_id,
                note.note_id,
                note.title,
                note.desc,
                note.type,
                note.author.user_id if note.author else None,
                note.author.nickname if note.author else None,
                note.model_dump_json(),
                datetime.now().isoformat()
            ))
    
    def get_collections(self, account_id: str, limit: int = 100, offset: int = 0) -> List[Note]:
        """获取收藏列表"""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM collections 
                WHERE account_id = ? 
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (account_id, limit, offset))
            
            notes = []
            for row in cursor.fetchall():
                if row["note_data"]:
                    notes.append(Note.model_validate_json(row["note_data"]))
                else:
                    notes.append(Note(
                        note_id=row["note_id"],
                        title=row["note_title"] or "",
                        desc=row["note_desc"],
                        type=row["note_type"] or "normal"
                    ))
            return notes
    
    # ========== 操作日志 ==========
    
    def log_operation(self, account_id: str, operation: str, target: str, 
                      status: str, message: str = "") -> None:
        """记录操作日志"""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO operation_logs
                (account_id, operation, target, status, message, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (account_id, operation, target, status, message, datetime.now().isoformat()))


# 全局数据库实例
_db: Optional[Database] = None


def get_db() -> Database:
    """获取数据库实例"""
    global _db
    if _db is None:
        _db = Database()
    return _db
