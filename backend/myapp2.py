import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader
import json
from dotenv import load_dotenv
from pathlib import Path
import os
from openai import OpenAI
import uvicorn

# 导入数据库操作
import database

BASE_DIR = Path(__file__).resolve().parent.parent  #主文件夹地址
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI()
load_dotenv(dotenv_path= BASE_DIR / r"backend\.env")

templates = Jinja2Templates(directory=str(FRONTEND_DIR))

# 挂载静态资源
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# Jinja2 模板引擎（用于渲染 HTML）
template_env = Environment(loader=FileSystemLoader(str(FRONTEND_DIR)))

@app.get("/", response_class=HTMLResponse)
async def home(): #挂载网页，连接前端
    template = template_env.get_template("myapp.html")
    characters = database.get_all_characters()
    characters_json = json.dumps([
        {"id": c["id"], "name": c["name"], "trait": c["trait"]}
        for c in characters
    ], ensure_ascii=False)
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

    # ✅ 使用 DeepSeek API 进行推理
    try:
        #本地模型调用
        """ 
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
            response = requests.post("https://api.deepseek.com/v1/chat/completions", ...)
            reply = response.json()["choices"][0]["message"]["content"]

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
        """
        API_KEY = os.getenv("DASHSCOPE_API_KEY")
        if not API_KEY:
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

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=30.0
            )

        if response.status_code != 200:
            error_detail = response.text
            return JSONResponse(
                {"error": f"远程API错误 [{response.status_code}]", "detail": error_detail},
                status_code=response.status_code
            )

        result = response.json()
        reply = result["choices"][0]["message"]["content"].strip()

        # 保存对话记录
        database.save_conversation(character_id, user_message, reply)

        return JSONResponse({"reply": reply})

    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        return JSONResponse(
            {"error": f"请求失败: {str(e)}", "detail": error_msg},
            status_code=500
        )


if __name__ == "__main__":
    uvicorn.run("myapp2:app", host="127.0.0.1", port=8000, reload=True)