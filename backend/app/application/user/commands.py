"""
User Management Commands
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from bson import ObjectId

from ..common.interfaces import Command


@dataclass
class CreateUserCommand(Command):
    """創建用戶命令"""
    telegram_id: int
    username: str
    points: int = 0
    student_id: Optional[str] = None
    real_name: Optional[str] = None
    group_id: Optional[str] = None
    
    def __post_init__(self):
        super().__post_init__()
        if self.telegram_id <= 0:
            raise ValueError("Telegram ID must be positive")
        if not self.username:
            raise ValueError("Username is required")
        if self.points < 0:
            raise ValueError("Points cannot be negative")


@dataclass
class UpdateUserProfileCommand(Command):
    """更新用戶資料命令"""
    target_user_id: str
    username: Optional[str] = None
    real_name: Optional[str] = None
    student_id: Optional[str] = None
    group_id: Optional[str] = None
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")


@dataclass
class ChangeUserPointsCommand(Command):
    """變更用戶點數命令"""
    target_user_id: str
    amount: int
    change_type: str
    description: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")
        if self.amount == 0:
            raise ValueError("Amount cannot be zero")
        if not self.change_type:
            raise ValueError("Change type is required")


@dataclass
class TransferPointsCommand(Command):
    """轉帳點數命令"""
    recipient_user_id: str
    amount: int
    description: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        if not self.recipient_user_id:
            raise ValueError("Recipient user ID is required")
        if self.amount <= 0:
            raise ValueError("Amount must be positive")
        if self.user_id == self.recipient_user_id:
            raise ValueError("Cannot transfer to yourself")


@dataclass
class LinkStudentCommand(Command):
    """連結學生身份命令"""
    student_id: str
    real_name: str
    
    def __post_init__(self):
        super().__post_init__()
        if not self.student_id:
            raise ValueError("Student ID is required")
        if not self.real_name:
            raise ValueError("Real name is required")


@dataclass
class JoinGroupCommand(Command):
    """加入群組命令"""
    group_id: str
    
    def __post_init__(self):
        super().__post_init__()
        if not self.group_id:
            raise ValueError("Group ID is required")


@dataclass
class DeactivateUserCommand(Command):
    """停用用戶命令"""
    target_user_id: str
    reason: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")


@dataclass
class ReactivateUserCommand(Command):
    """重新啟用用戶命令"""
    target_user_id: str
    reason: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")


@dataclass
class BulkUpdatePointsCommand(Command):
    """批量更新點數命令"""
    user_point_changes: list  # List of {"user_id": str, "amount": int, "description": str}
    change_type: str
    
    def __post_init__(self):
        super().__post_init__()
        if not self.user_point_changes:
            raise ValueError("User point changes list is required")
        if not self.change_type:
            raise ValueError("Change type is required")
        
        for change in self.user_point_changes:
            if not isinstance(change, dict):
                raise ValueError("Each change must be a dictionary")
            if "user_id" not in change or "amount" not in change:
                raise ValueError("Each change must have user_id and amount")
            if change["amount"] == 0:
                raise ValueError("Amount cannot be zero")


@dataclass
class CreatePointLogCommand(Command):
    """創建點數記錄命令"""
    target_user_id: str
    change_type: str
    amount: int
    description: str = ""
    related_user_id: Optional[str] = None
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")
        if not self.change_type:
            raise ValueError("Change type is required")
        if self.amount == 0:
            raise ValueError("Amount cannot be zero")


@dataclass
class ResetUserPasswordCommand(Command):
    """重置用戶密碼命令"""
    target_user_id: str
    new_password: str
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")
        if not self.new_password:
            raise ValueError("New password is required")
        if len(self.new_password) < 8:
            raise ValueError("Password must be at least 8 characters")


@dataclass
class UpdateUserPermissionsCommand(Command):
    """更新用戶權限命令"""
    target_user_id: str
    permissions: list  # List of permission names
    operation: str  # "add", "remove", "set"
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")
        if not self.permissions:
            raise ValueError("Permissions list is required")
        if self.operation not in ["add", "remove", "set"]:
            raise ValueError("Operation must be 'add', 'remove', or 'set'")


@dataclass
class SendUserNotificationCommand(Command):
    """發送用戶通知命令"""
    target_user_id: str
    message: str
    notification_type: str = "info"
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")
        if not self.message:
            raise ValueError("Message is required")
        if self.notification_type not in ["info", "warning", "error", "success"]:
            raise ValueError("Invalid notification type")


@dataclass
class BulkSendNotificationCommand(Command):
    """批量發送通知命令"""
    target_user_ids: list
    message: str
    notification_type: str = "info"
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_ids:
            raise ValueError("Target user IDs list is required")
        if not self.message:
            raise ValueError("Message is required")
        if self.notification_type not in ["info", "warning", "error", "success"]:
            raise ValueError("Invalid notification type")


@dataclass
class ArchiveUserCommand(Command):
    """歸檔用戶命令"""
    target_user_id: str
    reason: str = ""
    preserve_data: bool = True
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")


@dataclass
class ValidateUserDataCommand(Command):
    """驗證用戶數據命令"""
    target_user_id: str
    validation_type: str = "full"  # "full", "basic", "compliance"
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")
        if self.validation_type not in ["full", "basic", "compliance"]:
            raise ValueError("Invalid validation type")


@dataclass
class RecalculateUserStatsCommand(Command):
    """重新計算用戶統計命令"""
    target_user_id: str
    stats_type: str = "all"  # "all", "points", "trading", "social"
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")
        if self.stats_type not in ["all", "points", "trading", "social"]:
            raise ValueError("Invalid stats type")


@dataclass
class MergeUserAccountsCommand(Command):
    """合併用戶帳戶命令"""
    primary_user_id: str
    secondary_user_id: str
    merge_strategy: str = "primary_priority"  # "primary_priority", "secondary_priority", "merge_all"
    
    def __post_init__(self):
        super().__post_init__()
        if not self.primary_user_id:
            raise ValueError("Primary user ID is required")
        if not self.secondary_user_id:
            raise ValueError("Secondary user ID is required")
        if self.primary_user_id == self.secondary_user_id:
            raise ValueError("Cannot merge user with themselves")
        if self.merge_strategy not in ["primary_priority", "secondary_priority", "merge_all"]:
            raise ValueError("Invalid merge strategy")


@dataclass
class ExportUserDataCommand(Command):
    """匯出用戶資料命令"""
    target_user_id: str
    export_format: str = "json"  # "json", "csv", "xml"
    include_sensitive: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")
        if self.export_format not in ["json", "csv", "xml"]:
            raise ValueError("Invalid export format")