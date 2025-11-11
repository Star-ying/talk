# backend/crud/characters.py
from sqlmodel import select
from backend.database import AsyncSessionLocal
from backend.models.character import Character

async def get_all_characters() -> list[dict]:
    async with AsyncSessionLocal() as db:
        # 查询所有角色
        result = await db.execute(select(Character).order_by(Character.name))
        chars = result.scalars().all()
        return [{
            "id": c.id,
            "name": c.name,
            "trait": c.trait
        } for c in chars]

async def get_character_by_id(character_id: int) -> dict | None:
    async with AsyncSessionLocal() as db:
        # 查询单个角色
        result = await db.execute(select(Character).where(Character.id == character_id))
        char = result.scalar_one_or_none()
        if not char:
            return None
        return {
            "id": char.id,
            "name": char.name,
            "trait": char.trait
        }
