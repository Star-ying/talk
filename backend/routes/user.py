# backend/routes/user.py
from setting import logger
from fastapi import APIRouter, HTTPException, Depends

from jwt_handler import get_current_user_id
from backend.crud.user import create_or_update_user_info
from backend.models.user import User_Info

router = APIRouter(prefix="/user",tags=["用户信息管理"])

@router.post("/commit")
async def commit_user_info(
    data: User_Info,
    current_user_id: int = Depends(get_current_user_id)  # 确保类型为 int
) -> dict:
    try:
        logger.info(data)

        if not data:
            return {
                "success": False,
                "message": "请求体为空"
            }

        # 执行创建或更新
        user_info = await create_or_update_user_info(user_id=current_user_id, user_info_data=data.model_dump())

        # ✅ 成功响应：结构化输出
        return {
            "success": True,
            "message": "用户信息保存成功",
            "data": user_info.model_dump() if hasattr(user_info, "dict") else user_info  # 兼容 SQLModel
        }

    except HTTPException:
        # 如果是主动抛出的 HTTPException，交给 FastAPI 处理
        raise
    except Exception as e:
        logger.error(f"保存用户信息失败 (user_id={current_user_id}): {str(e)}", exc_info=True)

        # ✅ 统一错误响应
        return {
            "success": False,
            "message": "服务器内部错误，请稍后重试",
            "error": "internal_server_error"
        }