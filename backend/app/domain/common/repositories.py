"""
Common Repository Interfaces and Base Classes
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, TypeVar, Generic
from bson import ObjectId

# 泛型類型定義
T = TypeVar('T')


class Repository(ABC, Generic[T]):
    """
    基礎 Repository 介面
    定義所有 Repository 的共同操作
    """
    
    @abstractmethod
    async def save(self, entity: T) -> T:
        """保存實體"""
        pass
    
    @abstractmethod
    async def find_by_id(self, entity_id: ObjectId) -> Optional[T]:
        """根據 ID 查找實體"""
        pass
    
    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """查找所有實體"""
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        """更新實體"""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: ObjectId) -> bool:
        """刪除實體"""
        pass
    
    @abstractmethod
    async def exists(self, entity_id: ObjectId) -> bool:
        """檢查實體是否存在"""
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """計算實體總數"""
        pass


class ReadOnlyRepository(ABC, Generic[T]):
    """
    只讀 Repository 介面
    用於查詢專用的儲存庫
    """
    
    @abstractmethod
    async def find_by_id(self, entity_id: ObjectId) -> Optional[T]:
        """根據 ID 查找實體"""
        pass
    
    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """查找所有實體"""
        pass
    
    @abstractmethod
    async def exists(self, entity_id: ObjectId) -> bool:
        """檢查實體是否存在"""
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """計算實體總數"""
        pass


class SpecificationRepository(ABC, Generic[T]):
    """
    支援規格模式的 Repository 介面
    """
    
    @abstractmethod
    async def find_by_specification(self, specification: Dict[str, Any]) -> List[T]:
        """根據規格查找實體"""
        pass
    
    @abstractmethod
    async def find_one_by_specification(self, specification: Dict[str, Any]) -> Optional[T]:
        """根據規格查找單一實體"""
        pass
    
    @abstractmethod
    async def count_by_specification(self, specification: Dict[str, Any]) -> int:
        """根據規格計算實體數量"""
        pass


class UnitOfWork(ABC):
    """
    工作單元介面
    用於管理事務邊界
    """
    
    @abstractmethod
    async def begin(self):
        """開始事務"""
        pass
    
    @abstractmethod
    async def commit(self):
        """提交事務"""
        pass
    
    @abstractmethod
    async def rollback(self):
        """回滾事務"""
        pass
    
    @abstractmethod
    async def __aenter__(self):
        """進入上下文管理器"""
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器"""
        pass