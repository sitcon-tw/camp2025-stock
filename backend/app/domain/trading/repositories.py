"""
Trading Domain Repositories (Interfaces)
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from bson import ObjectId
from .entities import Stock, StockOrder, UserStock, OrderStatus, OrderType
from datetime import datetime
from ..common.repositories import Repository, SpecificationRepository


class StockRepository(Repository[Stock], SpecificationRepository[Stock]):
    """股票存儲庫接口"""
    
    @abstractmethod
    async def find_by_symbol(self, symbol: str) -> Optional[Stock]:
        """根據股票代碼查找股票"""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Stock]:
        """查找所有股票"""
        pass
    
    @abstractmethod
    async def save(self, stock: Stock) -> Stock:
        """儲存股票"""
        pass
    
    @abstractmethod
    async def update(self, stock: Stock) -> bool:
        """更新股票"""
        pass
    
    @abstractmethod
    async def delete(self, symbol: str) -> bool:
        """刪除股票"""
        pass


class OrderRepository(Repository[StockOrder], SpecificationRepository[StockOrder]):
    """訂單存儲庫接口"""
    
    @abstractmethod
    async def find_by_id(self, order_id: ObjectId) -> Optional[StockOrder]:
        """根據訂單 ID 查找訂單"""
        pass
    
    @abstractmethod
    async def find_by_user_id(self, user_id: ObjectId, skip: int = 0, limit: int = 100) -> List[StockOrder]:
        """根據使用者 ID 查找訂單"""
        pass
    
    @abstractmethod
    async def find_by_symbol(self, symbol: str, skip: int = 0, limit: int = 100) -> List[StockOrder]:
        """根據股票代碼查找訂單"""
        pass
    
    @abstractmethod
    async def find_active_orders(self, symbol: str = None) -> List[StockOrder]:
        """查找活躍訂單"""
        pass
    
    @abstractmethod
    async def find_by_user_and_symbol(self, user_id: ObjectId, symbol: str) -> List[StockOrder]:
        """根據使用者和股票代碼查找訂單"""
        pass
    
    @abstractmethod
    async def save(self, order: StockOrder) -> StockOrder:
        """儲存訂單"""
        pass
    
    @abstractmethod
    async def update(self, order: StockOrder) -> bool:
        """更新訂單"""
        pass
    
    @abstractmethod
    async def delete(self, order_id: ObjectId) -> bool:
        """刪除訂單"""
        pass


class UserStockRepository(Repository[UserStock], SpecificationRepository[UserStock]):
    """使用者股票持有存儲庫接口"""
    
    @abstractmethod
    async def find_by_user_id(self, user_id: ObjectId) -> List[UserStock]:
        """根據使用者 ID 查找股票持有"""
        pass
    
    @abstractmethod
    async def find_by_user_and_symbol(self, user_id: ObjectId, symbol: str) -> Optional[UserStock]:
        """根據使用者和股票代碼查找股票持有"""
        pass
    
    @abstractmethod
    async def save(self, user_stock: UserStock) -> UserStock:
        """儲存使用者股票持有"""
        pass
    
    @abstractmethod
    async def update(self, user_stock: UserStock) -> bool:
        """更新使用者股票持有"""
        pass
    
    @abstractmethod
    async def delete(self, user_id: ObjectId, symbol: str) -> bool:
        """刪除使用者股票持有"""
        pass
    
    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[UserStock]:
        """查找所有使用者股票持有"""
        pass


class TradeRepository(ABC):
    """交易記錄存儲庫接口"""
    
    @abstractmethod
    async def find_recent_trades_with_user_info(self, limit: int) -> List[Dict[str, Any]]:
        """查找最近的交易記錄並包含使用者資訊"""
        pass
    
    @abstractmethod
    async def find_recent_trades(self, limit: int) -> List[Dict[str, Any]]:
        """查找最近的交易記錄"""
        pass
    
    @abstractmethod
    async def find_trades_after(self, start_time: datetime) -> List[Dict[str, Any]]:
        """查找指定時間後的交易記錄"""
        pass
    
    @abstractmethod
    async def find_user_buy_trades(self, user_id: ObjectId) -> List[Dict[str, Any]]:
        """查找使用者的買入交易記錄"""
        pass
    
    @abstractmethod
    async def find_by_user_id(self, user_id: ObjectId, limit: int = 100) -> List[Dict[str, Any]]:
        """根據使用者 ID 查找交易記錄"""
        pass