import asyncio
from datetime import timedelta
import httpx
import json
import os
import torch
import uvicorn
from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
from jwt_handler import (
    decode_access_token,
    get_current_user_id,
    verify_password,
    get_password_hash,
    create_access_token
)
import database
import logging
from typing import Callable

# --- 日志配置 ---
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)  # 确保 logs 目录存在
LOG_FILE = LOG_DIR / "app.log"

# 配置 logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8', mode='a'),  # 写入文件
        logging.StreamHandler()  # 同时输出到控制台
    ]
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent  # 项目根目录
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI()
load_dotenv(dotenv_path=BASE_DIR / "backend" / ".env")

# 挂载静态资源
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(FRONTEND_DIR))
template_env = Environment(loader=FileSystemLoader(str(FRONTEND_DIR)))

model, tokenizer = None, None

def load_model():
    model_name = str(BASE_DIR / "model/deepseek-coder-1.3b-instruct")
    print("Loading tokenizer...")
    tok = AutoTokenizer.from_pretrained(model_name)
    print("Loading model...")
    m = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto",
        low_cpu_mem_usage=True
    ).eval()
    return m, tok

async def start_load():
    global model, tokenizer
    loop = asyncio.get_event_loop()
    model, tokenizer = await loop.run_in_executor(None, load_model)
    print("✅ Model loaded during startup!")

# --- HTTP 中间件用于调试日志 ---
@app.middleware("http")
async def debug_request_middleware(request: Request, call_next: Callable):
    # 记录客户端 IP
    client_host = request.client.host if request.client else "unknown"
    logger.info(f"➡️  {request.method} {request.url.path} from {client_host}")

    # 尝试读取 cookie 中的 token 并解析用户 ID（不中断流程）
    try:
        access_token = request.cookies.get("access_token")
        user_id = None
        if access_token:        
            user_id = decode_access_token(access_token)  # 直接调用，不加 await
        logger.info(f"👤 User ID: {user_id or 'Not logged in'}")
    except Exception as e:
        logger.warning(f"⚠️  Failed to decode user from token: {e}")
        user_id = None

    # 记录请求体（仅 POST/PUT 等有 body 的）
    if request.method in ("POST", "PUT", "PATCH"):
        try:
            body = await request.json()
            logger.debug(f"📥 Request Body: {body}")
        except Exception as e:
            logger.debug(f"❌ Could not parse request body: {e}")

    # 执行请求
    response: Response = await call_next(request)

    # 记录响应状态
    logger.info(f"⬅️  Response status: {response.status_code}")

    return response

@app.get("/", response_class=HTMLResponse)
async def home():
    template = template_env.get_template("home.html")
    content = template.render(debug_user=None)
    return HTMLResponse(content=content)

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    template = template_env.get_template("login.html")
    content = template.render()
    return HTMLResponse(content=content)

@app.post("/login")
async def login(request: Request):
    data = await request.json()
    account = data.get("account")
    password = data.get("password")
    hash_password = get_password_hash(password)

    if not account or not password:
        logger.warning(f"Login failed: missing credentials from {request.client.host}")
        return JSONResponse(
            {"success": False, "message": "请输入用户名和密码"},
            status_code=400
        )

    result = database.check_users(account, hash_password)
    if not result:
        logger.warning(f"Login failed: user not found - {account}")
        return JSONResponse(
            {"success": False, "message": "用户名或密码错误"},
            status_code=401
        )

    user_id, hashed_password_from_db = result

    if not verify_password(password, hashed_password_from_db):
        logger.warning(f"Login failed: wrong password for user {account}")
        return JSONResponse(
            {"success": False, "message": "用户名或密码错误"},
            status_code=401
        )

    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)))
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

@app.get("/user2", response_class=HTMLResponse)
async def chat_page(request: Request, current_user_id: str = Depends(get_current_user_id)):
    client_ip = request.client.host
    logger.info(f"📋 User {current_user_id} accessing /user2 from IP: {client_ip}")

    if not current_user_id:
        logger.warning(f"🚫 Unauthorized access to /user2 from IP: {client_ip}")
        return RedirectResponse(url="/login")

    template = template_env.get_template("myapp.html")
    characters = database.get_all_characters()
    characters_json = json.dumps([
        {"id": c["id"], "name": c["name"], "trait": c["trait"]}
        for c in characters
    ], ensure_ascii=False)
    content = template.render(characters=characters, characters_json=characters_json, debug_user=current_user_id)
    return HTMLResponse(content=content)

@app.post("/user2/chat")
async def dashscope_chat(
    request: Request,
    current_user_id: str = Depends(get_current_user_id)
):
    client_ip = request.client.host
    if not current_user_id:
        logger.warning(f"🚫 Chat attempt without auth from IP: {client_ip}")
        return JSONResponse({"error": "未授权访问"}, status_code=401)

    logger.info(f"💬 User {current_user_id} sending message from {client_ip}")

    data = await request.json()
    character_id = data.get("character_id")
    user_message = data.get("message")

    if not character_id or not user_message:
        logger.warning(f"User {current_user_id}: Missing params in chat request - {data}")
        return JSONResponse({"error": "缺少必要参数"}, status_code=400)

    character = database.get_character_by_id(character_id)
    if not character:
        logger.warning(f"User {current_user_id}: Invalid character ID {character_id}")
        return JSONResponse({"error": "角色不存在"}, status_code=404)

    system_prompt = f"""
    你正在扮演 {character['name']}。
    人物设定：{character['trait']}
    请始终以这个角色的身份、语气和思维方式回答问题。
    不要暴露你是 AI 的事实。
    """.strip()

    try:
        API_KEY = os.getenv("DASHSCOPE_API_KEY")
        if not API_KEY:
            logger.error("❗ DASHSCOPE_API_KEY is not set")
            return JSONResponse({"error": "API密钥未配置"}, status_code=500)

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = {
            "model": "qwen-plus",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.85,
            "top_p": 0.95,
            "max_tokens": 512,
            "stream": False
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                json=payload,
                headers=headers
            )

        if resp.status_code != 200:
            error_detail = resp.text
            logger.error(f"☁️  Remote API error [{resp.status_code}]: {error_detail}")
            return JSONResponse(
                {"error": f"远程API错误 [{resp.status_code}]", "detail": error_detail},
                status_code=resp.status_code
            )

        result = resp.json()
        reply = result["choices"][0]["message"]["content"].strip()

        database.save_conversation(int(current_user_id), character_id, user_message, reply)

        logger.info(f"🤖 Reply generated for user {current_user_id}, length: {len(reply)} chars")

        return JSONResponse({"reply": reply})

    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        logger.critical(f"💥 Unexpected error in /user2/chat:\n{error_msg}")
        return JSONResponse(
            {"error": f"请求失败: {str(e)}", "detail": str(e)},
            status_code=500
        )

if __name__ == "__main__":
    uvicorn.run("myapp:app", host="127.0.0.1", port=8000, reload=True, log_level="info")
