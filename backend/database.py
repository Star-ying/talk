# backend/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

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
