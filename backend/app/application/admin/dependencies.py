# 管理員應用服務依賴注入
# DDD Dependency Injection for Admin Services

from typing import Optional
from functools import lru_cache

from .services import AdminApplicationService
from app.domain.admin.services import AdminDomainService
from app.domain.user.services import UserDomainService
from app.domain.market.services import MarketDomainService
from app.infrastructure.database.repositories import (
    MongoUserRepository,
    MongoPointLogRepository, 
    MongoStockRepository,
    MongoTradeRepository
)
from app.core.database import get_database


# Singleton pattern for service instances
_admin_application_service: Optional[AdminApplicationService] = None
_admin_domain_service: Optional[AdminDomainService] = None


async def get_admin_domain_service() -> AdminDomainService:
    """取得管理員領域服務實例"""
    global _admin_domain_service
    
    if _admin_domain_service is None:
        db = await get_database()
        
        # 初始化所需的 repositories
        user_repository = MongoUserRepository(db)
        point_log_repository = MongoPointLogRepository(db)
        stock_repository = MongoStockRepository(db)
        trade_repository = MongoTradeRepository(db)
        
        _admin_domain_service = AdminDomainService(
            user_repository=user_repository,
            point_log_repository=point_log_repository,
            stock_repository=stock_repository,
            trade_repository=trade_repository
        )
    
    return _admin_domain_service


async def get_user_domain_service() -> UserDomainService:
    """取得使用者領域服務實例"""
    # 這裡應該從其他地方獲取，暫時回傳 None
    # 實際實現需要從 user domain service dependencies 取得
    return None


async def get_market_domain_service() -> MarketDomainService:
    """取得市場領域服務實例"""
    # 這裡應該從其他地方獲取，暫時回傳 None
    # 實際實現需要從 market domain service dependencies 取得
    return None


async def get_admin_application_service() -> AdminApplicationService:
    """取得管理員應用服務實例"""
    global _admin_application_service
    
    if _admin_application_service is None:
        admin_domain_service = await get_admin_domain_service()
        user_domain_service = await get_user_domain_service()
        market_domain_service = await get_market_domain_service()
        
        _admin_application_service = AdminApplicationService(
            admin_domain_service=admin_domain_service,
            user_domain_service=user_domain_service,
            market_domain_service=market_domain_service
        )
    
    return _admin_application_service


# Legacy compatibility function
async def get_admin_service() -> AdminApplicationService:
    """
    Legacy compatibility function
    向後相容性函數，供現有的路由器使用
    """
    return await get_admin_application_service()


def cleanup_admin_services():
    """清理服務實例 - 主要用於測試或重新初始化"""
    global _admin_application_service, _admin_domain_service
    _admin_application_service = None
    _admin_domain_service = None