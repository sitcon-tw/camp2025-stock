"""
Application Layer Common Interfaces
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

# Command and Query type variables
TCommand = TypeVar('TCommand')
TQuery = TypeVar('TQuery')
TResult = TypeVar('TResult')


@dataclass
class Command:
    """命令基類"""
    user_id: str
    timestamp: datetime
    correlation_id: str
    
    def __post_init__(self):
        if not self.user_id:
            raise ValueError("User ID is required")
        if not self.correlation_id:
            raise ValueError("Correlation ID is required")


class Query:
    """查詢基類"""
    
    def __init__(self, **kwargs):
        self.user_id = kwargs.get('user_id', None)
        self.timestamp = kwargs.get('timestamp', datetime.utcnow())
        self.correlation_id = kwargs.get('correlation_id', self._generate_correlation_id())
    
    def _generate_correlation_id(self) -> str:
        from bson import ObjectId
        return str(ObjectId())


@dataclass
class CommandResult:
    """命令結果基類"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    
    @classmethod
    def success_result(cls, message: str, data: Optional[Dict[str, Any]] = None) -> CommandResult:
        """創建成功結果"""
        return cls(success=True, message=message, data=data)
    
    @classmethod
    def failure_result(cls, message: str, errors: Optional[List[str]] = None) -> CommandResult:
        """創建失敗結果"""
        return cls(success=False, message=message, errors=errors or [])


@dataclass
class QueryResult(Generic[TResult]):
    """查詢結果基類"""
    success: bool
    data: Optional[TResult] = None
    message: str = ""
    errors: Optional[List[str]] = None
    total_count: Optional[int] = None
    
    @classmethod
    def success_result(cls, data: TResult, message: str = "", total_count: Optional[int] = None) -> QueryResult[TResult]:
        """創建成功結果"""
        return cls(success=True, data=data, message=message, total_count=total_count)
    
    @classmethod
    def failure_result(cls, message: str, errors: Optional[List[str]] = None) -> QueryResult[TResult]:
        """創建失敗結果"""
        return cls(success=False, message=message, errors=errors or [])


class CommandHandler(ABC, Generic[TCommand, TResult]):
    """命令處理器接口"""
    
    @abstractmethod
    async def handle(self, command: TCommand) -> TResult:
        """處理命令"""
        pass
    
    @abstractmethod
    def can_handle(self, command: TCommand) -> bool:
        """檢查是否可以處理該命令"""
        pass


class QueryHandler(ABC, Generic[TQuery, TResult]):
    """查詢處理器接口"""
    
    @abstractmethod
    async def handle(self, query: TQuery) -> TResult:
        """處理查詢"""
        pass
    
    @abstractmethod
    def can_handle(self, query: TQuery) -> bool:
        """檢查是否可以處理該查詢"""
        pass


