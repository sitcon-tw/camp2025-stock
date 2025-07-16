"""
Application Layer Dependencies (Dependency Injection)
"""
from __future__ import annotations
from functools import lru_cache
from app.domain.user.repositories import UserRepository, PointLogRepository
from app.infrastructure.database.repositories import MongoUserRepository, MongoPointLogRepository
from app.application.user.services import UserApplicationService
from app.domain.trading.repositories import StockRepository, OrderRepository, UserStockRepository
from app.infrastructure.database.repositories import MongoStockRepository, MongoOrderRepository, MongoUserStockRepository
from app.application.trading.services import TradingApplicationService


# Repository Dependencies
@lru_cache()
def get_user_repository() -> UserRepository:
    """獲取使用者存儲庫"""
    return MongoUserRepository()


@lru_cache()
def get_point_log_repository() -> PointLogRepository:
    """獲取點數記錄存儲庫"""
    return MongoPointLogRepository()


@lru_cache()
def get_stock_repository() -> StockRepository:
    """獲取股票存儲庫"""
    return MongoStockRepository()


@lru_cache()
def get_order_repository() -> OrderRepository:
    """獲取訂單存儲庫"""
    return MongoOrderRepository()


@lru_cache()
def get_user_stock_repository() -> UserStockRepository:
    """獲取使用者股票存儲庫"""
    return MongoUserStockRepository()


# Application Service Dependencies
@lru_cache()
def get_user_application_service() -> UserApplicationService:
    """獲取使用者應用服務"""
    # 使用 DDD 服務容器獲取服務
    from app.application.container import get_service_container
    container = get_service_container()
    return container.user_application_service


@lru_cache()
def get_trading_application_service() -> TradingApplicationService:
    """獲取交易應用服務"""
    # 使用 DDD 服務容器獲取服務
    from app.application.container import get_service_container
    container = get_service_container()
    return container.trading_application_service


# Legacy compatibility functions (for gradual migration)
def get_user_service() -> UserApplicationService:
    """向後兼容的使用者服務獲取函數"""
    return get_user_application_service()


def get_trading_service() -> TradingApplicationService:
    """向後兼容的交易服務獲取函數"""
    return get_trading_application_service()