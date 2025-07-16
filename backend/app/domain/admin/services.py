"""
Admin Domain Services
"""
from __future__ import annotations
from typing import Optional, List
from bson import ObjectId
from .entities import AdminUser, AdminAction, AdminRole
from ..user.repositories import UserRepository
from app.shared.exceptions import DomainException
import logging

logger = logging.getLogger(__name__)


class AdminDomainService:
    """管理員領域服務"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def give_points_to_user(self, user_id: ObjectId, amount: int, description: str = "") -> bool:
        """給使用者增加點數"""
        if amount <= 0:
            raise DomainException("點數增加量必須大於 0")
        
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise DomainException("使用者不存在")
        
        user.add_points(amount)
        await self.user_repository.update(user)
        
        # 這裡可以添加日誌記錄
        logger.info(f"Admin gave {amount} points to user {user_id}: {description}")
        
        return True
    
    async def deduct_points_from_user(self, user_id: ObjectId, amount: int, description: str = "") -> bool:
        """扣除使用者點數"""
        if amount <= 0:
            raise DomainException("點數扣除量必須大於 0")
        
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise DomainException("使用者不存在")
        
        if not user.deduct_points(amount):
            raise DomainException("使用者餘額不足")
        
        await self.user_repository.update(user)
        
        # 這裡可以添加日誌記錄
        logger.info(f"Admin deducted {amount} points from user {user_id}: {description}")
        
        return True
    
    async def get_user_summary(self, user_id: ObjectId) -> dict:
        """獲取使用者摘要"""
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise DomainException("使用者不存在")
        
        return {
            "id": str(user.id),
            "username": user.username,
            "telegram_id": user.telegram_id,
            "points": user.points,
            "student_id": user.student_id,
            "real_name": user.real_name,
            "group_id": user.group_id,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    
    async def get_all_users_summary(self, skip: int = 0, limit: int = 100) -> List[dict]:
        """獲取所有使用者摘要"""
        users = await self.user_repository.find_all(skip, limit)
        
        return [
            {
                "id": str(user.id),
                "username": user.username,
                "telegram_id": user.telegram_id,
                "points": user.points,
                "student_id": user.student_id,
                "real_name": user.real_name,
                "group_id": user.group_id,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
            for user in users
        ]
    
    async def get_users_count(self) -> int:
        """獲取使用者總數"""
        return await self.user_repository.count()
    
    async def validate_admin_permissions(self, admin_id: str, required_permission: str) -> bool:
        """驗證管理員權限"""
        # 這裡可以實現管理員權限驗證邏輯
        # 目前簡單返回 True，實際實現需要查詢管理員數據庫
        return True