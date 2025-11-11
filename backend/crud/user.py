# backend/crud/users.py
from sqlmodel import select
from sqlalchemy.exc import NoResultFound
from backend.models.user import User, User_Info
from backend.database import AsyncSessionLocal

async def check_user(account: str, password: str) -> tuple[int, str]:
    async with AsyncSessionLocal() as db:
        # 查询用户是否存在
        result = await db.execute(select(User).where(User.account == account))
        try:
            user = result.scalar_one()
            return user.id, user.password
        except NoResultFound:
            # 创建新用户
            new_user = User(account=account, password=password)
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)  # 刷新以获取新用户的ID

            return new_user.id, password

async def get_user_info(user_id: int):
    async with AsyncSessionLocal() as db:
        # 查询用户信息
        result = await db.execute(select(User_Info).where(User_Info.user_id == user_id))
        try:
            user_info = result.scalar_one()
            return {
                "Stu_ID": user_info.Stu_ID,
                "College": user_info.College,
                "name": user_info.name
            }
        except NoResultFound:
            return None
