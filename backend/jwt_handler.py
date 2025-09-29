# backend/jwt_handler.py
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
import os
from dotenv import load_dotenv
from fastapi import Cookie
from jose import jwt, JWTError
from passlib.hash import pbkdf2_sha256
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent  # 项目根目录
FRONTEND_DIR = BASE_DIR / "frontend"
load_dotenv(dotenv_path=BASE_DIR / "backend" / ".env")

# JWT 配置
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("环境变量 SECRET_KEY 未设置")

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


class TokenData(BaseModel):
    user_id: Optional[str] = None


def get_password_hash(password: str) -> str:
    """
    使用 PBKDF2-SHA256 对密码进行哈希。
    默认 rounds=29000（可根据需要调整）
    """
    return pbkdf2_sha256.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    校验明文密码是否与 PBKDF2 哈希匹配。
    passlib 会自动识别 salt 和 rounds。
    """
    return pbkdf2_sha256.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT Token
    :param data: 要编码的数据，例如 {"sub": "123"}
    :param expires_delta: 自定义过期时间
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user_id(access_token: str = Cookie(None)) -> Optional[str]:
    """
    【异步依赖】从 HttpOnly Cookie 中提取 JWT 并解析出用户 ID（即 'sub' 字段）
    用于 FastAPI 的 Depends 注入系统做权限校验。
    :return: 用户 ID 字符串 或 None（未登录或 token 无效）
    """
    if not access_token:
        return None

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None
    except Exception:
        return None  # 捕获其他异常（如篡改、编码错误等）


# ==================== 同步解码函数 ====================

def decode_access_token(token: str) -> Optional[str]:
    """
    【同步函数】解析 JWT token 获取用户 ID。
    适用于中间件、日志记录、非 await 上下文等场景。
    :param token: JWT 字符串
    :return: 用户 ID (str) 或 None（无效/过期/无 sub）
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None
    except Exception:
        return None  # 其他异常也返回 None
