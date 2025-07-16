"""
Shared Domain Exceptions
"""


class DomainException(Exception):
    """領域異常基類"""
    pass


class ValidationException(DomainException):
    """驗證異常"""
    pass


class BusinessRuleException(DomainException):
    """業務規則異常"""
    pass


class ResourceNotFoundException(DomainException):
    """資源未找到異常"""
    pass


class InsufficientBalanceException(DomainException):
    """餘額不足異常"""
    pass


class UnauthorizedException(DomainException):
    """未授權異常"""
    pass


class ConcurrencyException(DomainException):
    """並發異常"""
    pass