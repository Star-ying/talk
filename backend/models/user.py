# backend/models/user.py
from datetime import date
from typing import List, Optional
from sqlmodel import Field, Relationship
from sqlalchemy import Column, String, Date
from .base import Base, VARCHAR_100, VARCHAR_255, VARCHAR_50

class User(Base, table=True):
    __tablename__ = "users"

    id: int = Field(default=None, primary_key=True)
    account: str = Field(
        sa_type=VARCHAR_100,
        unique=True,
        index=True,
        nullable=False
    )
    password: str = Field(
        sa_type=VARCHAR_255,
        nullable=False
    )

    # 关联 UserInfo（一对一）
    user_info: "User_Info" = Relationship(
        back_populates="user",
        cascade_delete=True
    )

class User_Info(Base, table=True):
    __tablename__ = "user_info"

    # 主键：学号 —— 必填
    stu_id: str = Field(sa_type=VARCHAR_100, primary_key=True, description="学号")

    # 核心信息（必填）
    name: str = Field(sa_type=VARCHAR_100, nullable=False)
    college: str = Field(sa_type=VARCHAR_100, nullable=False)
    major: Optional[str] = Field(sa_type=VARCHAR_100, default=None)  # 可选
    class_name: Optional[str] = Field(sa_type=VARCHAR_100, default=None)  # 可选
    grade: Optional[int] = Field(default=None)  # 年级可空
    gender: Optional[str] = Field(sa_type=String(10), default=None)

    # 非核心信息（全部设为可选）
    birth_date: Optional[date] = Field(
        sa_column=Column("birth_date", Date, default=None, nullable=True)
    )
    enrollment_date: Optional[date] = Field(
        sa_column=Column("enrollment_date", Date, default=None, nullable=True)
    )
    phone: Optional[str] = Field(sa_type=String(15), default="", nullable=True)
    email: Optional[str] = Field(sa_type=VARCHAR_100, default="", nullable=True)
    qq: Optional[str] = Field(sa_type=String(15), default="", nullable=True)
    dormitory: Optional[str] = Field(sa_type=VARCHAR_50, default="", nullable=True)

    political_status: Optional[str] = Field(sa_type=String(20), default="群众")  # 不强制“群众”

    # 外键
    user_id: int = Field(foreign_key="users.id", nullable=False)

    # 关系
    user: User = Relationship(back_populates="user_info")
    
    def is_complete(self, required_fields: List[str] = None) -> bool:
        """
        检查指定必填字段是否都不为空（非None且非空字符串）
        """
        if required_fields is None:
            required_fields = ["name", "college", "stu_id"]

        for field in required_fields:
            value = getattr(self, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                return False
        return True