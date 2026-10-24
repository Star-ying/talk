# backend/models/character.py
from sqlmodel import Field
from .base import Base, VARCHAR_100
from sqlalchemy import Text

class Character(Base, table=True):
    __tablename__ = "characters"

    id: int = Field(default=None, primary_key=True, index=True)
    name: str = Field(
        sa_type=VARCHAR_100,
        nullable=False,
        description="角色名称"
    )
    trait: str = Field(
        sa_type=Text,
        default=None,
        nullable=True,
        description="角色性格描述"
    )
