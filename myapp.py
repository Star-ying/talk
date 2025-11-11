from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from setting import FRONTEND_DIR
import uvicorn
import logging

# 导入路由
from backend.routes.pages import router as pages_router
from backend.routes.ai import router as ai_router
from backend.routes.web_socket import router as chat_router

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = FastAPI()

    # === 中间件：自动记录访问者 IP ===
    @app.middleware("http")
    async def log_client_ip(request: Request, call_next):
        # 获取客户端真实 IP（考虑反向代理）
        client_ip = request.client.host

        # 如果有反向代理（如 Nginx），可能需要从 X-Forwarded-For 中取
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For 可能是 "client, proxy1, proxy2"
            client_ip = forwarded_for.split(",")[0].strip()

        logger.info(f"🌐 Request from IP: {client_ip} | Path: {request.url.path}")

        # 将 IP 注入 request.state，供后续处理函数使用
        request.state.client_ip = client_ip

        response = await call_next(request)
        return response

    # 挂载静态文件
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")

    # 注册路由
    app.include_router(pages_router)
    app.include_router(ai_router)
    app.include_router(chat_router)

    return app

if __name__ == "__main__":
    # 只需运行在一个端口上即可
    PORT = 8000
    HOST = "0.0.0.0"  # 允许所有 IP 接入（外网可访问）
    
    print(f"🚀 Server starting on http://{HOST}:{PORT}")
    print(f"💡 Allows connections from any IP address (multi-client supported)")

    uvicorn.run(
        "myapp:create_app",  # 使用工厂模式
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info",
        factory=True  # 表示 create_app 是一个工厂函数
    )
