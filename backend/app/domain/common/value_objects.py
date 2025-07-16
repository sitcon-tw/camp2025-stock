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


@dataclass(frozen=True)
class Email(ValueObject):
    """電子郵件值物件"""
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("Email cannot be empty")
        if "@" not in self.value:
            raise ValueError("Invalid email format")
        if len(self.value) > 100:
            raise ValueError("Email cannot exceed 100 characters")
    
    def get_domain(self) -> str:
        """獲取郵件域名"""
        return self.value.split("@")[1]
    
    def get_username(self) -> str:
        """獲取用戶名部分"""
        return self.value.split("@")[0]
    
    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Email:
        return cls(value=data["value"])


@dataclass(frozen=True)
class PhoneNumber(ValueObject):
    """電話號碼值物件"""
    value: str
    country_code: str = "TW"
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("Phone number cannot be empty")
        if not self.value.replace("+", "").replace("-", "").replace(" ", "").isdigit():
            raise ValueError("Phone number must contain only digits, +, -, and spaces")
        if len(self.value) > 20:
            raise ValueError("Phone number cannot exceed 20 characters")
    
    def get_formatted(self) -> str:
        """獲取格式化的電話號碼"""
        clean_number = self.value.replace(" ", "").replace("-", "")
        if self.country_code == "TW" and not clean_number.startswith("+"):
            if clean_number.startswith("0"):
                return f"+886{clean_number[1:]}"
            else:
                return f"+886{clean_number}"
        return clean_number
    
    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value, "country_code": self.country_code}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PhoneNumber:
        return cls(value=data["value"], country_code=data.get("country_code", "TW"))


@dataclass(frozen=True)
class Address(ValueObject):
    """地址值物件"""
    street: str
    city: str
    postal_code: str
    country: str = "Taiwan"
    
    def __post_init__(self):
        if not self.street:
            raise ValueError("Street cannot be empty")
        if not self.city:
            raise ValueError("City cannot be empty")
        if not self.postal_code:
            raise ValueError("Postal code cannot be empty")
        if len(self.street) > 200:
            raise ValueError("Street cannot exceed 200 characters")
        if len(self.city) > 50:
            raise ValueError("City cannot exceed 50 characters")
        if len(self.postal_code) > 10:
            raise ValueError("Postal code cannot exceed 10 characters")
    
    def get_full_address(self) -> str:
        """獲取完整地址"""
        return f"{self.street}, {self.city} {self.postal_code}, {self.country}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "street": self.street,
            "city": self.city,
            "postal_code": self.postal_code,
            "country": self.country
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Address:
        return cls(
            street=data["street"],
            city=data["city"],
            postal_code=data["postal_code"],
            country=data.get("country", "Taiwan")
        )


@dataclass(frozen=True)
class DateRange(ValueObject):
    """日期範圍值物件"""
    start_date: str  # ISO format date string
    end_date: str    # ISO format date string
    
    def __post_init__(self):
        if not self.start_date or not self.end_date:
            raise ValueError("Start date and end date are required")
        
        # 簡單的日期格式驗證
        if len(self.start_date) != 10 or len(self.end_date) != 10:
            raise ValueError("Date must be in YYYY-MM-DD format")
        
        if self.start_date > self.end_date:
            raise ValueError("Start date must be before end date")
    
    def contains_date(self, date_str: str) -> bool:
        """檢查日期是否在範圍內"""
        return self.start_date <= date_str <= self.end_date
    
    def get_duration_days(self) -> int:
        """獲取持續天數"""
        from datetime import datetime
        start = datetime.fromisoformat(self.start_date)
        end = datetime.fromisoformat(self.end_date)
        return (end - start).days
    
    def to_dict(self) -> Dict[str, Any]:
        return {"start_date": self.start_date, "end_date": self.end_date}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DateRange:
        return cls(start_date=data["start_date"], end_date=data["end_date"])


