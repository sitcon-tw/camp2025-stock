# 領域實體 (Domain Entities)
# DDD 原則：封裝業務邏輯和規則的核心對象

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from decimal import Decimal


@dataclass
class User:
    """
    使用者領域實體
    SRP 原則：專注於使用者相關的業務邏輯和狀態管理
    """
    user_id: str
    username: str
    email: str
    team: str
    points: int
    telegram_id: Optional[int] = None
    photo_url: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    
    def can_transfer(self, amount: int) -> bool:
        """檢查是否有足夠點數進行轉帳"""
        return self.points >= amount and amount > 0
    
    def deduct_points(self, amount: int) -> None:
        """扣除點數 - 業務規則：不允許負數"""
        if not self.can_transfer(amount):
            raise ValueError("insufficient_points")
        self.points -= amount
    
    def add_points(self, amount: int) -> None:
        """增加點數 - 業務規則：金額必須為正數"""
        if amount <= 0:
            raise ValueError("invalid_amount")
        self.points += amount


@dataclass
class Stock:
    """
    股票領域實體
    SRP 原則：專注於股票相關的業務邏輯
    """
    user_id: str
    quantity: int
    avg_cost: Decimal
    updated_at: Optional[datetime] = None
    
    def can_sell(self, quantity: int) -> bool:
        """檢查是否有足夠股票可賣出"""
        return self.quantity >= quantity and quantity > 0
    
    def sell_shares(self, quantity: int) -> None:
        """賣出股票 - 業務規則：不允許超賣"""
        if not self.can_sell(quantity):
            raise ValueError("insufficient_stocks")
        self.quantity -= quantity
    
    def buy_shares(self, quantity: int, price: Decimal) -> None:
        """買入股票 - 更新平均成本"""
        if quantity <= 0 or price <= 0:
            raise ValueError("invalid_parameters")
        
        total_cost = self.quantity * self.avg_cost + quantity * price
        self.quantity += quantity
        self.avg_cost = total_cost / self.quantity


@dataclass
class StockOrder:
    """
    股票訂單領域實體
    SRP 原則：專注於訂單狀態和業務邏輯
    """
    order_id: str
    user_id: str
    order_type: str  # market, limit
    side: str  # buy, sell
    quantity: int
    price: Optional[Decimal] = None
    status: str = "pending"  # pending, filled, cancelled
    filled_quantity: int = 0  # 已成交數量
    created_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancel_reason: Optional[str] = None
    
    def can_execute(self, market_price: Optional[Decimal] = None) -> bool:
        """檢查訂單是否可執行"""
        if self.status != "pending":
            return False
        
        if self.order_type == "market":
            return True
        
        if self.order_type == "limit" and self.price and market_price:
            if self.side == "buy":
                return market_price <= self.price
            else:  # sell
                return market_price >= self.price
        
        return False
    
    def execute(self, executed_price: Decimal) -> None:
        """執行訂單"""
        if not self.can_execute():
            raise ValueError("order_cannot_be_executed")
        
        self.status = "filled"
        self.executed_at = datetime.now()
        
        # 對於市價單，記錄實際成交價格
        if self.order_type == "market":
            self.price = executed_price
    
    def can_cancel(self) -> bool:
        """檢查訂單是否可以取消"""
        return self.status in ["pending", "partial", "pending_limit"]
    
    def cancel(self, reason: Optional[str] = None) -> None:
        """取消訂單"""
        if not self.can_cancel():
            raise ValueError(f"order_cannot_be_cancelled_status_{self.status}")
        
        self.status = "cancelled"
        self.cancelled_at = datetime.now()
        self.cancel_reason = reason or "user_cancelled"


@dataclass
class Transfer:
    """
    轉帳領域實體
    SRP 原則：專注於轉帳業務邏輯
    """
    transfer_id: str
    from_user_id: str
    to_user_id: str
    amount: int
    fee: int
    note: Optional[str] = None
    status: str = "pending"
    created_at: Optional[datetime] = None
    
    @staticmethod
    def calculate_fee(amount: int) -> int:
        """計算轉帳手續費 - 業務規則：1% 手續費，最低 1 點"""
        return max(1, amount // 100)
    
    def get_total_deduction(self) -> int:
        """獲取總扣除金額（含手續費）"""
        return self.amount + self.fee
    
    def execute(self) -> None:
        """執行轉帳"""
        if self.status != "pending":
            raise ValueError("transfer_already_processed")
        self.status = "completed"