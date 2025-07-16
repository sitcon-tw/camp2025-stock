"""
User Management Queries
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..common.interfaces import Query


class GetUserByIdQuery(Query):
    """根據ID獲取用戶查詢"""
    
    def __init__(self, target_user_id: str, include_permissions: bool = False, include_stats: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.target_user_id = target_user_id
        self.include_permissions = include_permissions
        self.include_stats = include_stats
        
        if not self.target_user_id:
            raise ValueError("Target user ID is required")


@dataclass
class GetUserByTelegramIdQuery(Query):
    """根據Telegram ID獲取用戶查詢"""
    telegram_id: int
    include_permissions: bool = False
    include_stats: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        if self.telegram_id <= 0:
            raise ValueError("Telegram ID must be positive")


@dataclass
class GetUserByStudentIdQuery(Query):
    """根據學生ID獲取用戶查詢"""
    student_id: str
    include_permissions: bool = False
    include_stats: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        if not self.student_id:
            raise ValueError("Student ID is required")


@dataclass
class GetUsersByGroupQuery(Query):
    """根據群組獲取用戶查詢"""
    group_id: str
    include_permissions: bool = False
    include_stats: bool = False
    skip: int = 0
    limit: int = 100
    
    def __post_init__(self):
        super().__post_init__()
        if not self.group_id:
            raise ValueError("Group ID is required")
        if self.skip < 0:
            raise ValueError("Skip cannot be negative")
        if self.limit <= 0 or self.limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")


@dataclass
class GetUsersListQuery(Query):
    """獲取用戶列表查詢"""
    search_term: Optional[str] = None
    active_only: bool = True
    include_permissions: bool = False
    include_stats: bool = False
    sort_by: str = "created_at"
    sort_order: str = "desc"
    skip: int = 0
    limit: int = 100
    
    def __post_init__(self):
        super().__post_init__()
        if self.skip < 0:
            raise ValueError("Skip cannot be negative")
        if self.limit <= 0 or self.limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")
        if self.sort_by not in ["created_at", "updated_at", "username", "points", "real_name"]:
            raise ValueError("Invalid sort field")
        if self.sort_order not in ["asc", "desc"]:
            raise ValueError("Sort order must be 'asc' or 'desc'")


@dataclass
class GetUserPointHistoryQuery(Query):
    """獲取用戶點數歷史查詢"""
    target_user_id: str
    change_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    skip: int = 0
    limit: int = 100
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")
        if self.skip < 0:
            raise ValueError("Skip cannot be negative")
        if self.limit <= 0 or self.limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("Start date cannot be after end date")


@dataclass
class GetUserStatisticsQuery(Query):
    """獲取用戶統計查詢"""
    target_user_id: str
    stats_type: str = "all"  # "all", "points", "trading", "social"
    period: str = "all"  # "all", "today", "week", "month", "year"
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")
        if self.stats_type not in ["all", "points", "trading", "social"]:
            raise ValueError("Invalid stats type")
        if self.period not in ["all", "today", "week", "month", "year"]:
            raise ValueError("Invalid period")


@dataclass
class GetUserPermissionsQuery(Query):
    """獲取用戶權限查詢"""
    target_user_id: str
    include_inherited: bool = True
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")


@dataclass
class GetUserNotificationsQuery(Query):
    """獲取用戶通知查詢"""
    target_user_id: str
    unread_only: bool = False
    notification_type: Optional[str] = None
    skip: int = 0
    limit: int = 50
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")
        if self.skip < 0:
            raise ValueError("Skip cannot be negative")
        if self.limit <= 0 or self.limit > 200:
            raise ValueError("Limit must be between 1 and 200")


@dataclass
class GetUserActivityQuery(Query):
    """獲取用戶活動查詢"""
    target_user_id: str
    activity_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    skip: int = 0
    limit: int = 100
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")
        if self.skip < 0:
            raise ValueError("Skip cannot be negative")
        if self.limit <= 0 or self.limit > 500:
            raise ValueError("Limit must be between 1 and 500")
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("Start date cannot be after end date")


@dataclass
class SearchUsersQuery(Query):
    """搜索用戶查詢"""
    search_term: str
    search_fields: List[str] = None  # ["username", "real_name", "student_id", "group_id"]
    active_only: bool = True
    skip: int = 0
    limit: int = 50
    
    def __post_init__(self):
        super().__post_init__()
        if not self.search_term:
            raise ValueError("Search term is required")
        if self.search_fields is None:
            self.search_fields = ["username", "real_name", "student_id"]
        if self.skip < 0:
            raise ValueError("Skip cannot be negative")
        if self.limit <= 0 or self.limit > 200:
            raise ValueError("Limit must be between 1 and 200")


@dataclass
class GetUserRankingQuery(Query):
    """獲取用戶排名查詢"""
    ranking_type: str = "points"  # "points", "trading_volume", "activity"
    period: str = "all"  # "all", "today", "week", "month", "year"
    group_id: Optional[str] = None
    limit: int = 50
    
    def __post_init__(self):
        super().__post_init__()
        if self.ranking_type not in ["points", "trading_volume", "activity"]:
            raise ValueError("Invalid ranking type")
        if self.period not in ["all", "today", "week", "month", "year"]:
            raise ValueError("Invalid period")
        if self.limit <= 0 or self.limit > 200:
            raise ValueError("Limit must be between 1 and 200")


@dataclass
class GetUserBalanceQuery(Query):
    """獲取用戶餘額查詢"""
    target_user_id: str
    include_frozen: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")


@dataclass
class GetUserTransactionHistoryQuery(Query):
    """獲取用戶交易歷史查詢"""
    target_user_id: str
    transaction_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    skip: int = 0
    limit: int = 100
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")
        if self.skip < 0:
            raise ValueError("Skip cannot be negative")
        if self.limit <= 0 or self.limit > 500:
            raise ValueError("Limit must be between 1 and 500")
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("Start date cannot be after end date")


@dataclass
class GetUserValidationStatusQuery(Query):
    """獲取用戶驗證狀態查詢"""
    target_user_id: str
    validation_type: str = "all"  # "all", "identity", "student", "email", "phone"
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")
        if self.validation_type not in ["all", "identity", "student", "email", "phone"]:
            raise ValueError("Invalid validation type")


@dataclass
class GetUserSessionsQuery(Query):
    """獲取用戶會話查詢"""
    target_user_id: str
    active_only: bool = True
    include_device_info: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")


@dataclass
class GetUserPreferencesQuery(Query):
    """獲取用戶偏好查詢"""
    target_user_id: str
    preference_category: Optional[str] = None
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")


@dataclass
class GetUserGroupsQuery(Query):
    """獲取用戶群組查詢"""
    target_user_id: str
    include_permissions: bool = False
    active_only: bool = True
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")


@dataclass
class GetUserAuditLogQuery(Query):
    """獲取用戶審計日誌查詢"""
    target_user_id: str
    action_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    skip: int = 0
    limit: int = 100
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")
        if self.skip < 0:
            raise ValueError("Skip cannot be negative")
        if self.limit <= 0 or self.limit > 500:
            raise ValueError("Limit must be between 1 and 500")
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("Start date cannot be after end date")


@dataclass
class GetUserDashboardQuery(Query):
    """獲取用戶儀表板查詢"""
    target_user_id: str
    include_stats: bool = True
    include_recent_activity: bool = True
    include_notifications: bool = True
    include_portfolio: bool = True
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")


@dataclass
class GetSystemUsersStatsQuery(Query):
    """獲取系統用戶統計查詢"""
    period: str = "all"  # "all", "today", "week", "month", "year"
    group_by: str = "none"  # "none", "group", "role", "registration_date"
    
    def __post_init__(self):
        super().__post_init__()
        if self.period not in ["all", "today", "week", "month", "year"]:
            raise ValueError("Invalid period")
        if self.group_by not in ["none", "group", "role", "registration_date"]:
            raise ValueError("Invalid group_by option")


@dataclass
class GetInactiveUsersQuery(Query):
    """獲取非活躍用戶查詢"""
    inactive_days: int = 30
    include_stats: bool = False
    skip: int = 0
    limit: int = 100
    
    def __post_init__(self):
        super().__post_init__()
        if self.inactive_days <= 0:
            raise ValueError("Inactive days must be positive")
        if self.skip < 0:
            raise ValueError("Skip cannot be negative")
        if self.limit <= 0 or self.limit > 500:
            raise ValueError("Limit must be between 1 and 500")


@dataclass
class GetUserComplianceStatusQuery(Query):
    """獲取用戶合規狀態查詢"""
    target_user_id: str
    compliance_type: str = "all"  # "all", "kyc", "privacy", "terms"
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")
        if self.compliance_type not in ["all", "kyc", "privacy", "terms"]:
            raise ValueError("Invalid compliance type")