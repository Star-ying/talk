# backend/models/base.py
from sqlmodel import SQLModel
from sqlalchemy import Column, DateTime, String, text
from datetime import datetime, timezone

# --- 公共类型定义 ---
# 统一长度限制
VARCHAR_50 = String(50)
VARCHAR_100 = String(100)
VARCHAR_255 = String(255)

# 可复用的时间列
created_at_column = Column(
    DateTime(timezone=True),
    nullable=False,
    default=lambda: datetime.now(timezone.utc),  # Python 层默认
    server_default=text("CURRENT_TIMESTAMP"),   # 数据库层默认
)

updated_at_column = Column(
    DateTime(timezone=True),
    nullable=False,
    default=lambda: datetime.now(timezone.utc),
    onupdate=lambda: datetime.now(timezone.utc),  # 注意：SQLModel 中 onupdate 可能不生效！
    server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
)

class Base(SQLModel):
    pass
