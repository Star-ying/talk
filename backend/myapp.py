import asyncio
from datetime import timedelta
import httpx
import json
import os
from pydantic import BaseModel
from sqlalchemy import text
import torch
import uvicorn
from fastapi import Depends, FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
import logging
from typing import Callable
import subprocess
from jwt_handler import (
    decode_access_token,
    get_current_user_id,
    verify_password,
    get_password_hash,
    create_access_token
)
import database

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
# 存储每个用户的会话状态 { user_id: { "settings": {}, "history": [...] } }
user_conversations = {}
# 默认角色设定模板
DEFAULT_ROLE_SETTING = """
你正在扮演一位聪明、幽默又略带毒舌的程序员助手。
你的名字叫 DeepPy，喜欢用 Python 写代码，讨厌写 Java。
说话风格犀利但有逻辑，偶尔吐槽用户写的烂代码。
不要总是说“好的”，要像真人一样回应。
"""
# 构建输入文本：包含系统提示 + 历史对话
def build_prompt(user_id: str, new_message: str):
    settings = user_conversations[user_id].get("settings", {})
    role_setting = settings.get("role_setting", DEFAULT_ROLE_SETTING)
    max_history = settings.get("max_history", 4)

    # 获取历史记录
    history = user_conversations[user_id]["history"]
    recent_history = history[-max_history:] if len(history) > max_history else history

    # 构造 prompt
    prompt_parts = [
        "<|System|>\n" + role_setting.strip(),
        "<|Conversation|>"
    ]

    for msg in recent_history:
        if msg["role"] == "user":
            prompt_parts.append(f"User: {msg['content']}")
        elif msg["role"] == "ai":
            prompt_parts.append(f"DeepPy: {msg['content']}")

    prompt_parts.append(f"User: {new_message}")
    prompt_parts.append("DeepPy:")  # 输出起始标记

    full_prompt = "\n".join(prompt_parts)
    return full_prompt

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
    
def shutdown_event():
    """在应用关闭时清理资源"""
    global model, tokenizer
    if model is not None:
        del model
    if tokenizer is not None:
        del tokenizer
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    print("👋 Cleaned up model and CUDA cache on shutdown.")

app.add_event_handler("shutdown",shutdown_event)
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

    result = await database.check_users(account, hash_password)
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

