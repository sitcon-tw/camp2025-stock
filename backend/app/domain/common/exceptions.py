"""
Domain-Specific Exceptions
"""
from typing import Optional, Dict, Any


class DomainException(Exception):
    """
    領域異常基類
    所有領域相關的異常都應該繼承此類
    """
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self):
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


class ValidationException(DomainException):
    """
    驗證異常
    當輸入資料不符合業務規則時拋出
    """
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        super().__init__(message, "VALIDATION_ERROR")
        self.field = field
        self.value = value
        self.details = {
            "field": field,
            "value": value
        }


class BusinessRuleException(DomainException):
    """
    業務規則異常
    當違反業務規則時拋出
    """
    
    def __init__(self, message: str, rule_name: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "BUSINESS_RULE_VIOLATION")
        self.rule_name = rule_name
        self.context = context or {}
        self.details = {
            "rule_name": rule_name,
            "context": self.context
        }


class EntityNotFoundException(DomainException):
    """
    實體未找到異常
    當查找的實體不存在時拋出
    """
    
    def __init__(self, entity_type: str, identifier: Any):
        message = f"{entity_type} with identifier '{identifier}' not found"
        super().__init__(message, "ENTITY_NOT_FOUND")
        self.entity_type = entity_type
        self.identifier = identifier
        self.details = {
            "entity_type": entity_type,
            "identifier": str(identifier)
        }


class ConcurrencyException(DomainException):
    """
    並行異常
    當發生並行衝突時拋出
    """
    
    def __init__(self, message: str, entity_type: str, entity_id: Any):
        super().__init__(message, "CONCURRENCY_CONFLICT")
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.details = {
            "entity_type": entity_type,
            "entity_id": str(entity_id)
        }


class InsufficientResourceException(DomainException):
    """
    資源不足異常
    當資源不足時拋出（如餘額不足、庫存不足等）
    """
    
    def __init__(self, message: str, resource_type: str, required: Any, available: Any):
        super().__init__(message, "INSUFFICIENT_RESOURCE")
        self.resource_type = resource_type
        self.required = required
        self.available = available
        self.details = {
            "resource_type": resource_type,
            "required": required,
            "available": available
        }


class AuthorizationException(DomainException):
    """
    授權異常
    當沒有權限執行操作時拋出
    """
    
    def __init__(self, message: str, user_id: Any, operation: str):
        super().__init__(message, "AUTHORIZATION_FAILED")
        self.user_id = user_id
        self.operation = operation
        self.details = {
            "user_id": str(user_id),
            "operation": operation
        }


class ConfigurationException(DomainException):
    """
    配置異常
    當配置錯誤時拋出
    """
    
    def __init__(self, message: str, config_key: str, config_value: Any):
        super().__init__(message, "CONFIGURATION_ERROR")
        self.config_key = config_key
        self.config_value = config_value
        self.details = {
            "config_key": config_key,
            "config_value": config_value
        }


# 領域特定異常

class UserDomainException(DomainException):
    """使用者領域異常"""
    pass


class TradingDomainException(DomainException):
    """交易領域異常"""
    pass


class MarketDomainException(DomainException):
    """市場領域異常"""
    pass


class SystemDomainException(DomainException):
    """系統領域異常"""
    pass


class AdminDomainException(DomainException):
    """管理領域異常"""
    pass


# 具體業務異常

class InsufficientPointsException(UserDomainException):
    """點數不足異常"""
    
    def __init__(self, user_id: Any, required: int, available: int):
        message = f"Insufficient points: required {required}, available {available}"
        super().__init__(message, "INSUFFICIENT_POINTS")
        self.user_id = user_id
        self.required = required
        self.available = available
        self.details = {
            "user_id": str(user_id),
            "required": required,
            "available": available
        }


class InvalidOrderException(TradingDomainException):
    """無效訂單異常"""
    
    def __init__(self, message: str, order_data: Dict[str, Any]):
        super().__init__(message, "INVALID_ORDER")
        self.order_data = order_data
        self.details = {"order_data": order_data}


class MarketClosedException(TradingDomainException):
    """市場關閉異常"""
    
    def __init__(self, message: str = "Market is closed"):
        super().__init__(message, "MARKET_CLOSED")


class InsufficientStockException(TradingDomainException):
    """股票不足異常"""
    
    def __init__(self, symbol: str, required: int, available: int):
        message = f"Insufficient stock {symbol}: required {required}, available {available}"
        super().__init__(message, "INSUFFICIENT_STOCK")
        self.symbol = symbol
        self.required = required
        self.available = available
        self.details = {
            "symbol": symbol,
            "required": required,
            "available": available
        }


class StudentNotExistsException(SystemDomainException):
    """學生不存在異常"""
    
    def __init__(self, student_id: str):
        message = f"Student with ID '{student_id}' does not exist"
        super().__init__(message, "STUDENT_NOT_EXISTS")
        self.student_id = student_id
        self.details = {"student_id": student_id}


class DebtAlreadyResolvedException(SystemDomainException):
    """債務已解決異常"""
    
    def __init__(self, debt_id: Any):
        message = f"Debt '{debt_id}' is already resolved"
        super().__init__(message, "DEBT_ALREADY_RESOLVED")
        self.debt_id = debt_id
        self.details = {"debt_id": str(debt_id)}


class InvalidPermissionException(AdminDomainException):
    """無效權限異常"""
    
    def __init__(self, permission: str, required_role: str):
        message = f"Permission '{permission}' requires role '{required_role}'"
        super().__init__(message, "INVALID_PERMISSION")
        self.permission = permission
        self.required_role = required_role
        self.details = {
            "permission": permission,
            "required_role": required_role
        }