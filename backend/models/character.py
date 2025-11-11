# backend/models/character.py
from sqlmodel import Field, Text
from .base import Base

class Character(Base, table=True):
    __tablename__ = "characters"

    id: int = Field(default=None, primary_key=True, index=True, nullable=False)
    name: str = Field(max_length=100, nullable=False)
    trait: str = Field(default=None, sa_type=Text, nullable=True)
    
    # 添加示例方法展示 SQLModel 优势
    def greet(self):
        return f"Hello, I'm {self.name}!"
