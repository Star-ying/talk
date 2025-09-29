# backend/database.py
import re
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# 数据库配置（请替换为你的真实信息）
DATABASE_URL = "mysql+asyncmy://root:123456@localhost/ai_roleplay?charset=utf8mb4"

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # 调试时可设为 True 查看 SQL 输出
    pool_pre_ping=True,
    max_overflow=10,
    pool_size=5
)

# 创建异步 Session 工厂
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 工具函数：获取用户专属对话表名
def get_conversation_table_name(user_id: str):
    # 安全处理 user_id，防止 SQL 注入（仅允许字母数字下划线）
    safe_id = "".join(c for c in user_id if c.isalnum() or c == "_")
    return f"conversations_{safe_id}"

# 用户表名白名单校验（防止 SQL 注入）
def is_valid_table_name(table_name: str) -> bool:
    return re.match(r'^conversations_[a-zA-Z0-9_]+$', table_name) is not None

async def check_users(account: str, password: str):
    async with AsyncSessionLocal() as db:
        # 先查询是否存在该账号
        result = await db.execute(
            text("SELECT id, password FROM users WHERE account = :account"),
            {"account": account}
        )
        row = result.fetchone()

        if row:
            user_id, stored_password = row
            return user_id, stored_password

        # 如果不存在，插入新用户
        await db.execute(
            text("""
                INSERT INTO users (account, password)
                VALUES (:account, :password)
            """),
            {"account": account, "password": password}
        )
        await db.commit()

        # 获取刚插入的 ID
        result = await db.execute(text("SELECT LAST_INSERT_ID()"))
        user_id = result.scalar()

        # 动态创建专属对话表（注意：表名需安全）
        table_name = f"conversations_{user_id}"
        if not is_valid_table_name(table_name):
            raise ValueError("Invalid user ID for table name")

        try:
            await db.execute(text(f"""
                CREATE TABLE IF NOT EXISTS `{table_name}` (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    character_id INT,
                    user_message TEXT,
                    ai_message TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
                ) ENGINE=InnoDB CHARSET=utf8mb4;
            """))
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise Exception(f"Failed to create conversation table for user {user_id}: {e}")

        return user_id, password

async def get_all_characters():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("SELECT * FROM characters ORDER BY name")
        )
        rows = result.fetchall()
        # 转成字典列表
        return [dict(row._mapping) for row in rows]

async def save_conversation(user_id: int, character_id: int, user_msg: str, ai_msg: str):
    async with AsyncSessionLocal() as db:
        table_name = f"conversations_{user_id}"
        if not is_valid_table_name(table_name):
            raise ValueError("Invalid user ID")

        try:
            await db.execute(
                text(f"""
                    INSERT INTO `{table_name}`
                    (character_id, user_message, ai_message)
                    VALUES (:character_id, :user_msg, :ai_msg)
                """),
                {
                    "character_id": character_id,
                    "user_msg": user_msg,
                    "ai_msg": ai_msg
                }
            )
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise Exception(f"[DB] Failed to save conversation for user {user_id}: {e}")

async def get_character_by_id(character_id: int):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("SELECT name, trait FROM characters WHERE id = :id"),
            {"id": character_id}
        )
        row = result.fetchone()
        if not row:
            return None
        return dict(row._mapping)  # 返回 {'name': ..., 'trait': ...}

async def get_user_profile(user_id: str) -> Optional[Dict]:
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                text("""
                    SELECT personality, role_setting
                    FROM user_profiles
                    WHERE user_id = :user_id
                """),
                {"user_id": user_id}
            )
            row = result.fetchone()
            return dict(row._mapping) if row else None
        except Exception as e:
            raise Exception(f"[DB] Failed to fetch profile for {user_id}: {e}")

async def create_or_update_user_profile(user_id: str, personality: str, role_setting: str) -> bool:
    async with AsyncSessionLocal() as db:
        try:
            query = text("""
                INSERT INTO user_profiles (user_id, personality, role_setting)
                VALUES (:user_id, :personality, :role_setting)
                ON DUPLICATE KEY UPDATE
                    personality = VALUES(personality),
                    role_setting = VALUES(role_setting)
            """)
            await db.execute(
                query,
                {
                    "user_id": user_id,
                    "personality": personality.strip(),
                    "role_setting": role_setting.strip()
                }
            )
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            raise Exception(f"[DB] Failed to save profile for {user_id}: {e}")

async def load_history_from_db(user_id: str, max_count: int = 4):
    """
    从数据库加载最近的对话历史
    """
    table_name = get_conversation_table_name(user_id)
    async with AsyncSessionLocal() as db:
        result = await db.execute(text(f"""
            SELECT role, content FROM `{table_name}`
            ORDER BY timestamp DESC
            LIMIT :limit
        """), {"limit": max_count})
        rows = result.fetchall()
        # 反转顺序，变成时间正序
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

async def save_message_to_db(user_id: str, role: str, content: str):
    """
    保存一条消息到用户专属表
    """
    table_name = get_conversation_table_name(user_id)
    async with AsyncSessionLocal() as db:
        await db.execute(text(f"""
            INSERT INTO `{table_name}` (role, content)
            VALUES (:role, :content)
        """), {"role": role, "content": content})
        await db.commit()