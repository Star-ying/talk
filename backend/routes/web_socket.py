# backend/routes/room.py
import time
from fastapi import APIRouter, Request, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
import json
import logging
from typing import List

from jinja2 import Environment, FileSystemLoader

from jwt_handler import get_current_user_id
from backend.crud.user import get_user_info
from setting import FRONTEND_DIR

logger = logging.getLogger(__name__)

template_env = Environment(loader=FileSystemLoader(str(FRONTEND_DIR)))

router = APIRouter()

# 存储活跃的 WebSocket 连接（简单示例，生产建议用 Redis 或后台任务管理）
active_connections: List[WebSocket] = []

@router.get("/room", response_class=HTMLResponse)
async def chat_room_page(request: Request, current_user_id: str = Depends(get_current_user_id)):
    client_ip = request.client.host
    logger.info(f"📋 User {current_user_id} accessing /room from IP: {client_ip}")

    if not current_user_id:
        logger.warning(f"🚫 Unauthorized access to /room from IP: {client_ip}")
        return RedirectResponse(url="/login")

    template = template_env.get_template("room.html")
    user_result = await get_user_info(int(current_user_id))
    stu_id = user_result['Stu_ID'] if user_result else "Unknown"

    content = template.render(debug_user=current_user_id, stu_id = stu_id)
    return HTMLResponse(content=content)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, current_user_id: str = None):
    # 注意：FastAPI 中 WebSocket 不支持直接使用 Depends 在路径参数中，需手动解析
    try:
        # 手动从 cookie 提取 token 并验证
        token = websocket.cookies.get("access_token")
        if not token:
            await websocket.close(code=4001, reason="Missing access token")
            return

        current_user_id = await get_current_user_id(token)  # 复用你的函数（稍作改造见下方说明）
        if not current_user_id:
            await websocket.close(code=4001, reason="Invalid or expired token")
            return

        user_result = await get_user_info(current_user_id)
        stu_id = user_result['Stu_ID'] if user_result else "Unknown"
    except Exception as e:
        logger.error(f"WebSocket auth failed: {e}")
        await websocket.close(code=4001, reason="Authentication failed")
        return

    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"🟢 User {stu_id} ({current_user_id}) connected via WebSocket")

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            msg_type = message_data.get("type")
            content = message_data.get("content", "").strip()

            if not content:
                continue

            # 构造广播消息
            response = {
                "type": "message",
                "user_id": current_user_id,
                "stu_id": stu_id,
                "content": content,
                "timestamp": int(time.time())
            }

            # 广播给所有连接的客户端
            disconnected = []
            for conn in active_connections:
                try:
                    await conn.send_json(response)
                except Exception:
                    disconnected.append(conn)

            # 移除失效连接
            for conn in disconnected:
                if conn in active_connections:
                    active_connections.remove(conn)

    except WebSocketDisconnect:
        logger.info(f"🔴 User {stu_id} ({current_user_id}) disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for user {current_user_id}: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)
