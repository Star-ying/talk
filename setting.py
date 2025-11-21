# --- 日志配置 ---
import logging
from pathlib import Path

from dotenv import dotenv_values

BASE_DIR = Path(__file__).resolve().parent  # 项目根目录
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)  # 确保 logs 目录存在
LOG_FILE = LOG_DIR / "app.log"

FRONTEND_DIR = BASE_DIR / "frontend"
BACKEND_DIR = BASE_DIR / "backend"
# 加载 .env 文件为全局配置
ENV_CONFIG = dotenv_values(BASE_DIR / ".env")  # 假设 .env 在当前文件同级目录

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

#日志工厂
async def log_middleware(request, call_next):
    logger.info(f"➡️ {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"⬅️ {response.status_code}")
    return response