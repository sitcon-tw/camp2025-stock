"""
System Domain Entities
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId
from dataclasses import dataclass
from enum import Enum


class DebtStatus(Enum):
    """債務狀態"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    WAIVED = "waived"


@dataclass
class UserDebt:
    """使用者債務實體"""
    id: Optional[ObjectId] = None
    user_id: ObjectId = None
    amount: int = 0
    description: str = ""
    status: DebtStatus = DebtStatus.ACTIVE
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[ObjectId] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def resolve(self, resolved_by: ObjectId) -> None:
        """解決債務"""
        self.status = DebtStatus.RESOLVED
        self.resolved_at = datetime.utcnow()
        self.resolved_by = resolved_by
    
    def waive(self, waived_by: ObjectId) -> None:
        """免除債務"""
        self.status = DebtStatus.WAIVED
        self.resolved_at = datetime.utcnow()
        self.resolved_by = waived_by
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "_id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
            "resolved_by": self.resolved_by
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UserDebt:
        """從字典創建實體"""
        return cls(
            id=data.get("_id"),
            user_id=data.get("user_id"),
            amount=data.get("amount", 0),
            description=data.get("description", ""),
            status=DebtStatus(data.get("status", "active")),
            created_at=data.get("created_at"),
            resolved_at=data.get("resolved_at"),
            resolved_by=data.get("resolved_by")
        )


@dataclass
class Student:
    """學生實體"""
    id: Optional[ObjectId] = None
    student_id: str = ""
    real_name: str = ""
    group_id: Optional[str] = None
    telegram_id: Optional[int] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def update_info(self, real_name: str, group_id: Optional[str] = None) -> None:
        """更新學生資訊"""
        self.real_name = real_name
        if group_id is not None:
            self.group_id = group_id
        self.updated_at = datetime.utcnow()
    
    def link_telegram(self, telegram_id: int) -> None:
        """連結 Telegram 帳號"""
        self.telegram_id = telegram_id
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """啟用學生"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """停用學生"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "_id": self.id,
            "student_id": self.student_id,
            "real_name": self.real_name,
            "group_id": self.group_id,
            "telegram_id": self.telegram_id,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Student:
        """從字典創建實體"""
        return cls(
            id=data.get("_id"),
            student_id=data.get("student_id", ""),
            real_name=data.get("real_name", ""),
            group_id=data.get("group_id"),
            telegram_id=data.get("telegram_id"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )