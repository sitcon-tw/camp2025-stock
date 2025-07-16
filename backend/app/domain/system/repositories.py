"""
System Domain Repositories (Interfaces)
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from bson import ObjectId
from .entities import Student, UserDebt
from ..common.repositories import Repository, SpecificationRepository


class StudentRepository(Repository[Student], SpecificationRepository[Student]):
    """學生存儲庫接口"""
    
    @abstractmethod
    async def find_by_student_id(self, student_id: str) -> Optional[Student]:
        """根據學生 ID 查找學生"""
        pass
    
    @abstractmethod
    async def find_by_telegram_id(self, telegram_id: int) -> Optional[Student]:
        """根據 Telegram ID 查找學生"""
        pass
    
    @abstractmethod
    async def find_by_group_id(self, group_id: str) -> List[Student]:
        """根據群組 ID 查找學生"""
        pass
    
    @abstractmethod
    async def find_active_students(self, skip: int = 0, limit: int = 100) -> List[Student]:
        """查找活躍學生"""
        pass
    
    @abstractmethod
    async def count_active_students(self) -> int:
        """計算活躍學生數量"""
        pass


class UserDebtRepository(Repository[UserDebt], SpecificationRepository[UserDebt]):
    """使用者債務存儲庫接口"""
    
    @abstractmethod
    async def find_by_user_id(self, user_id: ObjectId) -> List[UserDebt]:
        """根據使用者 ID 查找債務"""
        pass
    
    @abstractmethod
    async def find_active_debts(self, skip: int = 0, limit: int = 100) -> List[UserDebt]:
        """查找活躍債務"""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[UserDebt]:
        """根據狀態查找債務"""
        pass
    
    @abstractmethod
    async def calculate_total_debt(self, user_id: ObjectId) -> int:
        """計算使用者總債務"""
        pass
    
    @abstractmethod
    async def mark_as_resolved(self, debt_id: ObjectId, resolved_by: ObjectId) -> bool:
        """標記債務為已解決"""
        pass