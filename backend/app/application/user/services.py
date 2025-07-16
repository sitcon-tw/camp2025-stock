"""
User Application Services
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.domain.user.entities import User, PointLog
from app.domain.user.repositories import UserRepository, PointLogRepository
from app.domain.user.services import UserDomainService
from app.shared.exceptions import DomainException, ValidationException
import logging

logger = logging.getLogger(__name__)


class UserApplicationService:
    """使用者應用服務"""
    
    def __init__(self, user_repository: UserRepository, point_log_repository: PointLogRepository):
        self.user_repository = user_repository
        self.point_log_repository = point_log_repository
        self.domain_service = UserDomainService(user_repository, point_log_repository)
    
    async def login_user(self, telegram_id: int, username: str) -> Dict[str, Any]:
        """使用者登入"""
        try:
            # 查找現有使用者
            user = await self.user_repository.find_by_telegram_id(telegram_id)
            
            if not user:
                # 創建新使用者
                user = await self.domain_service.create_user(telegram_id, username)
                logger.info(f"Created new user: {user.id}")
            
            # 返回使用者資訊
            return {
                "success": True,
                "user_id": str(user.id),
                "username": user.username,
                "points": user.points,
                "message": "登入成功"
            }
            
        except DomainException as e:
            logger.error(f"Domain error during login: {e}")
            return {
                "success": False,
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error during login: {e}")
            return {
                "success": False,
                "message": "登入失敗，請稍後再試"
            }
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """獲取使用者資料"""
        try:
            if not ObjectId.is_valid(user_id):
                raise ValidationException("無效的使用者 ID")
            
            user = await self.user_repository.find_by_id(ObjectId(user_id))
            if not user:
                raise DomainException("使用者不存在")
            
            return {
                "success": True,
                "user": {
                    "id": str(user.id),
                    "telegram_id": user.telegram_id,
                    "username": user.username,
                    "points": user.points,
                    "student_id": user.student_id,
                    "real_name": user.real_name,
                    "group_id": user.group_id,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                }
            }
            
        except DomainException as e:
            logger.error(f"Domain error getting user profile: {e}")
            return {
                "success": False,
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error getting user profile: {e}")
            return {
                "success": False,
                "message": "獲取使用者資料失敗"
            }
    
    async def transfer_points(self, from_user_id: str, to_user_id: str, amount: int, description: str = "") -> Dict[str, Any]:
        """轉帳點數"""
        try:
            if not ObjectId.is_valid(from_user_id) or not ObjectId.is_valid(to_user_id):
                raise ValidationException("無效的使用者 ID")
            
            if amount <= 0:
                raise ValidationException("轉帳金額必須大於 0")
            
            success = await self.domain_service.transfer_points(
                ObjectId(from_user_id),
                ObjectId(to_user_id),
                amount,
                description
            )
            
            if success:
                return {
                    "success": True,
                    "message": "轉帳成功"
                }
            else:
                return {
                    "success": False,
                    "message": "轉帳失敗"
                }
                
        except DomainException as e:
            logger.error(f"Domain error during transfer: {e}")
            return {
                "success": False,
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error during transfer: {e}")
            return {
                "success": False,
                "message": "轉帳失敗，請稍後再試"
            }
    
    async def get_point_history(self, user_id: str, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """獲取點數歷史"""
        try:
            if not ObjectId.is_valid(user_id):
                raise ValidationException("無效的使用者 ID")
            
            logs = await self.domain_service.get_user_point_history(ObjectId(user_id), skip, limit)
            
            return {
                "success": True,
                "logs": [
                    {
                        "id": str(log.id),
                        "change_type": log.change_type,
                        "amount": log.amount,
                        "description": log.description,
                        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                        "related_user_id": str(log.related_user_id) if log.related_user_id else None
                    }
                    for log in logs
                ]
            }
            
        except DomainException as e:
            logger.error(f"Domain error getting point history: {e}")
            return {
                "success": False,
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error getting point history: {e}")
            return {
                "success": False,
                "message": "獲取點數歷史失敗"
            }
    
    async def add_points_to_user(self, user_id: str, amount: int, description: str = "", change_type: str = "admin_add") -> Dict[str, Any]:
        """給使用者增加點數（管理員功能）"""
        try:
            if not ObjectId.is_valid(user_id):
                raise ValidationException("無效的使用者 ID")
            
            if amount <= 0:
                raise ValidationException("增加點數必須大於 0")
            
            success = await self.domain_service.add_points(
                ObjectId(user_id),
                amount,
                description,
                change_type
            )
            
            if success:
                return {
                    "success": True,
                    "message": "點數增加成功"
                }
            else:
                return {
                    "success": False,
                    "message": "點數增加失敗"
                }
                
        except DomainException as e:
            logger.error(f"Domain error adding points: {e}")
            return {
                "success": False,
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error adding points: {e}")
            return {
                "success": False,
                "message": "點數增加失敗，請稍後再試"
            }
    
    async def list_users(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """列出所有使用者（管理員功能）"""
        try:
            users = await self.user_repository.find_all(skip, limit)
            total_count = await self.user_repository.count()
            
            return {
                "success": True,
                "users": [
                    {
                        "id": str(user.id),
                        "telegram_id": user.telegram_id,
                        "username": user.username,
                        "points": user.points,
                        "student_id": user.student_id,
                        "real_name": user.real_name,
                        "group_id": user.group_id,
                        "created_at": user.created_at.isoformat() if user.created_at else None
                    }
                    for user in users
                ],
                "total_count": total_count,
                "skip": skip,
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"Unexpected error listing users: {e}")
            return {
                "success": False,
                "message": "獲取使用者列表失敗"
            }