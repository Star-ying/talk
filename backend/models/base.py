# backend/models/base.py
from sqlmodel import SQLModel

class Base(SQLModel):
    """所有模型的基类"""
    class Config:
        arbitrary_types_allowed = True
        from_attributes = True  # 兼容 SQLAlchemy ORM 模式