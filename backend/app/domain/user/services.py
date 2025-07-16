"""
User Domain Services
"""
from __future__ import annotations
from typing import Optional, List
from bson import ObjectId
from .entities import User, PointLog
from .repositories import UserRepository, PointLogRepository
from app.shared.exceptions import DomainException


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