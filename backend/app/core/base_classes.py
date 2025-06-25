# 基礎類別定義
# LSP 原則：確保子類別可以完全替換父類別
# ISP 原則：分離介面，避免強制實作不需要的方法

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List
from datetime import datetime


class BaseEntity(ABC):
    """
    基礎實體抽象類
    LSP 原則：所有實體都必須遵循相同的基礎行為
    """
    
    def __init__(self, entity_id: str, created_at: Optional[datetime] = None):
        self.entity_id = entity_id
        self.created_at = created_at or datetime.now()
        self.updated_at = datetime.now()
    
    def update_timestamp(self) -> None:
        """更新時間戳"""
        self.updated_at = datetime.now()
    
    @abstractmethod
    def validate(self) -> bool:
        """驗證實體的有效性"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        pass
    
    def __eq__(self, other) -> bool:
        """比較兩個實體是否相等（基於 ID）"""
        if not isinstance(other, BaseEntity):
            return False
        return self.entity_id == other.entity_id


class BaseRepository(ABC):
    """
    基礎資料存取抽象類
    LSP 原則：所有 Repository 實作都必須遵循相同的基礎行為
    ISP 原則：只定義最基本的 CRUD 操作
    """
    
    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[BaseEntity]:
        """根據ID獲取實體"""
        pass
    
    @abstractmethod
    async def save(self, entity: BaseEntity) -> None:
        """保存實體"""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """刪除實體"""
        pass
    
    @abstractmethod
    async def exists(self, entity_id: str) -> bool:
        """檢查實體是否存在"""
        pass


class ReadOnlyRepository(ABC):
    """
    唯讀資料存取介面
    ISP 原則：分離讀取和寫入操作，某些服務可能只需要讀取功能
    """
    
    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[BaseEntity]:
        """根據ID獲取實體"""
        pass
    
    @abstractmethod
    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[BaseEntity]:
        """根據條件查詢實體"""
        pass
    
    @abstractmethod
    async def count(self, criteria: Optional[Dict[str, Any]] = None) -> int:
        """計算符合條件的實體數量"""
        pass


class WriteOnlyRepository(ABC):
    """
    唯寫資料存取介面
    ISP 原則：分離寫入操作，某些服務可能只需要寫入功能
    """
    
    @abstractmethod
    async def save(self, entity: BaseEntity) -> None:
        """保存實體"""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """刪除實體"""
        pass
    
    @abstractmethod
    async def batch_save(self, entities: List[BaseEntity]) -> None:
        """批量保存實體"""
        pass


class BaseService(ABC):
    """
    基礎服務抽象類
    LSP 原則：所有服務都必須遵循相同的基礎行為
    """
    
    def __init__(self, logger_name: str):
        import logging
        self.logger = logging.getLogger(logger_name)
    
    def log_operation(self, operation: str, details: str = "") -> None:
        """記錄操作日誌"""
        self.logger.info(f"Operation: {operation} - {details}")
    
    def log_error(self, error: Exception, context: str = "") -> None:
        """記錄錯誤日誌"""
        self.logger.error(f"Error in {context}: {error}")
    
    @abstractmethod
    async def initialize(self) -> None:
        """初始化服務"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """清理服務資源"""
        pass


class BaseApplicationService(BaseService):
    """
    基礎應用服務抽象類
    LSP 原則：所有應用服務都遵循相同的介面
    """
    
    def __init__(self, service_name: str):
        super().__init__(service_name)
        self.service_name = service_name
    
    async def initialize(self) -> None:
        """初始化應用服務"""
        self.log_operation("initialize", f"Initializing {self.service_name}")
    
    async def cleanup(self) -> None:
        """清理應用服務"""
        self.log_operation("cleanup", f"Cleaning up {self.service_name}")


class EventHandler(ABC):
    """
    事件處理器介面
    ISP 原則：分離事件處理邏輯，只實作需要的事件
    """
    
    @abstractmethod
    async def handle(self, event_data: Dict[str, Any]) -> bool:
        """處理事件"""
        pass
    
    @abstractmethod
    def can_handle(self, event_type: str) -> bool:
        """判斷是否可以處理特定類型的事件"""
        pass


class Validator(ABC):
    """
    驗證器介面
    ISP 原則：分離驗證邏輯，不同的驗證器只關注特定的驗證規則
    """
    
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """驗證資料"""
        pass
    
    @abstractmethod
    def get_error_message(self) -> str:
        """獲取錯誤訊息"""
        pass


class CacheProvider(ABC):
    """
    快取提供者介面
    ISP 原則：只定義必要的快取操作
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """獲取快取值"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """設定快取值"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """刪除快取值"""
        pass


class NotificationProvider(ABC):
    """
    通知提供者介面
    ISP 原則：只定義通知相關的操作
    """
    
    @abstractmethod
    async def send_notification(self, recipient: str, message: str, 
                              notification_type: str = "info") -> bool:
        """傳送通知"""
        pass
    
    @abstractmethod
    async def send_bulk_notification(self, recipients: List[str], 
                                   message: str, notification_type: str = "info") -> Dict[str, bool]:
        """批量傳送通知"""
        pass


# LSP 原則的示範：確保子類別可以完全替換父類別
class UserEntityBase(BaseEntity):
    """
    使用者實體基礎類
    LSP 原則：所有使用者類型都必須遵循相同的基礎行為
    """
    
    def __init__(self, entity_id: str, username: str, email: str):
        super().__init__(entity_id)
        self.username = username
        self.email = email
    
    def validate(self) -> bool:
        """驗證使用者基礎資料"""
        return (
            len(self.username) >= 2 and 
            len(self.username) <= 50 and
            "@" in self.email
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "entity_id": self.entity_id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class RegularUser(UserEntityBase):
    """
    一般使用者
    LSP 原則：可以完全替換 UserEntityBase
    """
    
    def __init__(self, entity_id: str, username: str, email: str, points: int = 100):
        super().__init__(entity_id, username, email)
        self.points = points
        self.user_type = "regular"
    
    def validate(self) -> bool:
        """擴充驗證邏輯，但不破壞基礎約定"""
        return super().validate() and self.points >= 0
    
    def to_dict(self) -> Dict[str, Any]:
        """擴充字典格式，但包含基礎欄位"""
        base_dict = super().to_dict()
        base_dict.update({
            "points": self.points,
            "user_type": self.user_type
        })
        return base_dict


class VIPUser(UserEntityBase):
    """
    VIP 使用者
    LSP 原則：可以完全替換 UserEntityBase
    """
    
    def __init__(self, entity_id: str, username: str, email: str, 
                 points: int = 1000, privilege_level: int = 1):
        super().__init__(entity_id, username, email)
        self.points = points
        self.privilege_level = privilege_level
        self.user_type = "vip"
    
    def validate(self) -> bool:
        """擴充驗證邏輯，但不破壞基礎約定"""
        return (
            super().validate() and 
            self.points >= 0 and 
            self.privilege_level in [1, 2, 3]
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """擴充字典格式，但包含基礎欄位"""
        base_dict = super().to_dict()
        base_dict.update({
            "points": self.points,
            "privilege_level": self.privilege_level,
            "user_type": self.user_type
        })
        return base_dict