# Repository 抽象介面
# DIP 原則：定義抽象介面，具體實作由基礎設施層提供
# ISP 原則：分離不同的 repository 介面，避免強制實作不需要的方法

from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import User, Stock, StockOrder, Transfer


class UserRepository(ABC):
    """
    使用者資料存取抽象介面
    DIP 原則：高層模組不依賴低層模組，都依賴抽象
    ISP 原則：只包含使用者相關的方法
    """
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """根據用戶名獲取使用者"""
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """根據ID獲取使用者"""
        pass
    
    @abstractmethod
    async def save(self, user: User) -> None:
        """保存使用者"""
        pass
    
    @abstractmethod
    async def create(self, user: User) -> str:
        """創建新使用者，返回 user_id"""
        pass
    
    @abstractmethod
    async def update_points(self, user_id: str, new_points: int) -> None:
        """更新使用者點數"""
        pass


class StockRepository(ABC):
    """
    股票資料存取抽象介面
    ISP 原則：專注於股票相關操作
    """
    
    @abstractmethod
    async def get_by_user_id(self, user_id: str) -> Optional[Stock]:
        """獲取使用者股票持倉"""
        pass
    
    @abstractmethod
    async def save(self, stock: Stock) -> None:
        """保存股票持倉"""
        pass
    
    @abstractmethod
    async def update_quantity(self, user_id: str, new_quantity: int, new_avg_cost: float) -> None:
        """更新股票數量和平均成本"""
        pass


class StockOrderRepository(ABC):
    """
    股票訂單資料存取抽象介面
    ISP 原則：專注於訂單相關操作
    """
    
    @abstractmethod
    async def create(self, order: StockOrder) -> str:
        """創建新訂單"""
        pass
    
    @abstractmethod
    async def get_by_id(self, order_id: str) -> Optional[StockOrder]:
        """根據ID獲取訂單"""
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: str, limit: int = 20) -> List[StockOrder]:
        """獲取使用者訂單歷史"""
        pass
    
    @abstractmethod
    async def get_pending_orders(self) -> List[StockOrder]:
        """獲取所有待處理訂單"""
        pass
    
    @abstractmethod
    async def update_status(self, order_id: str, status: str, executed_price: Optional[float] = None) -> None:
        """更新訂單狀態"""
        pass


class TransferRepository(ABC):
    """
    轉帳資料存取抽象介面
    ISP 原則：專注於轉帳相關操作
    """
    
    @abstractmethod
    async def create(self, transfer: Transfer) -> str:
        """創建轉帳記錄"""
        pass
    
    @abstractmethod
    async def get_by_id(self, transfer_id: str) -> Optional[Transfer]:
        """根據ID獲取轉帳記錄"""
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: str, limit: int = 20) -> List[Transfer]:
        """獲取使用者轉帳歷史"""
        pass


class MarketConfigRepository(ABC):
    """
    市場設定資料存取抽象介面
    ISP 原則：專注於市場設定操作
    """
    
    @abstractmethod
    async def get_ipo_config(self) -> Optional[dict]:
        """獲取 IPO 設定"""
        pass
    
    @abstractmethod
    async def update_ipo_config(self, config: dict) -> None:
        """更新 IPO 設定"""
        pass
    
    @abstractmethod
    async def get_market_price(self) -> Optional[float]:
        """獲取當前市場價格"""
        pass