@app.get("/loading")
async def loading_page(request: Request, current_user_id: str = Depends(get_current_user_id)):
    client_ip = request.client.host
    logger.info(f"📋 User {current_user_id} accessing /loading from IP: {client_ip}")

    if not current_user_id:
        logger.warning(f"🚫 Unauthorized access to /loading from IP: {client_ip}")
        return RedirectResponse(url="/login")
    try:
        profile = await database.get_user_profile(current_user_id)

        if not profile:
            logger.info(f"User {current_user_id} has no profile, redirecting to /set-role")
            return RedirectResponse(url="/set-role")
        loop = asyncio.get_running_loop()
        loop.create_task(start_load())
        # 显示加载页面
        return templates.TemplateResponse(
            "loading.html",
            {
                "request": request,
                "message": "🧠 正在加载 AI 模型...",
                "redirect_url": "/user1"
            }
        )

    except Exception as e:
        logger.error(f"[ERROR] During /loading: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

@app.get("/user1/model-status")
def get_model_status():
    """
    返回当前模型加载状态
    前端轮询这个接口
    """
    return {
        "loaded": model!=None
    }

@app.get("/set-role")
async def show_set_role_form(request: Request):
    return templates.TemplateResponse("set_role.html", {"request": request})

@app.post("/set-role")
async def save_role_setting(
    request: Request,
    personality: str = Form(...),
    role_setting: str = Form(...),
    current_user_id:str = Depends(get_current_user_id)
):
    client_ip = request.client.host
    logger.info(f"📋 User {current_user_id} accessing /set_role from IP: {client_ip}")

    if not current_user_id:
        logger.warning(f"🚫 Unauthorized access to /set_role from IP: {client_ip}")
        return RedirectResponse(url="/login")
    
    try:
        success = await database.create_or_update_user_profile(current_user_id, personality, role_setting)
        if success:
            logger.info(f"✅ Profile saved for user {current_user_id}")
            return RedirectResponse(url="/loading", status_code=303)

    except Exception as e:
        logger.error(f"[ERROR] Saving profile: {e}")
        return templates.TemplateResponse(
            "set_role.html",
            {"request": request, "error": "保存失败，请重试"},
            status_code=500
        )

@app.get("/user1")
async def chat_page(request: Request, current_user_id: str = Depends(get_current_user_id)):
    return templates.TemplateResponse("myapp1.html", {"request": request})

class ChatRequest(BaseModel):
    message: str

@app.post("/user1/chat")
async def chat_endpoint(
    req: ChatRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    global model, tokenizer
    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="消息不能为空")

    # 确保用户表存在
    await database.ensure_user_tables_exist(current_user_id)

    # === 处理特殊指令 ===
    if message.startswith("/set_role "):
        new_role = message[len("/set_role "):].strip()
        await database.update_user_setting(current_user_id, role_setting=new_role)
        reply = f"✅ 已更新角色设定：\n\n{new_role}"
        await database.save_message_to_db(current_user_id, "system", f"角色设定已修改为：{new_role}")

    elif message == "/reset":
        table_name = await database.get_conversation_table_name(current_user_id)
        async with await database.AsyncSessionLocal() as session:
            await session.execute(text(f"DELETE FROM `{table_name}`"))
            await session.commit()
        reply = "🗑️ 对话历史已清空。"

    elif message == "/default_role":
        await database.update_user_setting(current_user_id, role_setting=DEFAULT_ROLE_SETTING)
        reply = "↩️ 角色设定已恢复默认。"

    elif message == "/info":
        setting = await database.get_user_setting(current_user_id)
        count_result = await database.AsyncSessionLocal().execute(text(f"""
            SELECT COUNT(*) FROM `{await database.get_conversation_table_name(current_user_id)}`
        """))
        msg_count = count_result.scalar()
        reply = (
            f"👤 当前角色简介：\n{setting['role_setting'][:100]}...\n"
            f"📊 历史消息数：{msg_count}\n"
            f"🔧 使用 /set_role 修改角色"
        )

    else:
        # 正常对话流程
        if model is None or tokenizer is None:
            raise HTTPException(status_code=503, detail="模型尚未加载，请稍后再试")

        # 获取用户设定
        setting = await database.get_user_setting(current_user_id)
        role_setting = setting["role_setting"]
        max_history = setting["max_history"]

        # 加载历史
        history = await database.load_history_from_db(current_user_id, max_history)

        # 构建 prompt（复用之前的 build_prompt 函数）
        prompt_parts = [
            "<|System|>\n" + role_setting.strip(),
            "<|Conversation|>"
        ]
        for msg in history:
            if msg["role"] == "user":
                prompt_parts.append(f"User: {msg['content']}")
            elif msg["role"] in ["ai", "system"]:
                prompt_parts.append(f"DeepPy: {msg['content']}")

        prompt_parts.append(f"User: {message}")
        prompt_parts.append("DeepPy:")
        prompt = "\n".join(prompt_parts)

        # 调用模型生成
        try:
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            with torch.no_grad():
                output_ids = model.generate(
                    **inputs,
                    max_new_tokens=256,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.encode("\nUser:", add_special_tokens=False)[0]
                )
            generated = output_ids[0][inputs["input_ids"].shape[1]:]
            reply_text = tokenizer.decode(generated, skip_special_tokens=True).strip()
            reply = reply_text.split("\nUser:")[0].strip().split("<|")[0].strip()
            if not reply:
                reply = "……（沉默是金）"
        except Exception as e:
            print("生成失败:", e)
            reply = "抱歉，我现在脑子有点乱，稍后再试试？"

        # 保存到数据库
        await database.save_message_to_db(current_user_id, "user", message)
        await database.save_message_to_db(current_user_id, "ai", reply)

    return {"reply": reply}

@app.get("/user1/profile")
async def get_profile(user_id: str = Depends(get_current_user_id)):
    profile = await database.get_user_profile(user_id)
    if not profile:
        return {"personality": "", "role_setting": ""}
    return {
        "personality": profile["personality"],
        "role_setting": profile["role_setting"]
    }

@app.get("/user2", response_class=HTMLResponse)
async def chat_page(request: Request, current_user_id: str = Depends(get_current_user_id)):
    client_ip = request.client.host
    logger.info(f"📋 User {current_user_id} accessing /user2 from IP: {client_ip}")

    if not current_user_id:
        logger.warning(f"🚫 Unauthorized access to /user2 from IP: {client_ip}")
        return RedirectResponse(url="/login")

    template = template_env.get_template("myapp2.html")
    characters = await database.get_all_characters()
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

    character = await database.get_character_by_id(character_id)
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

        await database.save_conversation(int(current_user_id), character_id, user_message, reply)

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
    # 获取当前 Python 脚本所在的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 构建 .bat 文件的相对路径（假设 bat 文件和 py 文件在同一目录）
    bat_path = os.path.join(script_dir, "install_deps.bat")

    # 检查文件是否存在
    if not os.path.exists(bat_path):
        raise FileNotFoundError(f"找不到批处理文件: {bat_path}")

    # 使用 subprocess 运行 .bat 文件（注意要使用 shell=True 或直接调用 cmd）
    result = subprocess.run([bat_path], shell=True, encoding='utf-8', cwd=script_dir)

    # 可选：检查返回码
    if result.returncode == 0:
        uvicorn.run("myapp:app", host="127.0.0.1", port=8000, reload=True, log_level="info")
    else:
        print(f"批处理文件执行失败，返回码: {result.returncode}")