class ApplicationService(ABC):
    """應用服務基類"""
    
    def __init__(self):
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def initialize(self) -> None:
        """初始化服務"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """清理服務"""
        pass


class UnitOfWork(ABC):
    """工作單元接口"""
    
    @abstractmethod
    async def begin(self) -> None:
        """開始事務"""
        pass
    
    @abstractmethod
    async def commit(self) -> None:
        """提交事務"""
        pass
    
    @abstractmethod
    async def rollback(self) -> None:
        """回滾事務"""
        pass
    
    @abstractmethod
    async def __aenter__(self):
        """異步上下文管理器入口"""
        await self.begin()
        return self
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()


class EventPublisher(ABC):
    """事件發布器接口"""
    
    @abstractmethod
    async def publish(self, event: Any) -> None:
        """發布事件"""
        pass
    
    @abstractmethod
    async def publish_batch(self, events: List[Any]) -> None:
        """批量發布事件"""
        pass


class ApplicationContext:
    """應用上下文"""
    
    def __init__(self):
        self.user_id: Optional[str] = None
        self.correlation_id: str = ""
        self.tenant_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self.request_id: Optional[str] = None
        self.metadata: Dict[str, Any] = {}
    
    def set_user(self, user_id: str) -> None:
        """設置用戶"""
        self.user_id = user_id
    
    def set_correlation_id(self, correlation_id: str) -> None:
        """設置相關ID"""
        self.correlation_id = correlation_id
    
    def add_metadata(self, key: str, value: Any) -> None:
        """添加元數據"""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """獲取元數據"""
        return self.metadata.get(key, default)


class ValidationError(Exception):
    """驗證錯誤"""
    
    def __init__(self, message: str, field: str = "", errors: Optional[List[str]] = None):
        super().__init__(message)
        self.message = message
        self.field = field
        self.errors = errors or []


class AuthorizationError(Exception):
    """授權錯誤"""
    
    def __init__(self, message: str, required_permission: str = ""):
        super().__init__(message)
        self.message = message
        self.required_permission = required_permission


class BusinessLogicError(Exception):
    """業務邏輯錯誤"""
    
    def __init__(self, message: str, code: str = "", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class Validator(ABC, Generic[TCommand]):
    """驗證器基類"""
    
    @abstractmethod
    async def validate(self, command: TCommand) -> List[str]:
        """驗證命令，返回錯誤列表"""
        pass
    
    @abstractmethod
    def can_validate(self, command: TCommand) -> bool:
        """檢查是否可以驗證該命令"""
        pass


class Permission:
    """權限類"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    def __str__(self) -> str:
        return self.name
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Permission):
            return self.name == other.name
        return False
    
    def __hash__(self) -> int:
        return hash(self.name)


class AuthorizationService(ABC):
    """授權服務接口"""
    
    @abstractmethod
    async def check_permission(self, user_id: str, permission: Permission) -> bool:
        """檢查用戶權限"""
        pass
    
    @abstractmethod
    async def get_user_permissions(self, user_id: str) -> List[Permission]:
        """獲取用戶權限列表"""
        pass
    
    @abstractmethod
    async def has_role(self, user_id: str, role: str) -> bool:
        """檢查用戶角色"""
        pass


def require_permission(permission: Permission):
    """權限裝飾器"""
    def decorator(func):
        async def wrapper(self, command_or_query, *args, **kwargs):
            # 假設服務有 authorization_service 屬性
            if hasattr(self, 'authorization_service'):
                user_id = getattr(command_or_query, 'user_id', None)
                if user_id and not await self.authorization_service.check_permission(user_id, permission):
                    raise AuthorizationError(f"Permission denied: {permission.name}", permission.name)
            return await func(self, command_or_query, *args, **kwargs)
        return wrapper
    return decorator


def validate_command(validator_class):
    """命令驗證裝飾器"""
    def decorator(func):
        async def wrapper(self, command, *args, **kwargs):
            if hasattr(self, 'validators'):
                for validator in self.validators:
                    if isinstance(validator, validator_class) and validator.can_validate(command):
                        errors = await validator.validate(command)
                        if errors:
                            raise ValidationError("Validation failed", errors=errors)
            return await func(self, command, *args, **kwargs)
        return wrapper
    return decorator


class CacheService(ABC):
    """緩存服務接口"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """獲取緩存值"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """設置緩存值"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """刪除緩存值"""
        pass
    
    @abstractmethod
    async def clear_pattern(self, pattern: str) -> None:
        """清除匹配模式的緩存"""
        pass


class NotificationService(ABC):
    """通知服務接口"""
    
    @abstractmethod
    async def send_notification(self, user_id: str, message: str, type: str = "info") -> None:
        """發送通知"""
        pass
    
    @abstractmethod
    async def send_bulk_notification(self, user_ids: List[str], message: str, type: str = "info") -> None:
        """批量發送通知"""
        pass


class LoggingService(ABC):
    """日誌服務接口"""
    
    @abstractmethod
    async def log_command(self, command: Command, result: CommandResult) -> None:
        """記錄命令執行"""
        pass
    
    @abstractmethod
    async def log_query(self, query: Query, result: QueryResult) -> None:
        """記錄查詢執行"""
        pass
    
    @abstractmethod
    async def log_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """記錄錯誤"""
        pass