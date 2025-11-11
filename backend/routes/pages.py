# backend/routes/pages.py
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader
import json
import logging

from jwt_handler import get_current_user_id, verify_password, get_password_hash, create_access_token
from backend.crud.user import check_user
from backend.crud.character import get_all_characters
from setting import ENV_CONFIG, FRONTEND_DIR

logger = logging.getLogger(__name__)

# 使用 Jinja2Templates 或手动加载模板（避免循环导入）
template_env = Environment(loader=FileSystemLoader(str(FRONTEND_DIR)))

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def home():
    template = template_env.get_template("home.html")
    content = template.render(debug_user=None)
    return HTMLResponse(content=content)

@router.get("/login", response_class=HTMLResponse)
async def login_page():
    template = template_env.get_template("login.html")
    content = template.render()
    return HTMLResponse(content=content)

@router.post("/login")
async def login(request: Request):
    data = await request.json()
    account = data.get("account")
    password = data.get("password")
    hash_password = get_password_hash(password)

    if not account or not password:
        logger.warning(f"Login failed: missing credentials")
        return JSONResponse({"success": False, "message": "请输入用户名和密码"}, status_code=400)

    result = await check_user(account, hash_password)
    if not result:
        logger.warning(f"Login failed: user not found - {account}")
        return JSONResponse({"success": False, "message": "用户名或密码错误"}, status_code=401)

    user_id, hashed_password_from_db = result

    if not verify_password(password, hashed_password_from_db):
        logger.warning(f"Login failed: wrong password for user {account}")
        return JSONResponse({"success": False, "message": "用户名或密码错误"}, status_code=401)

    from datetime import timedelta
    access_token_expires = timedelta(minutes=int(ENV_CONFIG.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30)))
    access_token = create_access_token(data={"sub": str(user_id)}, expires_delta=access_token_expires)

    logger.info(f"🔐 User {user_id} logged in successfully")

    response = JSONResponse({"success": True, "account": account})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=access_token_expires.total_seconds()
    )
    return response

@router.get("/ai", response_class=HTMLResponse)
async def chat_page(request: Request, current_user_id: str = Depends(get_current_user_id)):
    client_ip = request.client.host
    logger.info(f"📋 User {current_user_id} accessing /user from IP: {client_ip}")

    if not current_user_id:
        logger.warning(f"🚫 Unauthorized access to /user from IP: {client_ip}")
        return RedirectResponse(url="/login")

    template = template_env.get_template("ai_talk.html")
    characters = await get_all_characters()
    characters_json = json.dumps([
        {"id": c["id"], "name": c["name"], "trait": c["trait"]}
        for c in characters
    ], ensure_ascii=False)
    content = template.render(characters=characters, characters_json=characters_json, debug_user=current_user_id)
    return HTMLResponse(content=content)
