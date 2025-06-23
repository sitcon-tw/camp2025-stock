from fastapi import APIRouter, HTTPException, status, Depends
from app.services.user_service import UserService, get_user_service
from app.schemas.user import TelegramOAuthRequest, TelegramOAuthResponse
from app.core.security import verify_telegram_auth, create_user_token
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/telegram",
    response_model=TelegramOAuthResponse,
    summary="Telegram OAuth 認證",
    description="使用 Telegram OAuth 進行使用者認證"
)
async def telegram_oauth(
    auth_request: TelegramOAuthRequest,
    user_service: UserService = Depends(get_user_service)
) -> TelegramOAuthResponse:
    """
    Telegram OAuth 認證端點
    
    Args:
        auth_request: Telegram OAuth 認證資料
        user_service: 使用者服務（自動注入）
        
    Returns:
        認證結果和 JWT Token
    """
    try:
        # 驗證 Telegram 認證資料
        auth_data = auth_request.dict()
        
        if not settings.CAMP_TELEGRAM_BOT_TOKEN:
            logger.error("Telegram bot token not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Telegram authentication not configured"
            )
        
        # 驗證 Telegram OAuth 數據
        if not verify_telegram_auth(auth_data.copy(), settings.CAMP_TELEGRAM_BOT_TOKEN):
            logger.warning(f"Invalid Telegram auth data for user {auth_request.id}")
            return TelegramOAuthResponse(
                success=False,
                message="Invalid Telegram authentication data"
            )
        
        # 查找使用者
        user = await user_service.get_user_by_telegram_id(auth_request.id)
        
        if not user:
            logger.warning(f"User not found for Telegram ID: {auth_request.id}")
            return TelegramOAuthResponse(
                success=False,
                message="使用者未註冊，請先透過 Telegram Bot 進行註冊"
            )
        
        # 檢查使用者是否已啟用
        if not user.get("enabled", True):
            logger.warning(f"Disabled user attempted login: {user.get('id')}")
            return TelegramOAuthResponse(
                success=False,
                message="使用者帳號已被停用"
            )
        
        # 建立 JWT Token
        token = create_user_token(user["id"], auth_request.id)
        
        # 準備使用者資訊（移除敏感資料）
        user_info = {
            "id": user["id"],
            "name": user.get("name"),
            "team": user.get("team"),
            "points": user.get("points", 0),
            "telegram_id": user.get("telegram_id")
        }
        
        logger.info(f"Successful Telegram OAuth login for user: {user['id']}")
        
        return TelegramOAuthResponse(
            success=True,
            token=token,
            user=user_info,
            message="登入成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Telegram OAuth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="認證過程發生錯誤"
        )


@router.get("/health")
async def auth_health_check():
    """認證服務健康檢查"""
    return {
        "status": "healthy",
        "service": "Authentication API",
        "telegram_oauth": "enabled" if settings.CAMP_TELEGRAM_BOT_TOKEN else "disabled"
    }