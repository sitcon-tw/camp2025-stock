"""
DDD Application Service Container
"""
from __future__ import annotations
from functools import lru_cache
import logging
from typing import Optional

# Domain Repositories
from app.domain.user.repositories import UserRepository, PointLogRepository
from app.domain.trading.repositories import StockRepository, OrderRepository, UserStockRepository
from app.domain.market.repositories import MarketConfigRepository, IPOConfigRepository, AnnouncementRepository

# Infrastructure Implementations
from app.infrastructure.database.repositories import (
    MongoUserRepository, MongoPointLogRepository,
    MongoStockRepository, MongoOrderRepository, MongoUserStockRepository
)

# Application Services
from app.application.user.services import UserApplicationService
from app.application.trading.services import TradingApplicationService

# Domain Services
from app.domain.user.services import UserDomainService
from app.domain.trading.services import TradingDomainService
from app.domain.market.services import MarketDomainService
from app.domain.admin.services import AdminDomainService

logger = logging.getLogger(__name__)


class DDDServiceContainer:
    """DDD 應用服務容器"""
    
    def __init__(self):
        self._repositories = {}
        self._domain_services = {}
        self._application_services = {}
        self._initialized = False
    
    # Repository Layer
    @property
    def user_repository(self) -> UserRepository:
        """使用者存儲庫"""
        if 'user' not in self._repositories:
            self._repositories['user'] = MongoUserRepository()
        return self._repositories['user']
    
    @property
    def point_log_repository(self) -> PointLogRepository:
        """點數記錄存儲庫"""
        if 'point_log' not in self._repositories:
            self._repositories['point_log'] = MongoPointLogRepository()
        return self._repositories['point_log']
    
    @property
    def stock_repository(self) -> StockRepository:
        """股票存儲庫"""
        if 'stock' not in self._repositories:
            self._repositories['stock'] = MongoStockRepository()
        return self._repositories['stock']
    
    @property
    def order_repository(self) -> OrderRepository:
        """訂單存儲庫"""
        if 'order' not in self._repositories:
            self._repositories['order'] = MongoOrderRepository()
        return self._repositories['order']
    
    @property
    def user_stock_repository(self) -> UserStockRepository:
        """使用者股票存儲庫"""
        if 'user_stock' not in self._repositories:
            self._repositories['user_stock'] = MongoUserStockRepository()
        return self._repositories['user_stock']
    
    # Domain Service Layer
    @property
    def user_domain_service(self) -> UserDomainService:
        """使用者領域服務"""
        if 'user' not in self._domain_services:
            self._domain_services['user'] = UserDomainService(
                user_repository=self.user_repository,
                point_log_repository=self.point_log_repository
            )
        return self._domain_services['user']
    
    @property
    def trading_domain_service(self) -> TradingDomainService:
        """交易領域服務"""
        if 'trading' not in self._domain_services:
            self._domain_services['trading'] = TradingDomainService(
                stock_repository=self.stock_repository,
                order_repository=self.order_repository,
                user_stock_repository=self.user_stock_repository,
                user_repository=self.user_repository
            )
        return self._domain_services['trading']
    
    @property
    def admin_domain_service(self) -> AdminDomainService:
        """管理員領域服務"""
        if 'admin' not in self._domain_services:
            self._domain_services['admin'] = AdminDomainService(
                user_repository=self.user_repository
            )
        return self._domain_services['admin']
    
    # Application Service Layer
    @property
    def user_application_service(self) -> UserApplicationService:
        """使用者應用服務"""
        if 'user' not in self._application_services:
            self._application_services['user'] = UserApplicationService(
                user_repository=self.user_repository,
                point_log_repository=self.point_log_repository
            )
        return self._application_services['user']
    
    @property
    def trading_application_service(self) -> TradingApplicationService:
        """交易應用服務"""
        if 'trading' not in self._application_services:
            self._application_services['trading'] = TradingApplicationService(
                stock_repository=self.stock_repository,
                order_repository=self.order_repository,
                user_stock_repository=self.user_stock_repository,
                user_repository=self.user_repository
            )
        return self._application_services['trading']
    
    # Service Lifecycle Management
    async def initialize(self) -> None:
        """初始化服務容器"""
        if self._initialized:
            return
        
        try:
            logger.info("Initializing DDD service container...")
            
            # 驗證關鍵服務
            await self._validate_services()
            
            self._initialized = True
            logger.info("DDD service container initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize DDD service container: {e}")
            raise
    
    async def cleanup(self) -> None:
        """清理服務容器"""
        if not self._initialized:
            return
        
        try:
            logger.info("Cleaning up DDD service container...")
            
            # 清理應用服務
            self._application_services.clear()
            
            # 清理領域服務
            self._domain_services.clear()
            
            # 清理存儲庫
            self._repositories.clear()
            
            self._initialized = False
            logger.info("DDD service container cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Failed to cleanup DDD service container: {e}")
    
    async def _validate_services(self) -> None:
        """驗證服務狀態"""
        try:
            # 驗證關鍵服務實例化
            user_service = self.user_application_service
            trading_service = self.trading_application_service
            
            logger.info("All DDD services validated successfully")
            
        except Exception as e:
            logger.error(f"Service validation failed: {e}")
            raise
    
    def get_health_status(self) -> dict:
        """獲取健康狀態"""
        return {
            "initialized": self._initialized,
            "repositories": len(self._repositories),
            "domain_services": len(self._domain_services),
            "application_services": len(self._application_services),
            "services": {
                "user_service": "healthy" if 'user' in self._application_services else "not_loaded",
                "trading_service": "healthy" if 'trading' in self._application_services else "not_loaded",
                "user_domain_service": "healthy" if 'user' in self._domain_services else "not_loaded",
                "trading_domain_service": "healthy" if 'trading' in self._domain_services else "not_loaded"
            }
        }


# Global service container instance
_service_container: Optional[DDDServiceContainer] = None


@lru_cache()
def get_service_container() -> DDDServiceContainer:
    """獲取服務容器單例"""
    global _service_container
    if _service_container is None:
        _service_container = DDDServiceContainer()
    return _service_container


# Backward compatibility functions
def get_user_service() -> UserApplicationService:
    """向後兼容的使用者服務獲取函數"""
    return get_service_container().user_application_service


def get_trading_service() -> TradingApplicationService:
    """向後兼容的交易服務獲取函數"""
    return get_service_container().trading_application_service


def get_user_application_service() -> UserApplicationService:
    """獲取使用者應用服務"""
    return get_service_container().user_application_service


def get_trading_application_service() -> TradingApplicationService:
    """獲取交易應用服務"""
    return get_service_container().trading_application_service