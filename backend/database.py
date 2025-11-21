# backend/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

from backend.models.base import Base

# ======================
# 数据库配置
# ======================

DATABASE_URL = "mysql+asyncmy://root:123456@localhost/ai_roleplay?charset=utf8mb4"

# 串行链接 mysql+pymysql://root:123456@localhost/ai_roleplay?charset=utf8mb4

# alemic 导入配置
# from backend.models.character import Character
# from backend.models.conversation import Conversation
# from backend.models.user import User, User_Info
# from sqlmodel import SQLModel
# target_metadata = SQLModel.metadata

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=True,           # 调试用，查看生成的 SQL
    pool_pre_ping=True,
    max_overflow=10,
    pool_size=5
)

# 创建异步 Session 工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# ======================
# 初始化数据库表（仅运行一次）
# ======================
async def init_db():
    """初始化静态表（users, characters），不包括动态 conversations_* 表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # 确保 characters 表有默认数据（示例）
        result = await conn.execute(text("SELECT COUNT(*) FROM characters"))
        count = result.scalar()
        if count == 0:
            await conn.execute(
                text("""
                    INSERT INTO characters (name, trait) VALUES 
                    ('Alice', 'cheerful and smart'),
                    ('Bob', 'calm and logical')
                """)
            )
