"""
User Domain Services
"""
from __future__ import annotations
from typing import Optional, List, Tuple
from bson import ObjectId
from .entities import User, PointLog
from .repositories import UserRepository, PointLogRepository
from app.shared.exceptions import DomainException
from app.core.security import verify_telegram_auth


class UserDomainService:
    """使用者領域服務"""
    
    def __init__(self, user_repository: UserRepository, point_log_repository: PointLogRepository):
        self.user_repository = user_repository
        self.point_log_repository = point_log_repository
    
    async def create_user(self, telegram_id: int, username: str, student_id: Optional[str] = None) -> User:
        """創建新使用者"""
        # 檢查是否已存在
        existing_user = await self.user_repository.find_by_telegram_id(telegram_id)
        if existing_user:
            raise DomainException("使用者已存在")
        
        if student_id:
            existing_student = await self.user_repository.find_by_student_id(student_id)
            if existing_student:
                raise DomainException("學生 ID 已被使用")
        
        user = User(
            telegram_id=telegram_id,
            username=username,
            student_id=student_id,
            points=0
        )
        
        return await self.user_repository.save(user)
    
    async def transfer_points(self, from_user_id: ObjectId, to_user_id: ObjectId, amount: int, description: str = "") -> bool:
        """轉帳點數"""
        if amount <= 0:
            raise DomainException("轉帳金額必須大於 0")
        
        if from_user_id == to_user_id:
            raise DomainException("不能轉帳給自己")
        
        # 獲取使用者
        from_user = await self.user_repository.find_by_id(from_user_id)
        to_user = await self.user_repository.find_by_id(to_user_id)
        
        if not from_user or not to_user:
            raise DomainException("使用者不存在")
        
        # 檢查餘額
        if not from_user.has_sufficient_points(amount):
            raise DomainException("餘額不足")
        
        # 執行轉帳
        from_user.deduct_points(amount)
        to_user.add_points(amount)
        
        # 更新使用者
        await self.user_repository.update(from_user)
        await self.user_repository.update(to_user)
        
        # 記錄轉帳日誌
        await self.point_log_repository.save(PointLog(
            user_id=from_user_id,
            change_type="transfer_out",
            amount=-amount,
            description=description,
            related_user_id=to_user_id
        ))
        
        await self.point_log_repository.save(PointLog(
            user_id=to_user_id,
            change_type="transfer_in",
            amount=amount,
            description=description,
            related_user_id=from_user_id
        ))
        
        return True
    
    async def add_points(self, user_id: ObjectId, amount: int, description: str = "", change_type: str = "manual") -> bool:
        """給使用者增加點數"""
        if amount <= 0:
            raise DomainException("增加點數必須大於 0")
        
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise DomainException("使用者不存在")
        
        user.add_points(amount)
        await self.user_repository.update(user)
        
        # 記錄日誌
        await self.point_log_repository.save(PointLog(
            user_id=user_id,
            change_type=change_type,
            amount=amount,
            description=description
        ))
        
        return True
    
    async def deduct_points(self, user_id: ObjectId, amount: int, description: str = "", change_type: str = "manual") -> bool:
        """扣除使用者點數"""
        if amount <= 0:
            raise DomainException("扣除點數必須大於 0")
        
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise DomainException("使用者不存在")
        
        if not user.deduct_points(amount):
            raise DomainException("餘額不足")
        
        await self.user_repository.update(user)
        
        # 記錄日誌
        await self.point_log_repository.save(PointLog(
            user_id=user_id,
            change_type=change_type,
            amount=-amount,
            description=description
        ))
        
        return True
    
    async def get_user_point_history(self, user_id: ObjectId, skip: int = 0, limit: int = 100) -> List[PointLog]:
        """獲取使用者點數歷史"""
        return await self.point_log_repository.find_by_user_id(user_id, skip, limit)
    
    def verify_telegram_oauth(self, auth_data: dict, bot_token: str) -> bool:
        """
        驗證 Telegram OAuth 資料
        委託給核心安全模組處理實際驗證邏輯
        """
        try:
            return verify_telegram_auth(auth_data, bot_token)
        except Exception as e:
            # 記錄驗證失敗的詳細原因
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Telegram OAuth verification failed: {e}")
            logger.debug(f"Auth data keys: {list(auth_data.keys()) if auth_data else 'None'}")
            logger.debug(f"Bot token present: {bool(bot_token)}")
            return False
    
    def validate_user_eligibility(self, user: Optional[User]) -> Tuple[bool, str]:
        """
        驗證使用者登入資格
        領域邏輯：確認使用者存在且狀態正常
        """
        if not user:
            return False, "使用者不存在"
        
        # 檢查使用者是否啟用（如果有 enabled 欄位）
        if hasattr(user, 'enabled') and not user.enabled:
            return False, "帳號已停用"
        
        # 檢查使用者是否有基本資訊
        if not user.username:
            return False, "使用者資料不完整"
        
        return True, "使用者資格驗證通過"
    
    async def authenticate_user(self, username: str, telegram_id: int) -> Optional[User]:
        """
        認證使用者
        根據使用者名稱和 Telegram ID 查找使用者
        """
        # 先嘗試透過 Telegram ID 查找
        user = await self.user_repository.find_by_telegram_id(telegram_id)
        if user and user.username == username:
            return user
        
        # 如果找不到或使用者名稱不符，回傳 None
        return None
    
    async def register_user(self, username: str, telegram_id: int, student_id: Optional[str] = None, real_name: Optional[str] = None) -> str:
        """
        註冊新使用者
        """
        # 檢查是否已存在
        existing_user = await self.user_repository.find_by_telegram_id(telegram_id)
        if existing_user:
            raise ValueError("user_already_exists")
        
        # 創建新使用者
        user = User(
            telegram_id=telegram_id,
            username=username,
            student_id=student_id,
            real_name=real_name,
            points=0
        )
        
        saved_user = await self.user_repository.save(user)
        return str(saved_user.id)