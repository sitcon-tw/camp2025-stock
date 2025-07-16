"""
Trading Domain Entities
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId
from dataclasses import dataclass
from enum import Enum


class OrderType(Enum):
    """訂單類型"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """訂單狀態"""
    PENDING = "pending"
    PARTIAL_FILLED = "partial_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"


@dataclass
class Stock:
    """股票實體"""
    symbol: str
    name: str
    current_price: int
    available_shares: int
    total_shares: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def update_price(self, new_price: int) -> None:
        """更新股票價格"""
        self.current_price = new_price
        self.updated_at = datetime.utcnow()
    
    def update_shares(self, available_shares: int) -> None:
        """更新可用股數"""
        self.available_shares = available_shares
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "symbol": self.symbol,
            "name": self.name,
            "current_price": self.current_price,
            "available_shares": self.available_shares,
            "total_shares": self.total_shares,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Stock:
        """從字典創建實體"""
        return cls(
            symbol=data.get("symbol", ""),
            name=data.get("name", ""),
            current_price=data.get("current_price", 0),
            available_shares=data.get("available_shares", 0),
            total_shares=data.get("total_shares", 0),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


@dataclass
class StockOrder:
    """股票訂單實體"""
    id: Optional[ObjectId] = None
    user_id: ObjectId = None
    symbol: str = ""
    order_type: OrderType = OrderType.BUY
    quantity: int = 0
    price: int = 0
    total_amount: int = 0
    filled_quantity: int = 0
    remaining_quantity: int = 0
    status: OrderStatus = OrderStatus.PENDING
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.remaining_quantity == 0:
            self.remaining_quantity = self.quantity
        if self.total_amount == 0:
            self.total_amount = self.quantity * self.price
    
    def fill_order(self, quantity: int) -> None:
        """填充訂單"""
        if quantity > self.remaining_quantity:
            raise ValueError("填充數量超過剩餘數量")
        
        self.filled_quantity += quantity
        self.remaining_quantity -= quantity
        self.updated_at = datetime.utcnow()
        
        if self.remaining_quantity == 0:
            self.status = OrderStatus.FILLED
        elif self.filled_quantity > 0:
            self.status = OrderStatus.PARTIAL_FILLED
    
    def cancel_order(self) -> None:
        """取消訂單"""
        self.status = OrderStatus.CANCELLED
        self.updated_at = datetime.utcnow()
    
    def is_active(self) -> bool:
        """檢查訂單是否活躍"""
        return self.status in [OrderStatus.PENDING, OrderStatus.PARTIAL_FILLED]
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "_id": self.id,
            "user_id": self.user_id,
            "symbol": self.symbol,
            "order_type": self.order_type.value,
            "quantity": self.quantity,
            "price": self.price,
            "total_amount": self.total_amount,
            "filled_quantity": self.filled_quantity,
            "remaining_quantity": self.remaining_quantity,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> StockOrder:
        """從字典創建實體"""
        return cls(
            id=data.get("_id"),
            user_id=data.get("user_id"),
            symbol=data.get("symbol", ""),
            order_type=OrderType(data.get("order_type", "buy")),
            quantity=data.get("quantity", 0),
            price=data.get("price", 0),
            total_amount=data.get("total_amount", 0),
            filled_quantity=data.get("filled_quantity", 0),
            remaining_quantity=data.get("remaining_quantity", 0),
            status=OrderStatus(data.get("status", "pending")),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


@dataclass
class UserStock:
    """使用者股票持有實體"""
    user_id: ObjectId
    symbol: str
    quantity: int
    average_price: int
    total_value: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def add_shares(self, quantity: int, price: int) -> None:
        """增加股票持有"""
        if quantity <= 0:
            raise ValueError("數量必須大於 0")
        
        total_cost = self.quantity * self.average_price + quantity * price
        self.quantity += quantity
        self.average_price = total_cost // self.quantity if self.quantity > 0 else 0
        self.total_value = self.quantity * self.average_price
        self.updated_at = datetime.utcnow()
    
    def remove_shares(self, quantity: int) -> bool:
        """減少股票持有"""
        if quantity <= 0:
            raise ValueError("數量必須大於 0")
        
        if self.quantity < quantity:
            return False
        
        self.quantity -= quantity
        self.total_value = self.quantity * self.average_price
        self.updated_at = datetime.utcnow()
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "user_id": self.user_id,
            "symbol": self.symbol,
            "quantity": self.quantity,
            "average_price": self.average_price,
            "total_value": self.total_value,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UserStock:
        """從字典創建實體"""
        return cls(
            user_id=data.get("user_id"),
            symbol=data.get("symbol", ""),
            quantity=data.get("quantity", 0),
            average_price=data.get("average_price", 0),
            total_value=data.get("total_value", 0),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )