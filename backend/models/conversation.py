# backend/models/conversation.py
from pydantic import BaseModel
from sqlmodel import Field
from sqlalchemy import Column, Text, Index
from datetime import datetime
from .base import Base,created_at_column

class Conversation(Base, table=True):
    __tablename__ = "conversations"

    id: int = Field(default=None, primary_key=True)

    user_id: int = Field(index=True, nullable=False, description="用户ID")
    character_id: int = Field(foreign_key="characters.id", nullable=False)

    user_message: str = Field(sa_column=Column("user_message", Text))
    ai_message: str = Field(sa_column=Column("ai_message", Text))

    timestamp: datetime = Field(sa_column=created_at_column)

class CreateConversationRequest(BaseModel):
    character_id: int
    user_message: str

# 手动创建复合索引（在 metadata 创建时自动应用）
Index("ix_conversation_user_char", Conversation.user_id, Conversation.character_id)
