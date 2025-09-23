# backend/main.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader
import json
import asyncio
from dotenv import load_dotenv
from pathlib import Path
import uvicorn
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# 导入数据库操作
import database

BASE_DIR = Path(__file__).resolve().parent.parent  #主文件夹地址
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI()
load_dotenv(dotenv_path= BASE_DIR / r"backend\MyAI.env")

templates = Jinja2Templates(directory=str(FRONTEND_DIR))

# 挂载静态资源
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# Jinja2 模板引擎（用于渲染 HTML）
template_env = Environment(loader=FileSystemLoader(str(FRONTEND_DIR)))

# 全局变量（在 app 启动时加载一次）
model = None
tokenizer = None

def load_model():
    """同步函数：实际加载模型"""
    model_name = str(BASE_DIR / "model\deepseek-coder-1.3b-instruct")
    print("Loading tokenizer...")
    tok = AutoTokenizer.from_pretrained(model_name)
    print("Loading model...")
    m = AutoModelForCausalLM.from_pretrained(
        model_name,
        dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto",
        low_cpu_mem_usage=True
    ).eval()
    return m, tok

async def start_load():
    global model,tokenizer
    """在程序启动时，非阻塞地加载模型"""
    loop = asyncio.get_event_loop()
    # 使用线程池执行同步加载，避免阻塞事件循环
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

app.add_event_handler("startup",start_load)
app.add_event_handler("shutdown",shutdown_event)

@app.get("/", response_class=HTMLResponse)
async def home(): #挂载网页，连接前端
    template = template_env.get_template("myapp.html")
    characters = database.get_all_characters()
    characters_json = json.dumps([{ "id": c["id"], "name": c["name"], "trait": c["trait"] } for c in characters], ensure_ascii=False)
    content = template.render(characters=characters, characters_json=characters_json)
    return HTMLResponse(content=content)

@app.post("/chat")
async def deepseek_chat(request: Request):
    data = await request.json()
    character_id = data.get("character_id")
    user_message = data.get("message")

    # 查询角色信息
    conn = database.get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT name, trait FROM characters WHERE id = %s", (character_id,))
    character = cursor.fetchone()
    conn.close()

    if not character:
        return JSONResponse({"error": "角色不存在"}, status_code=404)

    # 构建系统提示词
    system_prompt = f"""
你正在扮演 {character['name']}。
人物设定：{character['trait']}
请始终以这个角色的身份、语气和思维方式回答问题。
不要暴露你是 AI 的事实。
""".strip()

    # 👇 关键：使用本地模型进行推理
    try:
        # 确保模型已加载
        global model, tokenizer
        if model is None or tokenizer is None:
            return JSONResponse({"error": "模型尚未加载，请先启动模型"}, status_code=500)

        # 构造对话历史（必须使用 chat template）
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        # 使用 tokenizer.apply_chat_template 构造输入文本
        input_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True  # 让模型知道要开始生成 assistant 回复   
        )

        # Tokenize
        inputs = tokenizer(input_text, return_tensors="pt").to(model.device)

        # 生成参数
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.85,
                top_p=0.95,
                do_sample=True,
                repetition_penalty=1.1,
                eos_token_id=tokenizer.eos_token_id,
                pad_token_id=tokenizer.eos_token_id  # 避免 decoder-only 模型 padding 报错
            )

        # 解码输出（去掉输入部分）
        full_response = tokenizer.decode(outputs[0], skip_special_tokens=False)
        
        # 提取 assistant 的回复内容
        # 注意：apply_chat_template 已经添加了 <|assistant|> 标记
        if "<|assistant|>" in full_response:
            reply = full_response.split("<|assistant|>")[-1].strip()
        else:
            reply = full_response[len(input_text):].strip()

        # 清理结尾可能的无关 token
        eot_token = "<|EOT|>"
        if eot_token in reply:
            reply = reply.split(eot_token)[0].strip()

        # 保存对话记录
        database.save_conversation(character_id, user_message, reply)

        return JSONResponse({"reply": reply})

    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()  # 更详细的错误日志
        return JSONResponse({"error": f"推理失败: {str(e)}", "detail": error_msg}, status_code=500)

# 非llama.cpp实现

if __name__ == "__main__":
    uvicorn.run("myapp:app", host="127.0.0.1", port=8000, reload=True)