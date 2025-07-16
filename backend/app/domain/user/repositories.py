"""
User Domain Repositories (Interfaces)
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from bson import ObjectId
from .entities import User, PointLog


class UserRepository(ABC):
    """使用者存儲庫接口"""
    
    @abstractmethod
    async def find_by_id(self, user_id: ObjectId) -> Optional[User]:
        """根據 ID 查找使用者"""
        pass
    
    @abstractmethod
    async def find_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """根據 Telegram ID 查找使用者"""
        pass
    
    @abstractmethod
    async def find_by_student_id(self, student_id: str) -> Optional[User]:
        """根據學生 ID 查找使用者"""
        pass
    
    @abstractmethod
    async def save(self, user: User) -> User:
        """儲存使用者"""
        pass
    
    @abstractmethod
    async def update(self, user: User) -> bool:
        """更新使用者"""
        pass
    
    @abstractmethod
    async def delete(self, user_id: ObjectId) -> bool:
        """刪除使用者"""
        pass
    
    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """查找所有使用者"""
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """計算使用者總數"""
        pass
    
    @abstractmethod
    async def find_by_group_id(self, group_id: str) -> List[User]:
        """根據群組 ID 查找使用者"""
        pass


class PointLogRepository(ABC):
    """點數記錄存儲庫接口"""
    
    @abstractmethod
    async def save(self, point_log: PointLog) -> PointLog:
        """儲存點數記錄"""
        pass
    
    @abstractmethod
    async def find_by_user_id(self, user_id: ObjectId, skip: int = 0, limit: int = 100) -> List[PointLog]:
        """根據使用者 ID 查找點數記錄"""
        pass
    
    @abstractmethod
    async def find_by_user_id_and_type(self, user_id: ObjectId, change_type: str, skip: int = 0, limit: int = 100) -> List[PointLog]:
        """根據使用者 ID 和變更類型查找點數記錄"""
        pass
    
    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[PointLog]:
        """查找所有點數記錄"""
        pass
    
    @abstractmethod
    async def delete_by_user_id(self, user_id: ObjectId) -> bool:
        """刪除使用者的所有點數記錄"""
        pass