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
            return user.id, user.password, True
        except NoResultFound:
            # 创建新用户
            new_user = User(account=account, password=password)
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)  # 刷新以获取新用户的ID

            return new_user.id, password, False

async def get_user_info(user_id: int):
    async with AsyncSessionLocal() as db:
        # 查询用户信息
        result = await db.execute(select(User_Info).where(User_Info.user_id == user_id))
        try:
            user_info = result.scalar_one()
            return user_info
        except NoResultFound:
            return None
        
async def create_or_update_user_info(user_id: int, user_info_data: dict):
    """
    创建或更新用户的详细信息
    :param user_id: 关联的 users.id
    :param user_info_data: 包含 Stu_ID, name, College 等字段的字典
    :return: 写入后的 User_Info 对象
    """
    async with AsyncSessionLocal() as db:
        # 先尝试根据 user_id 查找是否已有记录
        result = await db.execute(
            select(User_Info).where(User_Info.user_id == user_id)
        )
        existing_info = result.scalar_one_or_none()

        if existing_info:
            # 存在则更新
            for key, value in user_info_data.items():
                if hasattr(existing_info, key):
                    setattr(existing_info, key, value)
            db.add(existing_info)
        else:
            # 不存在则创建新记录
            new_info = User_Info(**user_info_data, user_id=user_id)
            db.add(new_info)
            existing_info = new_info
        await db.commit()
        await db.refresh(existing_info)  # 刷新以获取最新数据（如主键）
        return existing_info
