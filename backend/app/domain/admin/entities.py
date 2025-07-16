"""
Admin Domain Entities
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any, List
from bson import ObjectId
from dataclasses import dataclass
from enum import Enum


class AdminRole(Enum):
    """管理員角色"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MODERATOR = "moderator"


@dataclass
class AdminUser:
    """管理員使用者實體"""
    id: Optional[ObjectId] = None
    username: str = ""
    role: AdminRole = AdminRole.ADMIN
    permissions: List[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.permissions is None:
            self.permissions = []
    
    def has_permission(self, permission: str) -> bool:
        """檢查是否有特定權限"""
        return permission in self.permissions or self.role == AdminRole.SUPER_ADMIN
    
    def add_permission(self, permission: str) -> None:
        """添加權限"""
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.updated_at = datetime.utcnow()
    
    def remove_permission(self, permission: str) -> None:
        """移除權限"""
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """啟用管理員"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """停用管理員"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "_id": self.id,
            "username": self.username,
            "role": self.role.value,
            "permissions": self.permissions,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AdminUser:
        """從字典創建實體"""
        return cls(
            id=data.get("_id"),
            username=data.get("username", ""),
            role=AdminRole(data.get("role", "admin")),
            permissions=data.get("permissions", []),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


@dataclass
class AdminAction:
    """管理員操作記錄實體"""
    id: Optional[ObjectId] = None
    admin_id: ObjectId = None
    action_type: str = ""
    target_type: str = ""
    target_id: Optional[ObjectId] = None
    description: str = ""
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.details is None:
            self.details = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "_id": self.id,
            "admin_id": self.admin_id,
            "action_type": self.action_type,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "description": self.description,
            "details": self.details,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AdminAction:
        """從字典創建實體"""
        return cls(
            id=data.get("_id"),
            admin_id=data.get("admin_id"),
            action_type=data.get("action_type", ""),
            target_type=data.get("target_type", ""),
            target_id=data.get("target_id"),
            description=data.get("description", ""),
            details=data.get("details", {}),
            timestamp=data.get("timestamp")
        )