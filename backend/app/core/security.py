from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
import hashlib
import hmac
import urllib.parse

# 密碼加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Token 驗證
security = HTTPBearer()

# 　驗證密碼


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# 密碼 hash
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """建立 JWT Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.CAMP_JWT_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.CAMP_JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """驗證 JWT Token"""
    try:
        payload = jwt.decode(token, settings.CAMP_JWT_SECRET,
                             algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_CAMP_ADMIN_PASSWORD(password: str) -> bool:
    """驗證管理員密碼（簡單版本，實際應該用雜湊）"""
    # TODO: 實際應該用雜湊
    return password == settings.CAMP_ADMIN_PASSWORD


async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """取得目前管理員（依賴注入）"""
    try:
        payload = verify_token(credentials.credentials)
        # 檢查是否為管理員 token
        if payload.get("type") == "admin" or payload.get("sub") == "admin":
            return payload
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not an admin user"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """取得目前使用者（依賴注入）"""
    try:
        payload = verify_token(credentials.credentials)

        # 檢查 token 類型
        token_type = payload.get("type", "user")
        if token_type not in ["user", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        return payload

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_bot_api_key(api_key: str) -> bool:
    """驗證內部 API 金鑰"""
    return api_key == settings.CAMP_INTERNAL_API_KEY


def verify_bot_token(token: str = Header(..., alias="token")) -> bool:
    """BOT API 驗證機制 - 驗證 token"""
    if token != settings.CAMP_INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return True


def verify_telegram_auth(auth_data: dict, bot_token: str) -> bool:
    """驗證 Telegram OAuth 認證資料"""
    # 取得 hash 值
    received_hash = auth_data.pop('hash', None)
    if not received_hash:
        return False

    # 準備驗證字串
    auth_data_items = []
    for key, value in sorted(auth_data.items()):
        auth_data_items.append(f"{key}={value}")

    data_check_string = '\n'.join(auth_data_items)

    # 計算預期的 hash
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    expected_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    return hmac.compare_digest(received_hash, expected_hash)


def create_user_token(user_id: str, telegram_id: int) -> str:
    """為 Telegram 使用者建立 JWT Token"""
    token_data = {
        "user_id": user_id,
        "telegram_id": telegram_id,
        "type": "user"
    }
    return create_access_token(token_data)
