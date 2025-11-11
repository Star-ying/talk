from logging.config import fileConfig
from sqlalchemy import create_engine, pool
from alembic import context

# 解决 ImportError: No module named 'backend'
import sys
from pathlib import Path
# 将项目根目录加入 sys.path
sys.path.append(str(Path(__file__).resolve().parents[2]))

# 解析配置对象
config = context.config

# 配置日志（如果 alembic.ini 有 logging 配置）
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 导入模型元数据
from backend.models.character import Character
from backend.models.user import User, User_Info
from backend.models.conversation import Conversation
from sqlmodel import SQLModel

target_metadata = SQLModel.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError("sqlalchemy.url not set in config")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    db_url = context.get_x_argument(as_dictionary=True).get('db_url')
    if not db_url:
        db_url = config.get_main_option("sqlalchemy.url")
    if not db_url:
        raise RuntimeError("Database URL required. Set in alembic.ini or use -x db_url=...")

    connectable = create_engine(db_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with connection.begin():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
