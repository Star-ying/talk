from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text, DateTime, Index, text
from datetime import datetime

class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"

    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)  # 用于分片查询
    character_id: int = Field(foreign_key="characters.id")

    user_message: str = Field(sa_column=Column(Text))
    ai_message: str = Field(sa_column=Column(Text))

    timestamp: datetime = Field(
        default=None,
        sa_column=Column(
            DateTime, 
            server_default=text('CURRENT_TIMESTAMP'), 
            nullable=False
        )
    )

# 创建复合索引加速查询
Index("ix_conversation_user_char", Conversation.user_id, Conversation.character_id)
