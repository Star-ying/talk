# backend/routes/api.py
from fastapi import APIRouter, Body, Request, Depends, HTTPException
import httpx
import logging

from jwt_handler import get_current_user_id
from backend.crud import character, conversation
from backend.models.conversation import CreateConversationRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI_chat"])
@router.post("/chat")
async def dashscope_chat(
    request: Request,
    data: CreateConversationRequest = Body(...),
    current_user_id: int = Depends(get_current_user_id)
):
    client_ip = request.client.host

    if not current_user_id:
        logger.warning(f"🚫 Chat attempt without auth from IP: {client_ip}")
        raise HTTPException(status_code=401, detail="未授权访问")

    logger.info(f"💬 User {current_user_id} sending message from {client_ip}")

    character_id = data.character_id
    user_message = data.user_message

    if not character_id or not user_message:
        logger.warning(f"User {current_user_id}: Missing params in chat request - {data}")
        raise HTTPException(status_code=400, detail="缺少必要参数")

    characters = await character.get_character_by_id(character_id)
    if not characters:
        logger.warning(f"User {current_user_id}: Invalid character ID {character_id}")
        raise HTTPException(status_code=404, detail="角色不存在")

    system_prompt = f"""
    你正在扮演 {characters['name']}。
    人物设定：{characters['trait']}
    请始终以这个角色的身份、语气和思维方式回答问题。
    不要暴露你是 AI 的事实。
    """.strip()

    try:
        # ★2026-10-24 统一走 dora 兼容网关（OpenAI 协议）；配置来自项目根 .env（ENV_CONFIG）。
        #   读不到 LLM_BASE_URL 时回落原本地 Ollama（localhost:11434/v1），向后兼容。
        #   —— 原硬编码（留痕）：OLLAMA_BASE_URL="http://localhost:11434" / MODEL_NAME="qwen3:8b"
        from setting import ENV_CONFIG
        _base = (ENV_CONFIG.get("LLM_BASE_URL") or "").strip().rstrip("/")
        MODEL_NAME = (ENV_CONFIG.get("LLM_MODEL") or "").strip() or "qwen3.8-flash"
        _key = (ENV_CONFIG.get("LLM_API_KEY") or "").strip()
        if not _base:
            _base = "http://localhost:11434/v1"   # 回落原 Ollama（含 /v1）
        # base 末尾已含 /v1（dora 与 Ollama 回落均是），统一拼 /chat/completions
        _url = _base + "/chat/completions"
        headers = {
            "Content-Type": "application/json"
        }
        if _key:
            headers["Authorization"] = f"Bearer {_key}"   # dora 需；Ollama 忽略无害

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.85,
            "top_p": 0.95,
            "max_tokens": 512,
            "stream": False
        }

        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(
                _url,
                json=payload,
                headers=headers
            )

        if resp.status_code != 200:
            error_detail = resp.text
            logger.error(f"🤖 Ollama API error [{resp.status_code}]: {error_detail}")
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Ollama 错误: {error_detail}"
            )

        result = resp.json()
        logger.info(f"🤖 Raw Ollama response: {result}")

        # 安全访问嵌套字段
        if not result.get("choices"):
            logger.error("❌ Ollama returned no choices in response")
            raise HTTPException(status_code=500, detail="模型未生成任何回复")
        
        choice = result["choices"][0]
        message = choice.get("message", {})
        content = message.get("content", "").strip()

        if not content:
            logger.warning("⚠️ Model returned empty content")
            # 可以设置一个兜底回复
            content = "嗯……我暂时不知道该怎么回答。"

        reply = content

        # 保存对话记录
        await conversation.save_conversation(current_user_id, character_id, user_message, reply)

        logger.info(f"✅ Reply generated for user {current_user_id}, length: {len(reply)} chars")

        return {"reply": reply}

    except httpx.ConnectError:
        logger.critical("❌ 无法连接到 Ollama 服务，请确认 'ollama serve' 是否已启动")
        raise HTTPException(status_code=503, detail="无法连接到本地大模型服务（Ollama）")
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        logger.critical(f"💥 Unexpected error in /api/user/chat:\n{error_msg}")
        raise HTTPException(status_code=500, detail=f"请求失败: {str(e)}")
