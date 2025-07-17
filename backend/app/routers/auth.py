from fastapi import APIRouter, HTTPException, status, Depends
from app.infrastructure.container import get_user_authentication_service
from app.application.user.authentication_service import UserAuthenticationApplicationService
from app.schemas.user import TelegramOAuthRequest, TelegramOAuthResponse
from app.core.security import create_user_token
from app.core.config_refactored import config
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
    auth_service: UserAuthenticationApplicationService = Depends(get_user_authentication_service)
) -> TelegramOAuthResponse:
    """
    Telegram OAuth 認證端點
    Clean Architecture 原則：控制器只負責 HTTP 處理，業務邏輯委託給應用服務
    
    Args:
        auth_request: Telegram OAuth 認證資料
        auth_service: 使用者認證應用服務（自動注入）
        
    Returns:
        認證結果和 JWT Token
    """
    try:
        # 委託給應用服務處理業務邏輯
        auth_data = auth_request.dict()
        success, user_info, message = await auth_service.telegram_oauth_login(
            auth_data, 
            config.external_services.telegram_bot_token
        )
        
        if not success:
            return TelegramOAuthResponse(
                success=False,
                message=message
            )
        
        # 建立 JWT Token
        token = create_user_token(user_info["id"], auth_request.id)
        
        return TelegramOAuthResponse(
            success=True,
            token=token,
            user=user_info,
            message=message
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
        "telegram_oauth": "enabled"
    }