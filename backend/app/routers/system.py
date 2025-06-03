from fastapi import APIRouter, Depends, HTTPException, status
from app.services.user_service import UserService, get_user_service
from app.schemas.bot import BotUserRegistrationRequest
from app.core.security import verify_bot_token
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class RegistrationResponse(BaseModel):
    """註冊回應"""
    ok: bool
    message: str


@router.post(
    "/users/register",
    response_model=RegistrationResponse,
    summary="學員註冊",
    description="透過驗證碼和姓名註冊新學員"
)
async def register_student(
    request: BotUserRegistrationRequest,
    token_verified: bool = Depends(verify_bot_token),
    user_service: UserService = Depends(get_user_service)
) -> RegistrationResponse:
    """
    學員註冊
    
    Args:
        request: 包含驗證碼(id)和姓名(name)的註冊請求
        token_verified: token 驗證結果（透過 header 傳入）
        
    Returns:
        註冊結果
    """
    try:
        # 將學員註冊請求轉換為標準請求
        from app.schemas.user import UserRegistrationRequest
        
        # 使用驗證碼作為 username，姓名作為顯示名稱
        standard_request = UserRegistrationRequest(
            username=request.id,  # 使用驗證碼作為 username
            email=f"{request.id}@student.local",  # 生成臨時 email
            team=request.name,  # 使用姓名作為 team（可以後續調整）
            activation_code=request.id,  # 使用驗證碼作為啟用代碼
            telegram_id=None
        )
        
        result = await user_service.register_user(standard_request)
        
        if result.success:
            return RegistrationResponse(
                ok=True,
                message="成功註冊"
            )
        else:
            # 如果註冊失敗（例如用戶已存在），也返回成功
            if "已存在" in result.message:
                return RegistrationResponse(
                    ok=True,
                    message="成功註冊"  # 統一返回成功訊息
                )
            else:
                return RegistrationResponse(
                    ok=False,
                    message=result.message
                )
                
    except Exception as e:
        logger.error(f"學員註冊失敗: {str(e)}")
        return RegistrationResponse(
            ok=False,
            message="註冊失敗，請聯繫管理員"
        )