@dataclass(frozen=True)
class Percentage(ValueObject):
    """百分比值物件"""
    value: float
    
    def __post_init__(self):
        if self.value < 0 or self.value > 100:
            raise ValueError("Percentage must be between 0 and 100")
    
    def as_decimal(self) -> float:
        """轉換為小數"""
        return self.value / 100
    
    def is_zero(self) -> bool:
        """是否為零"""
        return self.value == 0.0
    
    def is_full(self) -> bool:
        """是否為 100%"""
        return self.value == 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Percentage:
        return cls(value=data["value"])
    
    @classmethod
    def from_decimal(cls, decimal_value: float) -> Percentage:
        """從小數創建百分比"""
        return cls(decimal_value * 100)


@dataclass(frozen=True)
class IPAddress(ValueObject):
    """IP 地址值物件"""
    value: str
    version: int = 4  # IPv4 or IPv6
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("IP address cannot be empty")
        
        if self.version == 4:
            self._validate_ipv4()
        elif self.version == 6:
            self._validate_ipv6()
        else:
            raise ValueError("IP version must be 4 or 6")
    
    def _validate_ipv4(self):
        """驗證 IPv4 地址"""
        parts = self.value.split(".")
        if len(parts) != 4:
            raise ValueError("Invalid IPv4 address format")
        
        for part in parts:
            try:
                num = int(part)
                if num < 0 or num > 255:
                    raise ValueError("IPv4 address parts must be between 0 and 255")
            except ValueError:
                raise ValueError("IPv4 address parts must be integers")
    
    def _validate_ipv6(self):
        """驗證 IPv6 地址"""
        if "::" in self.value:
            parts = self.value.split("::")
            if len(parts) > 2:
                raise ValueError("Invalid IPv6 address format")
        else:
            parts = self.value.split(":")
            if len(parts) != 8:
                raise ValueError("Invalid IPv6 address format")
    
    def is_private(self) -> bool:
        """是否為私有 IP"""
        if self.version == 4:
            parts = [int(p) for p in self.value.split(".")]
            return (
                parts[0] == 10 or
                (parts[0] == 172 and 16 <= parts[1] <= 31) or
                (parts[0] == 192 and parts[1] == 168)
            )
        return False  # IPv6 私有地址檢查較複雜，暫時返回 False
    
    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value, "version": self.version}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> IPAddress:
        return cls(value=data["value"], version=data.get("version", 4))


@dataclass(frozen=True)
class Hash(ValueObject):
    """哈希值物件"""
    value: str
    algorithm: str = "sha256"
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("Hash value cannot be empty")
        
        # 驗證哈希長度
        expected_lengths = {
            "md5": 32,
            "sha1": 40,
            "sha256": 64,
            "sha512": 128
        }
        
        if self.algorithm in expected_lengths:
            expected_length = expected_lengths[self.algorithm]
            if len(self.value) != expected_length:
                raise ValueError(f"{self.algorithm} hash must be {expected_length} characters")
        
        # 驗證是否為十六進制
        if not all(c in "0123456789abcdefABCDEF" for c in self.value):
            raise ValueError("Hash must be hexadecimal")
    
    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value, "algorithm": self.algorithm}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Hash:
        return cls(value=data["value"], algorithm=data.get("algorithm", "sha256"))


@dataclass(frozen=True)
class Version(ValueObject):
    """版本號值物件"""
    major: int
    minor: int
    patch: int
    
    def __post_init__(self):
        if self.major < 0 or self.minor < 0 or self.patch < 0:
            raise ValueError("Version numbers cannot be negative")
    
    def is_greater_than(self, other: Version) -> bool:
        """版本比較"""
        if self.major != other.major:
            return self.major > other.major
        if self.minor != other.minor:
            return self.minor > other.minor
        return self.patch > other.patch
    
    def is_compatible_with(self, other: Version) -> bool:
        """版本兼容性檢查（主版本相同）"""
        return self.major == other.major
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {"major": self.major, "minor": self.minor, "patch": self.patch}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Version:
        return cls(major=data["major"], minor=data["minor"], patch=data["patch"])
    
    @classmethod
    def from_string(cls, version_str: str) -> Version:
        """從字符串創建版本"""
        parts = version_str.split(".")
        if len(parts) != 3:
            raise ValueError("Version string must be in format major.minor.patch")
        
        try:
            major, minor, patch = map(int, parts)
            return cls(major=major, minor=minor, patch=patch)
        except ValueError:
            raise ValueError("Version parts must be integers")