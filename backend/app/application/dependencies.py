"""
Application Layer Dependencies (Dependency Injection)
"""
from __future__ import annotations
from functools import lru_cache
from app.domain.user.repositories import UserRepository, PointLogRepository
from app.infrastructure.database.repositories import MongoUserRepository, MongoPointLogRepository
from app.application.user.services import UserApplicationService


# Repository Dependencies
@lru_cache()
def get_user_repository() -> UserRepository:
    """獲取使用者存儲庫"""
    return MongoUserRepository()


@lru_cache()
def get_point_log_repository() -> PointLogRepository:
    """獲取點數記錄存儲庫"""
    return MongoPointLogRepository()


# Application Service Dependencies
@lru_cache()
def get_user_application_service() -> UserApplicationService:
    """獲取使用者應用服務"""
    return UserApplicationService(
        user_repository=get_user_repository(),
        point_log_repository=get_point_log_repository()
    )


# Legacy compatibility functions (for gradual migration)
def get_user_service() -> UserApplicationService:
    """向後兼容的使用者服務獲取函數"""
    return get_user_application_service()