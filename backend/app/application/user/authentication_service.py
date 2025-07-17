# 使用者認證應用服務
# 專注於使用者登入和註冊的業務流程

from typing import Optional, Tuple
import logging

from app.core.base_classes import BaseApplicationService
from app.domain.user.services import UserDomainService
from app.domain.user.repositories import UserRepository
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
    
    def __init__(self, user_domain_service: UserDomainService, user_repository: UserRepository):
        super().__init__("UserAuthenticationApplicationService")
        self.user_domain_service = user_domain_service
        self.user_repository = user_repository
    
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
    
    async def telegram_oauth_login(
        self, 
        auth_data: dict, 
        bot_token: str
    ) -> Tuple[bool, Optional[dict], str]:
        """
        Telegram OAuth 登入用例
        協調認證驗證、使用者查找和資格檢查
        
        Returns:
            (success, user_data, message)
        """
        try:
            # 1. 驗證 Telegram OAuth 資料
            logger.debug(f"Received auth data: {auth_data}")
            if not self.user_domain_service.verify_telegram_oauth(auth_data.copy(), bot_token):
                logger.warning(f"Invalid Telegram auth data for user {auth_data.get('id')}")
                return False, None, "Invalid Telegram authentication data"
            
            # 2. 查找使用者
            telegram_id = auth_data.get('id')
            if not telegram_id:
                return False, None, "缺少 Telegram ID"
            
            user = await self.user_repository.get_by_telegram_id(telegram_id)
            
            # 3. 驗證使用者資格
            is_eligible, message = self.user_domain_service.validate_user_eligibility(user)
            if not is_eligible:
                return False, None, message
            
            # 3.5. 取得 photo_url（但不儲存，只用於回傳）
            photo_url = auth_data.get('photo_url')
            
            # 4. 回傳使用者資料
            user_data = {
                "id": str(user.id),
                "username": user.username,
                "real_name": user.real_name,
                "student_id": user.student_id,
                "group_id": user.group_id,
                "points": user.points,
                "photo_url": photo_url
            }
            
            return True, user_data, "登入成功"
            
        except Exception as e:
            logger.error(f"Telegram OAuth login failed: {e}")
            return False, None, f"登入失敗: {str(e)}"