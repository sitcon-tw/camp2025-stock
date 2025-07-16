"""
User Domain Entities
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from dataclasses import dataclass
from enum import Enum

from ..common.events import AggregateRoot, UserCreatedEvent, PointsChangedEvent
from ..common.exceptions import (
    InsufficientPointsException, ValidationException, BusinessRuleException
)
from ..common.value_objects import Money, TelegramId, Username, StudentId, GroupId


class PointChangeType(Enum):
    """點數變更類型"""
    INITIAL = "initial"  # 初始點數
    ADMIN_GIVE = "admin_give"  # 管理員給予
    ADMIN_DEDUCT = "admin_deduct"  # 管理員扣除
    TRANSFER_SEND = "transfer_send"  # 轉帳發送
    TRANSFER_RECEIVE = "transfer_receive"  # 轉帳接收
    TRADING_BUY = "trading_buy"  # 交易購買
    TRADING_SELL = "trading_sell"  # 交易出售
    GAME_REWARD = "game_reward"  # 遊戲獎勵
    GAME_PENALTY = "game_penalty"  # 遊戲懲罰
    QR_SCAN = "qr_scan"  # QR 碼掃描
    DEBT_PAYMENT = "debt_payment"  # 債務支付
    DEBT_FORGIVENESS = "debt_forgiveness"  # 債務免除


class User(AggregateRoot):
    """
    使用者聚合根
    封裝使用者相關的業務邏輯和規則
    """
    
    def __init__(
        self,
        telegram_id: int,
        username: str,
        points: int = 0,
        student_id: Optional[str] = None,
        real_name: Optional[str] = None,
        group_id: Optional[str] = None,
        id: Optional[ObjectId] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        super().__init__()
        self.id = id
        self.telegram_id = telegram_id
        self.username = username
        self.points = points
        self.student_id = student_id
        self.real_name = real_name
        self.group_id = group_id
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        
        # 業務規則驗證
        self._validate()
        
        # 如果是新用戶，發布用戶創建事件
        if id is None:
            self.add_domain_event(UserCreatedEvent(
                event_id="",
                occurred_at=datetime.utcnow(),
                user_id=str(self.id) if self.id else "",
                telegram_id=self.telegram_id,
                username=self.username
            ))
    
    def _validate(self) -> None:
        """驗證使用者資料"""
        if self.telegram_id <= 0:
            raise ValidationException("Telegram ID must be positive", "telegram_id", self.telegram_id)
        
        if not self.username or len(self.username) > 50:
            raise ValidationException("Username must be 1-50 characters", "username", self.username)
        
        if self.points < 0:
            raise ValidationException("Points cannot be negative", "points", self.points)
        
        if self.student_id and len(self.student_id) > 20:
            raise ValidationException("Student ID cannot exceed 20 characters", "student_id", self.student_id)
        
        if self.group_id and len(self.group_id) > 10:
            raise ValidationException("Group ID cannot exceed 10 characters", "group_id", self.group_id)
    
    def update_profile(self, username: str, real_name: Optional[str] = None, 
                      student_id: Optional[str] = None, group_id: Optional[str] = None) -> None:
        """更新使用者資料"""
        old_username = self.username
        self.username = username
        self.real_name = real_name
        self.student_id = student_id
        self.group_id = group_id
        self.updated_at = datetime.utcnow()
        
        # 驗證更新後的資料
        self._validate()
        
        # 增加版本號
        self.increment_version()
    
    def change_points(self, amount: int, change_type: PointChangeType, 
                     description: str = "", related_user_id: Optional[ObjectId] = None) -> PointLog:
        """
        變更點數並記錄日誌
        這是點數變更的唯一入口點
        """
        if amount == 0:
            raise BusinessRuleException("Point change amount cannot be zero", "invalid_amount")
        
        old_points = self.points
        
        # 檢查餘額是否足夠（扣除時）
        if amount < 0 and self.points < abs(amount):
            raise InsufficientPointsException(
                user_id=self.id,
                required=abs(amount),
                available=self.points
            )
        
        # 檢查點數限制
        new_points = self.points + amount
        if new_points < 0:
            raise BusinessRuleException("Points cannot be negative after change", "negative_points")
        
        if new_points > 1000000:  # 設定最大點數限制
            raise BusinessRuleException("Points cannot exceed 1,000,000", "max_points_exceeded")
        
        # 更新點數
        self.points = new_points
        self.updated_at = datetime.utcnow()
        
        # 創建點數記錄
        point_log = PointLog(
            user_id=self.id,
            change_type=change_type.value,
            amount=amount,
            description=description,
            related_user_id=related_user_id
        )
        
        # 發布點數變更事件
        self.add_domain_event(PointsChangedEvent(
            event_id="",
            occurred_at=datetime.utcnow(),
            user_id=str(self.id) if self.id else "",
            old_points=old_points,
            new_points=self.points,
            change_amount=amount,
            change_type=change_type.value,
            description=description
        ))
        
        # 增加版本號
        self.increment_version()
        
        return point_log
    
    def add_points(self, amount: int, change_type: PointChangeType, 
                  description: str = "", related_user_id: Optional[ObjectId] = None) -> PointLog:
        """增加點數"""
        if amount <= 0:
            raise BusinessRuleException("Amount to add must be positive", "invalid_amount")
        
        return self.change_points(amount, change_type, description, related_user_id)
    
    def deduct_points(self, amount: int, change_type: PointChangeType, 
                     description: str = "", related_user_id: Optional[ObjectId] = None) -> PointLog:
        """扣除點數"""
        if amount <= 0:
            raise BusinessRuleException("Amount to deduct must be positive", "invalid_amount")
        
        return self.change_points(-amount, change_type, description, related_user_id)
    
    def has_sufficient_points(self, amount: int) -> bool:
        """檢查是否有足夠點數"""
        return self.points >= amount
    
    def can_transfer_to(self, target_user: 'User', amount: int) -> bool:
        """檢查是否可以轉帳給目標用戶"""
        if not self.has_sufficient_points(amount):
            return False
        
        if target_user.id == self.id:
            return False  # 不能轉給自己
        
        return True
    
    def transfer_to(self, target_user: 'User', amount: int, description: str = "") -> tuple[PointLog, PointLog]:
        """轉帳給其他用戶"""
        if not self.can_transfer_to(target_user, amount):
            raise BusinessRuleException("Cannot transfer to target user", "transfer_invalid")
        
        # 發送方扣除點數
        sender_log = self.deduct_points(
            amount, 
            PointChangeType.TRANSFER_SEND, 
            f"Transfer to {target_user.username}: {description}",
            target_user.id
        )
        
        # 接收方增加點數
        receiver_log = target_user.add_points(
            amount,
            PointChangeType.TRANSFER_RECEIVE,
            f"Transfer from {self.username}: {description}",
            self.id
        )
        
        return sender_log, receiver_log
    
    def link_student(self, student_id: str, real_name: str) -> None:
        """連結學生身份"""
        if not student_id or not real_name:
            raise ValidationException("Student ID and real name are required", "student_link")
        
        self.student_id = student_id
        self.real_name = real_name
        self.updated_at = datetime.utcnow()
        
        # 驗證更新後的資料
        self._validate()
        
        # 增加版本號
        self.increment_version()
    
    def join_group(self, group_id: str) -> None:
        """加入群組"""
        if not group_id:
            raise ValidationException("Group ID is required", "group_id")
        
        self.group_id = group_id
        self.updated_at = datetime.utcnow()
        
        # 驗證更新後的資料
        self._validate()
        
        # 增加版本號
        self.increment_version()
    
    def is_student(self) -> bool:
        """是否為學生"""
        return self.student_id is not None and self.real_name is not None
    
    def is_in_group(self) -> bool:
        """是否在群組中"""
        return self.group_id is not None
    
    def get_display_name(self) -> str:
        """獲取顯示名稱"""
        if self.real_name:
            return self.real_name
        return self.username
    
    def get_point_balance(self) -> Money:
        """獲取點數餘額作為金額值物件"""
        return Money(self.points)
    
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


class PointLog:
    """
    點數變更記錄實體
    記錄所有點數變更的詳細資訊
    """
    
    def __init__(
        self,
        user_id: ObjectId,
        change_type: str,
        amount: int,
        description: str = "",
        related_user_id: Optional[ObjectId] = None,
        id: Optional[ObjectId] = None,
        timestamp: Optional[datetime] = None,
        log_id: Optional[str] = None
    ):
        self.id = id
        self.user_id = user_id
        self.change_type = change_type
        self.amount = amount
        self.description = description
        self.related_user_id = related_user_id
        self.timestamp = timestamp or datetime.utcnow()
        self.log_id = log_id or str(ObjectId())
        
        # 驗證記錄
        self._validate()
    
    def _validate(self) -> None:
        """驗證點數記錄"""
        if not self.user_id:
            raise ValidationException("User ID is required", "user_id")
        
        if not self.change_type:
            raise ValidationException("Change type is required", "change_type")
        
        if self.amount == 0:
            raise ValidationException("Amount cannot be zero", "amount")
        
        if len(self.description) > 200:
            raise ValidationException("Description cannot exceed 200 characters", "description")
    
    def is_positive_change(self) -> bool:
        """是否為正向變更（增加點數）"""
        return self.amount > 0
    
    def is_negative_change(self) -> bool:
        """是否為負向變更（扣除點數）"""
        return self.amount < 0
    
    def is_transfer_related(self) -> bool:
        """是否為轉帳相關"""
        return self.change_type in [
            PointChangeType.TRANSFER_SEND.value,
            PointChangeType.TRANSFER_RECEIVE.value
        ]
    
    def is_trading_related(self) -> bool:
        """是否為交易相關"""
        return self.change_type in [
            PointChangeType.TRADING_BUY.value,
            PointChangeType.TRADING_SELL.value
        ]
    
    def is_admin_action(self) -> bool:
        """是否為管理員操作"""
        return self.change_type in [
            PointChangeType.ADMIN_GIVE.value,
            PointChangeType.ADMIN_DEDUCT.value
        ]
    
    def get_formatted_amount(self) -> str:
        """獲取格式化的金額字符串"""
        sign = "+" if self.amount > 0 else ""
        return f"{sign}{self.amount:,}"
    
    def get_change_type_display(self) -> str:
        """獲取變更類型的顯示名稱"""
        type_map = {
            PointChangeType.INITIAL.value: "初始點數",
            PointChangeType.ADMIN_GIVE.value: "管理員給予",
            PointChangeType.ADMIN_DEDUCT.value: "管理員扣除",
            PointChangeType.TRANSFER_SEND.value: "轉帳發送",
            PointChangeType.TRANSFER_RECEIVE.value: "轉帳接收",
            PointChangeType.TRADING_BUY.value: "交易購買",
            PointChangeType.TRADING_SELL.value: "交易出售",
            PointChangeType.GAME_REWARD.value: "遊戲獎勵",
            PointChangeType.GAME_PENALTY.value: "遊戲懲罰",
            PointChangeType.QR_SCAN.value: "QR掃描",
            PointChangeType.DEBT_PAYMENT.value: "債務支付",
            PointChangeType.DEBT_FORGIVENESS.value: "債務免除"
        }
        return type_map.get(self.change_type, self.change_type)
    
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