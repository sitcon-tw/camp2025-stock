"""
Value Objects
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict
from dataclasses import dataclass


class ValueObject(ABC):
    """
    值物件基類
    值物件的特性：
    1. 不可變性
    2. 基於值的相等性
    3. 沒有身份標識
    """
    
    def __eq__(self, other: Any) -> bool:
        """基於值的相等性比較"""
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__
    
    def __hash__(self) -> int:
        """基於值的哈希"""
        return hash(tuple(sorted(self.__dict__.items())))
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> ValueObject:
        """從字典創建值物件"""
        pass


@dataclass(frozen=True)
class Money(ValueObject):
    """金額值物件"""
    amount: int
    currency: str = "TWD"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        if not self.currency:
            raise ValueError("Currency cannot be empty")
    
    def add(self, other: Money) -> Money:
        """加法"""
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
    
    def subtract(self, other: Money) -> Money:
        """減法"""
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")
        return Money(self.amount - other.amount, self.currency)
    
    def multiply(self, factor: int) -> Money:
        """乘法"""
        return Money(self.amount * factor, self.currency)
    
    def is_greater_than(self, other: Money) -> bool:
        """大於比較"""
        if self.currency != other.currency:
            raise ValueError("Cannot compare different currencies")
        return self.amount > other.amount
    
    def is_greater_than_or_equal(self, other: Money) -> bool:
        """大於等於比較"""
        if self.currency != other.currency:
            raise ValueError("Cannot compare different currencies")
        return self.amount >= other.amount
    
    def to_dict(self) -> Dict[str, Any]:
        return {"amount": self.amount, "currency": self.currency}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Money:
        return cls(amount=data["amount"], currency=data.get("currency", "TWD"))
    
    @classmethod
    def zero(cls, currency: str = "TWD") -> Money:
        """創建零金額"""
        return cls(0, currency)


@dataclass(frozen=True)
class Quantity(ValueObject):
    """數量值物件"""
    value: int
    
    def __post_init__(self):
        if self.value < 0:
            raise ValueError("Quantity cannot be negative")
    
    def add(self, other: Quantity) -> Quantity:
        """加法"""
        return Quantity(self.value + other.value)
    
    def subtract(self, other: Quantity) -> Quantity:
        """減法"""
        return Quantity(self.value - other.value)
    
    def multiply(self, factor: int) -> Quantity:
        """乘法"""
        return Quantity(self.value * factor)
    
    def is_greater_than(self, other: Quantity) -> bool:
        """大於比較"""
        return self.value > other.value
    
    def is_zero(self) -> bool:
        """是否為零"""
        return self.value == 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Quantity:
        return cls(value=data["value"])
    
    @classmethod
    def zero(cls) -> Quantity:
        """創建零數量"""
        return cls(0)


@dataclass(frozen=True)
class Price(ValueObject):
    """價格值物件"""
    amount: int
    currency: str = "TWD"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Price cannot be negative")
        if not self.currency:
            raise ValueError("Currency cannot be empty")
    
    def multiply(self, quantity: Quantity) -> Money:
        """價格乘以數量得到金額"""
        return Money(self.amount * quantity.value, self.currency)
    
    def is_greater_than(self, other: Price) -> bool:
        """大於比較"""
        if self.currency != other.currency:
            raise ValueError("Cannot compare different currencies")
        return self.amount > other.amount
    
    def to_dict(self) -> Dict[str, Any]:
        return {"amount": self.amount, "currency": self.currency}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Price:
        return cls(amount=data["amount"], currency=data.get("currency", "TWD"))


@dataclass(frozen=True)
class StockSymbol(ValueObject):
    """股票代碼值物件"""
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("Stock symbol cannot be empty")
        if not self.value.isalnum():
            raise ValueError("Stock symbol must be alphanumeric")
        if len(self.value) > 10:
            raise ValueError("Stock symbol cannot exceed 10 characters")
    
    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> StockSymbol:
        return cls(value=data["value"])


@dataclass(frozen=True)
class TelegramId(ValueObject):
    """Telegram ID 值物件"""
    value: int
    
    def __post_init__(self):
        if self.value <= 0:
            raise ValueError("Telegram ID must be positive")
    
    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TelegramId:
        return cls(value=data["value"])


@dataclass(frozen=True)
class StudentId(ValueObject):
    """學生 ID 值物件"""
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("Student ID cannot be empty")
        if len(self.value) > 20:
            raise ValueError("Student ID cannot exceed 20 characters")
    
    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> StudentId:
        return cls(value=data["value"])


@dataclass(frozen=True)
class Username(ValueObject):
    """使用者名稱值物件"""
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("Username cannot be empty")
        if len(self.value) > 50:
            raise ValueError("Username cannot exceed 50 characters")
    
    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Username:
        return cls(value=data["value"])


@dataclass(frozen=True)
class GroupId(ValueObject):
    """群組 ID 值物件"""
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("Group ID cannot be empty")
        if len(self.value) > 10:
            raise ValueError("Group ID cannot exceed 10 characters")
    
    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GroupId:
        return cls(value=data["value"])


@dataclass(frozen=True)
class OrderPrice(ValueObject):
    """訂單價格值物件"""
    amount: int
    
    def __post_init__(self):
        if self.amount <= 0:
            raise ValueError("Order price must be positive")
        if self.amount > 1000000:  # 最大價格限制
            raise ValueError("Order price cannot exceed 1,000,000")
    
    def calculate_total(self, quantity: Quantity) -> Money:
        """計算總金額"""
        return Money(self.amount * quantity.value)
    
    def to_dict(self) -> Dict[str, Any]:
        return {"amount": self.amount}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OrderPrice:
        return cls(amount=data["amount"])


@dataclass(frozen=True)
class OrderQuantity(ValueObject):
    """訂單數量值物件"""
    value: int
    
    def __post_init__(self):
        if self.value <= 0:
            raise ValueError("Order quantity must be positive")
        if self.value > 1000000:  # 最大數量限制
            raise ValueError("Order quantity cannot exceed 1,000,000")
    
    def can_fulfill(self, available: Quantity) -> bool:
        """是否可以滿足"""
        return available.value >= self.value
    
    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OrderQuantity:
        return cls(value=data["value"])