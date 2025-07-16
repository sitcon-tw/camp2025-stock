"""
Market Domain Entities
"""
from __future__ import annotations
from datetime import datetime, time
from typing import Optional, Dict, Any
from bson import ObjectId
from dataclasses import dataclass
from enum import Enum


class MarketStatus(Enum):
    """市場狀態"""
    OPEN = "open"
    CLOSED = "closed"
    MANUAL_OVERRIDE = "manual_override"


@dataclass
class MarketConfig:
    """市場配置實體"""
    id: Optional[ObjectId] = None
    config_type: str = ""
    status: MarketStatus = MarketStatus.CLOSED
    open_time: Optional[time] = None
    close_time: Optional[time] = None
    timezone: str = "Asia/Taipei"
    manual_control: bool = False
    trading_limits: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.trading_limits is None:
            self.trading_limits = {}
    
    def is_market_open(self) -> bool:
        """檢查市場是否開放"""
        if self.manual_control:
            return self.status == MarketStatus.OPEN
        
        # 根據設定的時間檢查
        if self.open_time and self.close_time:
            current_time = datetime.now().time()
            if self.open_time <= self.close_time:
                return self.open_time <= current_time <= self.close_time
            else:
                # 跨日情況
                return current_time >= self.open_time or current_time <= self.close_time
        
        return self.status == MarketStatus.OPEN
    
    def set_manual_control(self, is_open: bool) -> None:
        """設定手動控制"""
        self.manual_control = True
        self.status = MarketStatus.OPEN if is_open else MarketStatus.CLOSED
        self.updated_at = datetime.utcnow()
    
    def set_scheduled_hours(self, open_time: time, close_time: time) -> None:
        """設定預定時間"""
        self.manual_control = False
        self.open_time = open_time
        self.close_time = close_time
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "_id": self.id,
            "config_type": self.config_type,
            "status": self.status.value,
            "open_time": self.open_time.isoformat() if self.open_time else None,
            "close_time": self.close_time.isoformat() if self.close_time else None,
            "timezone": self.timezone,
            "manual_control": self.manual_control,
            "trading_limits": self.trading_limits,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MarketConfig:
        """從字典創建實體"""
        return cls(
            id=data.get("_id"),
            config_type=data.get("config_type", ""),
            status=MarketStatus(data.get("status", "closed")),
            open_time=time.fromisoformat(data["open_time"]) if data.get("open_time") else None,
            close_time=time.fromisoformat(data["close_time"]) if data.get("close_time") else None,
            timezone=data.get("timezone", "Asia/Taipei"),
            manual_control=data.get("manual_control", False),
            trading_limits=data.get("trading_limits", {}),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


@dataclass
class IPOConfig:
    """IPO 配置實體"""
    id: Optional[ObjectId] = None
    config_type: str = "ipo_status"
    initial_shares: int = 0
    initial_price: int = 0
    is_active: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """啟用 IPO"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """停用 IPO"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def update_settings(self, initial_shares: int, initial_price: int) -> None:
        """更新 IPO 設定"""
        self.initial_shares = initial_shares
        self.initial_price = initial_price
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "_id": self.id,
            "config_type": self.config_type,
            "initial_shares": self.initial_shares,
            "initial_price": self.initial_price,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> IPOConfig:
        """從字典創建實體"""
        return cls(
            id=data.get("_id"),
            config_type=data.get("config_type", "ipo_status"),
            initial_shares=data.get("initial_shares", 0),
            initial_price=data.get("initial_price", 0),
            is_active=data.get("is_active", False),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


@dataclass
class Announcement:
    """公告實體"""
    id: Optional[ObjectId] = None
    title: str = ""
    content: str = ""
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def update_content(self, title: str, content: str) -> None:
        """更新公告內容"""
        self.title = title
        self.content = content
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """啟用公告"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """停用公告"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "_id": self.id,
            "title": self.title,
            "content": self.content,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Announcement:
        """從字典創建實體"""
        return cls(
            id=data.get("_id"),
            title=data.get("title", ""),
            content=data.get("content", ""),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )