"""
Trading Domain Entities
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any, List
from bson import ObjectId
from dataclasses import dataclass
from enum import Enum

from ..common.events import AggregateRoot, OrderCreatedEvent, OrderExecutedEvent
from ..common.exceptions import (
    ValidationException, BusinessRuleException, InsufficientResourceException
)
from ..common.value_objects import Money, Quantity, Price, StockSymbol, OrderPrice, OrderQuantity


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


class StockType(Enum):
    """股票類型"""
    NORMAL = "normal"  # 普通股票
    IPO = "ipo"  # IPO 股票
    SPECIAL = "special"  # 特殊股票


class Stock(AggregateRoot):
    """
    股票聚合根
    管理股票的基本資訊、價格和供應量
    """
    
    def __init__(
        self,
        symbol: str,
        name: str,
        current_price: int,
        available_shares: int,
        total_shares: int,
        stock_type: StockType = StockType.NORMAL,
        min_price: int = 1,
        max_price: int = 1000000,
        id: Optional[ObjectId] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        super().__init__()
        self.id = id
        self.symbol = symbol
        self.name = name
        self.current_price = current_price
        self.available_shares = available_shares
        self.total_shares = total_shares
        self.stock_type = stock_type
        self.min_price = min_price
        self.max_price = max_price
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        
        # 驗證股票資料
        self._validate()
    
    def _validate(self) -> None:
        """驗證股票資料"""
        if not self.symbol or len(self.symbol) > 10:
            raise ValidationException("Symbol must be 1-10 characters", "symbol", self.symbol)
        
        if not self.name or len(self.name) > 100:
            raise ValidationException("Name must be 1-100 characters", "name", self.name)
        
        if self.current_price < self.min_price or self.current_price > self.max_price:
            raise ValidationException(
                f"Price must be between {self.min_price} and {self.max_price}", 
                "current_price", self.current_price
            )
        
        if self.available_shares < 0:
            raise ValidationException("Available shares cannot be negative", "available_shares", self.available_shares)
        
        if self.total_shares < self.available_shares:
            raise ValidationException("Total shares cannot be less than available shares", "total_shares", self.total_shares)
    
    def update_price(self, new_price: int, reason: str = "") -> None:
        """更新股票價格"""
        if new_price < self.min_price or new_price > self.max_price:
            raise ValidationException(
                f"Price must be between {self.min_price} and {self.max_price}", 
                "new_price", new_price
            )
        
        old_price = self.current_price
        self.current_price = new_price
        self.updated_at = datetime.utcnow()
        
        # 增加版本號
        self.increment_version()
        
        # 可以發布價格變更事件
        # self.add_domain_event(PriceChangedEvent(...))
    
    def update_shares(self, available_shares: int) -> None:
        """更新可用股數"""
        if available_shares < 0:
            raise ValidationException("Available shares cannot be negative", "available_shares", available_shares)
        
        if available_shares > self.total_shares:
            raise ValidationException("Available shares cannot exceed total shares", "available_shares", available_shares)
        
        self.available_shares = available_shares
        self.updated_at = datetime.utcnow()
        
        # 增加版本號
        self.increment_version()
    
    def can_buy(self, quantity: int) -> bool:
        """檢查是否可以購買指定數量"""
        return self.available_shares >= quantity
    
    def reserve_shares(self, quantity: int) -> None:
        """預留股票（下單時使用）"""
        if not self.can_buy(quantity):
            raise InsufficientResourceException(
                f"Insufficient shares for {self.symbol}",
                "shares",
                quantity,
                self.available_shares
            )
        
        self.available_shares -= quantity
        self.updated_at = datetime.utcnow()
        
        # 增加版本號
        self.increment_version()
    
    def release_shares(self, quantity: int) -> None:
        """釋放股票（取消訂單時使用）"""
        if self.available_shares + quantity > self.total_shares:
            raise BusinessRuleException("Cannot release more shares than total", "excessive_release")
        
        self.available_shares += quantity
        self.updated_at = datetime.utcnow()
        
        # 增加版本號
        self.increment_version()
    
    def calculate_total_value(self, quantity: int) -> Money:
        """計算總價值"""
        return Money(self.current_price * quantity)
    
    def get_market_cap(self) -> Money:
        """獲取市值"""
        return Money(self.current_price * self.total_shares)
    
    def get_availability_ratio(self) -> float:
        """獲取可用股票比率"""
        if self.total_shares == 0:
            return 0.0
        return self.available_shares / self.total_shares
    
    def is_available(self) -> bool:
        """股票是否可用"""
        return self.available_shares > 0
    
    def is_ipo(self) -> bool:
        """是否為 IPO 股票"""
        return self.stock_type == StockType.IPO
    
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


class StockOrder(AggregateRoot):
    """
    股票訂單聚合根
    管理訂單的生命週期和狀態變更
    """
    
    def __init__(
        self,
        user_id: ObjectId,
        symbol: str,
        order_type: OrderType,
        quantity: int,
        price: int,
        id: Optional[ObjectId] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        super().__init__()
        self.id = id
        self.user_id = user_id
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.price = price
        self.total_amount = quantity * price
        self.filled_quantity = 0
        self.remaining_quantity = quantity
        self.status = OrderStatus.PENDING
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        
        # 驗證訂單資料
        self._validate()
        
        # 發布訂單創建事件
        self.add_domain_event(OrderCreatedEvent(
            event_id="",
            occurred_at=datetime.utcnow(),
            order_id=str(self.id) if self.id else "",
            user_id=str(self.user_id),
            symbol=self.symbol,
            order_type=self.order_type.value,
            quantity=self.quantity,
            price=self.price
        ))
    
    def _validate(self) -> None:
        """驗證訂單資料"""
        if not self.user_id:
            raise ValidationException("User ID is required", "user_id")
        
        if not self.symbol:
            raise ValidationException("Symbol is required", "symbol")
        
        if self.quantity <= 0:
            raise ValidationException("Quantity must be positive", "quantity", self.quantity)
        
        if self.price <= 0:
            raise ValidationException("Price must be positive", "price", self.price)
        
        if self.quantity > 1000000:
            raise ValidationException("Quantity cannot exceed 1,000,000", "quantity", self.quantity)
        
        if self.price > 1000000:
            raise ValidationException("Price cannot exceed 1,000,000", "price", self.price)
    
    def fill_order(self, quantity: int, execution_price: int) -> None:
        """填充訂單"""
        if not self.is_active():
            raise BusinessRuleException("Cannot fill inactive order", "order_inactive")
        
        if quantity <= 0:
            raise ValidationException("Fill quantity must be positive", "quantity", quantity)
        
        if quantity > self.remaining_quantity:
            raise BusinessRuleException("Fill quantity exceeds remaining quantity", "excessive_fill")
        
        # 更新訂單狀態
        self.filled_quantity += quantity
        self.remaining_quantity -= quantity
        self.updated_at = datetime.utcnow()
        
        # 更新訂單狀態
        if self.remaining_quantity == 0:
            self.status = OrderStatus.FILLED
        elif self.filled_quantity > 0:
            self.status = OrderStatus.PARTIAL_FILLED
        
        # 發布訂單執行事件
        self.add_domain_event(OrderExecutedEvent(
            event_id="",
            occurred_at=datetime.utcnow(),
            order_id=str(self.id) if self.id else "",
            user_id=str(self.user_id),
            symbol=self.symbol,
            executed_quantity=quantity,
            executed_price=execution_price,
            total_amount=quantity * execution_price
        ))
        
        # 增加版本號
        self.increment_version()
    
    def cancel_order(self) -> None:
        """取消訂單"""
        if not self.is_active():
            raise BusinessRuleException("Cannot cancel inactive order", "order_inactive")
        
        self.status = OrderStatus.CANCELLED
        self.updated_at = datetime.utcnow()
        
        # 增加版本號
        self.increment_version()
    
    def is_active(self) -> bool:
        """檢查訂單是否活躍"""
        return self.status in [OrderStatus.PENDING, OrderStatus.PARTIAL_FILLED]
    
    def is_buy_order(self) -> bool:
        """是否為買單"""
        return self.order_type == OrderType.BUY
    
    def is_sell_order(self) -> bool:
        """是否為賣單"""
        return self.order_type == OrderType.SELL
    
    def is_fully_filled(self) -> bool:
        """是否已完全成交"""
        return self.status == OrderStatus.FILLED
    
    def is_partially_filled(self) -> bool:
        """是否已部分成交"""
        return self.status == OrderStatus.PARTIAL_FILLED
    
    def is_cancelled(self) -> bool:
        """是否已取消"""
        return self.status == OrderStatus.CANCELLED
    
    def get_fill_ratio(self) -> float:
        """獲取成交比率"""
        if self.quantity == 0:
            return 0.0
        return self.filled_quantity / self.quantity
    
    def get_remaining_value(self) -> Money:
        """獲取剩餘價值"""
        return Money(self.remaining_quantity * self.price)
    
    def get_filled_value(self) -> Money:
        """獲取已成交價值"""
        return Money(self.filled_quantity * self.price)
    
    def get_total_value(self) -> Money:
        """獲取總價值"""
        return Money(self.total_amount)
    
    def can_match_with(self, other_order: 'StockOrder') -> bool:
        """檢查是否可以與另一個訂單匹配"""
        if not self.is_active() or not other_order.is_active():
            return False
        
        if self.symbol != other_order.symbol:
            return False
        
        if self.order_type == other_order.order_type:
            return False
        
        if self.user_id == other_order.user_id:
            return False
        
        # 價格匹配檢查
        if self.is_buy_order() and other_order.is_sell_order():
            return self.price >= other_order.price
        elif self.is_sell_order() and other_order.is_buy_order():
            return self.price <= other_order.price
        
        return False
    
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


class UserStock:
    """
    使用者股票持有實體
    管理使用者的股票投資組合
    """
    
    def __init__(
        self,
        user_id: ObjectId,
        symbol: str,
        quantity: int = 0,
        average_price: int = 0,
        id: Optional[ObjectId] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.user_id = user_id
        self.symbol = symbol
        self.quantity = quantity
        self.average_price = average_price
        self.total_value = quantity * average_price
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        
        # 驗證資料
        self._validate()
    
    def _validate(self) -> None:
        """驗證股票持有資料"""
        if not self.user_id:
            raise ValidationException("User ID is required", "user_id")
        
        if not self.symbol:
            raise ValidationException("Symbol is required", "symbol")
        
        if self.quantity < 0:
            raise ValidationException("Quantity cannot be negative", "quantity", self.quantity)
        
        if self.average_price < 0:
            raise ValidationException("Average price cannot be negative", "average_price", self.average_price)
    
    def add_shares(self, quantity: int, purchase_price: int) -> None:
        """增加股票持有"""
        if quantity <= 0:
            raise ValidationException("Quantity must be positive", "quantity", quantity)
        
        if purchase_price <= 0:
            raise ValidationException("Purchase price must be positive", "purchase_price", purchase_price)
        
        # 計算新的平均價格
        total_cost = self.quantity * self.average_price + quantity * purchase_price
        self.quantity += quantity
        self.average_price = total_cost // self.quantity if self.quantity > 0 else 0
        self.total_value = self.quantity * self.average_price
        self.updated_at = datetime.utcnow()
        
        # 重新驗證
        self._validate()
    
    def remove_shares(self, quantity: int) -> bool:
        """減少股票持有"""
        if quantity <= 0:
            raise ValidationException("Quantity must be positive", "quantity", quantity)
        
        if self.quantity < quantity:
            return False
        
        self.quantity -= quantity
        # 平均價格保持不變
        self.total_value = self.quantity * self.average_price
        self.updated_at = datetime.utcnow()
        
        # 重新驗證
        self._validate()
        return True
    
    def can_sell(self, quantity: int) -> bool:
        """檢查是否可以賣出指定數量"""
        return self.quantity >= quantity
    
    def calculate_profit_loss(self, current_price: int) -> Money:
        """計算損益"""
        current_value = self.quantity * current_price
        cost_value = self.quantity * self.average_price
        return Money(current_value - cost_value)
    
    def calculate_current_value(self, current_price: int) -> Money:
        """計算當前價值"""
        return Money(self.quantity * current_price)
    
    def calculate_cost_basis(self) -> Money:
        """計算成本基礎"""
        return Money(self.total_value)
    
    def get_profit_loss_percentage(self, current_price: int) -> float:
        """獲取損益百分比"""
        if self.average_price == 0:
            return 0.0
        return ((current_price - self.average_price) / self.average_price) * 100
    
    def is_profitable(self, current_price: int) -> bool:
        """是否盈利"""
        return current_price > self.average_price
    
    def has_position(self) -> bool:
        """是否有持倉"""
        return self.quantity > 0
    
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