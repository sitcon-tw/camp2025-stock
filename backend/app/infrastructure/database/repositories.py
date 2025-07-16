"""
Infrastructure Layer Repository Implementations
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.core.database import get_database, Collections
from app.domain.user.repositories import UserRepository, PointLogRepository
from app.domain.user.entities import User, PointLog
from app.domain.trading.repositories import StockRepository, OrderRepository, UserStockRepository
from app.domain.trading.entities import Stock, StockOrder, UserStock
import logging

logger = logging.getLogger(__name__)


class MongoUserRepository(UserRepository):
    """MongoDB 使用者存儲庫實現"""
    
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self.db = db or get_database()
    
    async def find_by_id(self, user_id: ObjectId) -> Optional[User]:
        """根據 ID 查找使用者"""
        try:
            data = await self.db[Collections.USERS].find_one({"_id": user_id})
            return User.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Failed to find user by ID {user_id}: {e}")
            return None
    
    async def find_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """根據 Telegram ID 查找使用者"""
        try:
            data = await self.db[Collections.USERS].find_one({"telegram_id": telegram_id})
            return User.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Failed to find user by telegram ID {telegram_id}: {e}")
            return None
    
    async def find_by_student_id(self, student_id: str) -> Optional[User]:
        """根據學生 ID 查找使用者"""
        try:
            data = await self.db[Collections.USERS].find_one({"student_id": student_id})
            return User.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Failed to find user by student ID {student_id}: {e}")
            return None
    
    async def save(self, user: User) -> User:
        """儲存使用者"""
        try:
            data = user.to_dict()
            if user.id is None:
                # 新增使用者
                result = await self.db[Collections.USERS].insert_one(data)
                user.id = result.inserted_id
            else:
                # 更新使用者
                await self.db[Collections.USERS].replace_one({"_id": user.id}, data)
            return user
        except Exception as e:
            logger.error(f"Failed to save user: {e}")
            raise
    
    async def update(self, user: User) -> bool:
        """更新使用者"""
        try:
            data = user.to_dict()
            result = await self.db[Collections.USERS].replace_one({"_id": user.id}, data)
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            return False
    
    async def delete(self, user_id: ObjectId) -> bool:
        """刪除使用者"""
        try:
            result = await self.db[Collections.USERS].delete_one({"_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            return False
    
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """查找所有使用者"""
        try:
            cursor = self.db[Collections.USERS].find().skip(skip).limit(limit)
            users = []
            async for data in cursor:
                users.append(User.from_dict(data))
            return users
        except Exception as e:
            logger.error(f"Failed to find all users: {e}")
            return []
    
    async def count(self) -> int:
        """計算使用者總數"""
        try:
            return await self.db[Collections.USERS].count_documents({})
        except Exception as e:
            logger.error(f"Failed to count users: {e}")
            return 0
    
    async def find_by_group_id(self, group_id: str) -> List[User]:
        """根據群組 ID 查找使用者"""
        try:
            cursor = self.db[Collections.USERS].find({"group_id": group_id})
            users = []
            async for data in cursor:
                users.append(User.from_dict(data))
            return users
        except Exception as e:
            logger.error(f"Failed to find users by group ID: {e}")
            return []


class MongoPointLogRepository(PointLogRepository):
    """MongoDB 點數記錄存儲庫實現"""
    
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self.db = db or get_database()
    
    async def save(self, point_log: PointLog) -> PointLog:
        """儲存點數記錄"""
        try:
            data = point_log.to_dict()
            if point_log.id is None:
                result = await self.db[Collections.POINT_LOGS].insert_one(data)
                point_log.id = result.inserted_id
            else:
                await self.db[Collections.POINT_LOGS].replace_one({"_id": point_log.id}, data)
            return point_log
        except Exception as e:
            logger.error(f"Failed to save point log: {e}")
            raise
    
    async def find_by_user_id(self, user_id: ObjectId, skip: int = 0, limit: int = 100) -> List[PointLog]:
        """根據使用者 ID 查找點數記錄"""
        try:
            cursor = self.db[Collections.POINT_LOGS].find({"user_id": user_id}).sort("timestamp", -1).skip(skip).limit(limit)
            logs = []
            async for data in cursor:
                logs.append(PointLog.from_dict(data))
            return logs
        except Exception as e:
            logger.error(f"Failed to find point logs by user ID: {e}")
            return []
    
    async def find_by_user_id_and_type(self, user_id: ObjectId, change_type: str, skip: int = 0, limit: int = 100) -> List[PointLog]:
        """根據使用者 ID 和變更類型查找點數記錄"""
        try:
            cursor = self.db[Collections.POINT_LOGS].find({
                "user_id": user_id,
                "change_type": change_type
            }).sort("timestamp", -1).skip(skip).limit(limit)
            logs = []
            async for data in cursor:
                logs.append(PointLog.from_dict(data))
            return logs
        except Exception as e:
            logger.error(f"Failed to find point logs by user ID and type: {e}")
            return []
    
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[PointLog]:
        """查找所有點數記錄"""
        try:
            cursor = self.db[Collections.POINT_LOGS].find().sort("timestamp", -1).skip(skip).limit(limit)
            logs = []
            async for data in cursor:
                logs.append(PointLog.from_dict(data))
            return logs
        except Exception as e:
            logger.error(f"Failed to find all point logs: {e}")
            return []
    
    async def delete_by_user_id(self, user_id: ObjectId) -> bool:
        """刪除使用者的所有點數記錄"""
        try:
            result = await self.db[Collections.POINT_LOGS].delete_many({"user_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete point logs by user ID: {e}")
            return False