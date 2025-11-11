# backend/crud/conversations.py
from backend.database import AsyncSessionLocal
from backend.models.conversation import Conversation

async def save_conversation(user_id: int, character_id: int, user_msg: str, ai_msg: str):
    async with AsyncSessionLocal() as db:
        try:
            # 创建新记录
            record = Conversation(
                user_id=user_id,
                character_id=character_id,
                user_message=user_msg,
                ai_message=ai_msg
            )
            
            db.add(record)
            await db.commit()
            await db.refresh(record)  # 刷新以获取ID等数据库生成的值
            return True
        except Exception as e:
            await db.rollback()
            raise Exception(f"[DB] Failed to save conversation for user {user_id}: {e}")
