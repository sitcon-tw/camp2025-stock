# 使用者認證應用服務
# 專注於使用者登入和註冊的業務流程

from typing import Optional
import logging

from app.core.base_classes import BaseApplicationService
from app.domain.user.services import UserDomainService
from app.schemas.user import (
    UserLoginRequest, UserLoginResponse, 
    UserRegistrationRequest, UserRegistrationResponse
)
from app.core.security import create_access_token

logger = logging.getLogger(__name__)


class UserAuthenticationApplicationService(BaseApplicationService):
    """
    使用者認證應用服務
    SRP 原則：專注於認證相關的應用邏輯
    """
    
    def __init__(self, user_domain_service: UserDomainService):
        super().__init__("UserAuthenticationApplicationService")
        self.user_domain_service = user_domain_service
    
    async def login_user(self, request: UserLoginRequest) -> UserLoginResponse:
        """
        使用者登入用例
        Clean Code 原則：函數名稱清楚表達意圖
        """
        try:
            user = await self.user_domain_service.authenticate_user(
                request.username, request.telegram_id
            )
            
            if not user:
                return UserLoginResponse(
                    success=False,
                    message="使用者不存在或帳號未啟用"
                )
            
            # 產生 JWT Token
            token = create_access_token(data={"sub": user.user_id})
            
            return UserLoginResponse(
                success=True,
                token=token,
                user={
                    "id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "team": user.team,
                    "points": user.points
                }
            )
        except Exception as e:
            logger.error(f"Login failed for user {request.username}: {e}")
            return UserLoginResponse(success=False, message="登入失敗")
    
    async def register_user(self, request: UserRegistrationRequest) -> UserRegistrationResponse:
        """
        使用者註冊用例
        SRP 原則：專注於註冊流程的協調
        """
        try:
            user_id = await self.user_domain_service.register_user(
                request.username, request.email, request.team, request.telegram_id
            )
            
            return UserRegistrationResponse(
                success=True,
                message="註冊成功",
                user_id=user_id
            )
        except ValueError as e:
            error_messages = {
                "user_already_exists": "使用者名稱已存在",
            }
            message = error_messages.get(str(e), "註冊失敗")
            return UserRegistrationResponse(success=False, message=message)
        except Exception as e:
            logger.error(f"Registration failed for user {request.username}: {e}")
            return UserRegistrationResponse(success=False, message="註冊失敗")