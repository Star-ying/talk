# backend/models/user.py
from datetime import date
from typing import Optional
from sqlmodel import Field, Relationship
from .base import Base

class User(Base, table=True):
    __tablename__ = "users"

    id: int = Field(default=None, primary_key=True)
    account: str = Field(max_length=100, unique=True, nullable=False)
    password: str = Field(max_length=255, nullable=False)

    # 使用 SQLModel 的关系定义
    user_info: "User_Info" = Relationship(
        back_populates="users",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "uselist": False
        }
    )

class User_Info(Base, table=True):    
    __tablename__ = "user_info"

    # 主键：学号    
    Stu_ID: str = Field(primary_key=True, max_length=100)

    # 基本信息    
    name: str = Field(max_length=100, nullable=False)    
    College: str = Field(max_length=100, nullable=False)    
    Major: Optional[str] = Field(max_length=100, default=None)          # 专业    
    Class_Name: Optional[str] = Field(max_length=100, default=None)     # 班级    
    Grade: Optional[int] = Field(default=None)                          # 年级（如 2024）    
    Gender: Optional[str] = Field(max_length=10, default=None)          # 性别    
    Birth_Date: Optional[date] = Field(default=None)                   # 出生日期    
    Enrollment_Date: Optional[date] = Field(default=None)              # 入学时间

    # 联系方式    
    Phone: Optional[str] = Field(max_length=15, default=None)           # 手机号    
    Email: Optional[str] = Field(max_length=100, default=None)          # 邮箱    
    QQ: Optional[str] = Field(max_length=15, default=None)              # QQ 号    
    Dormitory: Optional[str] = Field(max_length=50, default=None)       # 宿舍号

    # 其他    
    Political_Status: Optional[str] = Field(max_length=20, default="群众")  # 政治面貌：群众/团员/党员等

    # 外键关联到 users 表    
    user_id: int = Field(foreign_key="users.id", nullable=False)

    # 关系映射    
    users: "User" = Relationship(back_populates="user_info")
