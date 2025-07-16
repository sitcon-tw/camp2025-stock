"""
User Domain Entities
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from dataclasses import dataclass


@dataclass
class User:
    """使用者實體"""
    id: Optional[ObjectId] = None
    telegram_id: int = 0
    username: str = ""
    points: int = 0
    student_id: Optional[str] = None
    real_name: Optional[str] = None
    group_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def add_points(self, amount: int) -> None:
        """增加點數"""
        self.points += amount
        self.updated_at = datetime.utcnow()
    
    def deduct_points(self, amount: int) -> bool:
        """扣除點數，如果餘額不足則返回 False"""
        if self.points < amount:
            return False
        self.points -= amount
        self.updated_at = datetime.utcnow()
        return True
    
    def has_sufficient_points(self, amount: int) -> bool:
        """檢查是否有足夠點數"""
        return self.points >= amount
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "_id": self.id,
            "telegram_id": self.telegram_id,
            "username": self.username,
            "points": self.points,
            "student_id": self.student_id,
            "real_name": self.real_name,
            "group_id": self.group_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> User:
        """從字典創建實體"""
        return cls(
            id=data.get("_id"),
            telegram_id=data.get("telegram_id", 0),
            username=data.get("username", ""),
            points=data.get("points", 0),
            student_id=data.get("student_id"),
            real_name=data.get("real_name"),
            group_id=data.get("group_id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


@dataclass
class PointLog:
    """點數變更記錄實體"""
    id: Optional[ObjectId] = None
    user_id: ObjectId = None
    change_type: str = ""
    amount: int = 0
    description: str = ""
    related_user_id: Optional[ObjectId] = None
    timestamp: Optional[datetime] = None
    log_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.log_id is None:
            self.log_id = str(ObjectId())
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "_id": self.id,
            "user_id": self.user_id,
            "change_type": self.change_type,
            "amount": self.amount,
            "description": self.description,
            "related_user_id": self.related_user_id,
            "timestamp": self.timestamp,
            "log_id": self.log_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PointLog:
        """從字典創建實體"""
        return cls(
            id=data.get("_id"),
            user_id=data.get("user_id"),
            change_type=data.get("change_type", ""),
            amount=data.get("amount", 0),
            description=data.get("description", ""),
            related_user_id=data.get("related_user_id"),
            timestamp=data.get("timestamp"),
            log_id=data.get("log_id")
        )