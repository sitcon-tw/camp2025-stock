"""
Enhanced Dependency Injection Container
"""
from __future__ import annotations
from typing import Type, TypeVar, Dict, Any, Optional, Callable
from functools import lru_cache
import logging
from contextlib import asynccontextmanager

from app.domain.common.repositories import UnitOfWork
from app.domain.common.events import DomainEventBus
from app.domain.common.exceptions import ConfigurationException

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceLifetime:
    """服務生命週期枚舉"""
    SINGLETON = "singleton"
    SCOPED = "scoped"
    TRANSIENT = "transient"


class ServiceDescriptor:
    """服務描述符"""
    
    def __init__(self, service_type: Type[T], implementation: Type[T], lifetime: str = ServiceLifetime.SINGLETON):
        self.service_type = service_type
        self.implementation = implementation
        self.lifetime = lifetime
        self.instance = None
        self.factory = None


class DIContainer:
    """
    增強的依賴注入容器
    支援生命週期管理、循環依賴檢測、作用域管理
    """
    
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scoped_instances: Dict[Type, Any] = {}
        self._building_stack: set = set()
        self._initialized = False
        self._event_bus: Optional[DomainEventBus] = None
        self._unit_of_work: Optional[UnitOfWork] = None
    
    def register_singleton(self, service_type: Type[T], implementation: Type[T]) -> 'DIContainer':
        """註冊單例服務"""
        self._services[service_type] = ServiceDescriptor(service_type, implementation, ServiceLifetime.SINGLETON)
        return self
    
    def register_scoped(self, service_type: Type[T], implementation: Type[T]) -> 'DIContainer':
        """註冊作用域服務"""
        self._services[service_type] = ServiceDescriptor(service_type, implementation, ServiceLifetime.SCOPED)
        return self
    
    def register_transient(self, service_type: Type[T], implementation: Type[T]) -> 'DIContainer':
        """註冊瞬態服務"""
        self._services[service_type] = ServiceDescriptor(service_type, implementation, ServiceLifetime.TRANSIENT)
        return self
    
    def register_instance(self, service_type: Type[T], instance: T) -> 'DIContainer':
        """註冊實例"""
        self._singletons[service_type] = instance
        return self
    
    def register_factory(self, service_type: Type[T], factory: Callable[['DIContainer'], T], 
                        lifetime: str = ServiceLifetime.SINGLETON) -> 'DIContainer':
        """註冊工廠函數"""
        descriptor = ServiceDescriptor(service_type, None, lifetime)
        descriptor.factory = factory
        self._services[service_type] = descriptor
        return self
    
    async def get(self, service_type: Type[T]) -> T:
        """異步獲取服務（向後兼容）"""
        return self.resolve(service_type)
    
    def resolve(self, service_type: Type[T]) -> T:
        """解析服務"""
        if not self._initialized:
            raise ConfigurationException("Container not initialized", "container_state", "not_initialized")
        
        # 檢查是否已有實例
        if service_type in self._singletons:
            return self._singletons[service_type]
        
        if service_type in self._scoped_instances:
            return self._scoped_instances[service_type]
        
        # 檢查循環依賴
        if service_type in self._building_stack:
            raise ConfigurationException(f"Circular dependency detected for {service_type}", 
                                       "circular_dependency", str(service_type))
        
        # 查找服務描述符
        if service_type not in self._services:
            raise ConfigurationException(f"Service {service_type} not registered", 
                                       "service_not_registered", str(service_type))
        
        descriptor = self._services[service_type]
        
        self._building_stack.add(service_type)
        try:
            instance = self._create_instance(descriptor)
            
            # 根據生命週期存儲實例
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                self._singletons[service_type] = instance
            elif descriptor.lifetime == ServiceLifetime.SCOPED:
                self._scoped_instances[service_type] = instance
            
            return instance
        finally:
            self._building_stack.remove(service_type)
    
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """創建服務實例"""
        if descriptor.factory:
            return descriptor.factory(self)
        
        if descriptor.implementation is None:
            raise ConfigurationException(f"No implementation for {descriptor.service_type}", 
                                       "no_implementation", str(descriptor.service_type))
        
        # 獲取構造函數參數
        import inspect
        signature = inspect.signature(descriptor.implementation.__init__)
        parameters = signature.parameters
        
        # 解析依賴
        kwargs = {}
        for param_name, param in parameters.items():
            if param_name == 'self':
                continue
            
            if param.annotation == inspect.Parameter.empty:
                raise ConfigurationException(f"Parameter {param_name} has no type annotation", 
                                           "missing_annotation", param_name)
            
            kwargs[param_name] = self.resolve(param.annotation)
        
        return descriptor.implementation(**kwargs)
    
    @asynccontextmanager
    async def create_scope(self):
        """創建作用域"""
        old_scoped = self._scoped_instances.copy()
        self._scoped_instances.clear()
        
        try:
            yield self
        finally:
            # 清理作用域實例
            for instance in self._scoped_instances.values():
                if hasattr(instance, 'dispose'):
                    await instance.dispose()
            
            self._scoped_instances = old_scoped
    
    async def initialize(self) -> None:
        """初始化容器"""
        if self._initialized:
            return
        
        try:
            logger.info("Initializing DI container...")
            
            # 創建事件總線
            if self._event_bus is None:
                import importlib.util
                import os
                events_file = os.path.join(os.path.dirname(__file__), "events.py")
                spec = importlib.util.spec_from_file_location("events_module", events_file)
                events_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(events_module)
                self._event_bus = events_module.InMemoryEventBus()
            
            # 初始化核心服務
            await self._initialize_core_services()
            
            self._initialized = True
            logger.info("DI container initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize DI container: {e}")
            raise
    
    async def _initialize_core_services(self) -> None:
        """初始化核心服務"""
        # 這裡可以預初始化一些核心服務
        pass
    
    async def dispose(self) -> None:
        """清理容器"""
        if not self._initialized:
            return
        
        try:
            logger.info("Disposing DI container...")
            
            # 清理單例實例
            for instance in self._singletons.values():
                if hasattr(instance, 'dispose'):
                    await instance.dispose()
            
            # 清理作用域實例
            for instance in self._scoped_instances.values():
                if hasattr(instance, 'dispose'):
                    await instance.dispose()
            
            # 清理事件總線
            if self._event_bus and hasattr(self._event_bus, 'dispose'):
                await self._event_bus.dispose()
            
            self._singletons.clear()
            self._scoped_instances.clear()
            self._initialized = False
            
            logger.info("DI container disposed successfully")
            
        except Exception as e:
            logger.error(f"Error during container disposal: {e}")
    
    def get_event_bus(self) -> DomainEventBus:
        """獲取事件總線"""
        if self._event_bus is None:
            raise ConfigurationException("Event bus not initialized", "event_bus", "not_initialized")
        return self._event_bus
    
    def set_event_bus(self, event_bus: DomainEventBus) -> None:
        """設置事件總線"""
        self._event_bus = event_bus
    
    def get_unit_of_work(self) -> UnitOfWork:
        """獲取工作單元"""
        if self._unit_of_work is None:
            raise ConfigurationException("Unit of work not initialized", "unit_of_work", "not_initialized")
        return self._unit_of_work
    
    def set_unit_of_work(self, unit_of_work: UnitOfWork) -> None:
        """設置工作單元"""
        self._unit_of_work = unit_of_work
    
    def get_health_status(self) -> Dict[str, Any]:
        """獲取健康狀態"""
        return {
            "initialized": self._initialized,
            "registered_services": len(self._services),
            "singleton_instances": len(self._singletons),
            "scoped_instances": len(self._scoped_instances),
            "event_bus_initialized": self._event_bus is not None,
            "unit_of_work_initialized": self._unit_of_work is not None
        }


# 全局容器實例
_container: Optional[DIContainer] = None


@lru_cache()
def get_container() -> DIContainer:
    """獲取全局容器實例"""
    global _container
    if _container is None:
        _container = DIContainer()
    return _container


def configure_container() -> DIContainer:
    """配置容器"""
    container = get_container()
    
    # 註冊核心服務
    _register_repositories(container)
    _register_domain_services(container)
    _register_application_services(container)
    _register_infrastructure_services(container)
    
    return container


def _register_repositories(container: DIContainer) -> None:
    """註冊存儲庫"""
    from app.domain.user.repositories import UserRepository, PointLogRepository
    from app.domain.trading.repositories import StockRepository, OrderRepository, UserStockRepository
    from app.domain.system.repositories import StudentRepository, UserDebtRepository
    from app.infrastructure.database.repositories import (
        MongoUserRepository, MongoPointLogRepository,
        MongoStockRepository, MongoOrderRepository, MongoUserStockRepository,
        MongoStudentRepository, MongoUserDebtRepository
    )
    
    container.register_singleton(UserRepository, MongoUserRepository)
    container.register_singleton(PointLogRepository, MongoPointLogRepository)
    container.register_singleton(StockRepository, MongoStockRepository)
    container.register_singleton(OrderRepository, MongoOrderRepository)
    container.register_singleton(UserStockRepository, MongoUserStockRepository)
    container.register_singleton(StudentRepository, MongoStudentRepository)
    container.register_singleton(UserDebtRepository, MongoUserDebtRepository)


def _register_domain_services(container: DIContainer) -> None:
    """註冊領域服務"""
    from app.domain.user.services import UserDomainService
    from app.domain.trading.services import TradingDomainService
    from app.domain.trading.data_services import TradingDataDomainService
    from app.domain.market.services import MarketDomainService
    from app.domain.market.data_services import MarketDataDomainService
    from app.domain.admin.services import AdminDomainService
    from app.domain.system.services import DebtDomainService, StudentDomainService
    from app.domain.auth.services import RBACDomainService
    
    container.register_singleton(UserDomainService, UserDomainService)
    container.register_singleton(TradingDomainService, TradingDomainService)
    container.register_singleton(TradingDataDomainService, TradingDataDomainService)
    container.register_singleton(MarketDomainService, MarketDomainService)
    container.register_singleton(MarketDataDomainService, MarketDataDomainService)
    container.register_singleton(AdminDomainService, AdminDomainService)
    container.register_singleton(DebtDomainService, DebtDomainService)
    container.register_singleton(StudentDomainService, StudentDomainService)
    container.register_singleton(RBACDomainService, RBACDomainService)


def _register_application_services(container: DIContainer) -> None:
    """註冊應用服務"""
    from app.application.admin.services import AdminApplicationService
    from app.application.user.authentication_service import UserAuthenticationApplicationService
    from app.application.user.portfolio_service import UserPortfolioApplicationService
    from app.application.trading.services import TradingApplicationService
    from app.application.public.services import PublicApplicationService
    from app.application.auth.services import RBACApplicationService
    
    # Legacy services for backward compatibility
    from app.application.user.services import UserApplicationService
    
    container.register_scoped(AdminApplicationService, AdminApplicationService)
    container.register_scoped(UserAuthenticationApplicationService, UserAuthenticationApplicationService)
    container.register_scoped(UserPortfolioApplicationService, UserPortfolioApplicationService)
    container.register_scoped(TradingApplicationService, TradingApplicationService)
    container.register_scoped(PublicApplicationService, PublicApplicationService)
    container.register_scoped(RBACApplicationService, RBACApplicationService)
    
    # Legacy compatibility
    container.register_scoped(UserApplicationService, UserApplicationService)


def _register_infrastructure_services(container: DIContainer) -> None:
    """註冊基礎設施服務"""
    from app.infrastructure.database.unit_of_work import MongoUnitOfWork
    import importlib.util
    import os
    
    # Import InMemoryEventBus from events.py file to avoid conflict with events/ directory
    events_file = os.path.join(os.path.dirname(__file__), "events.py")
    spec = importlib.util.spec_from_file_location("events_module", events_file)
    events_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(events_module)
    
    container.register_singleton(UnitOfWork, MongoUnitOfWork)
    container.register_singleton(DomainEventBus, events_module.InMemoryEventBus)


# Legacy compatibility functions - 向後相容性函數
async def get_admin_service():
    """向後相容：取得管理員服務"""
    from app.application.admin.services import AdminApplicationService
    container = configure_container()
    await container.initialize()
    return container.resolve(AdminApplicationService)


async def get_user_service():
    """向後相容：取得使用者服務"""
    from app.application.user.services import UserApplicationService
    container = configure_container()
    await container.initialize()
    return container.resolve(UserApplicationService)


async def get_trading_service():
    """向後相容：取得交易服務"""
    from app.application.trading.services import TradingApplicationService
    container = configure_container()
    await container.initialize()
    return container.resolve(TradingApplicationService)


async def get_debt_service():
    """向後相容：取得債務服務"""
    from app.domain.system.services import DebtDomainService
    container = configure_container()
    await container.initialize()
    return container.resolve(DebtDomainService)


async def get_student_service():
    """向後相容：取得學生服務"""
    from app.domain.system.services import StudentDomainService
    container = configure_container()
    await container.initialize()
    return container.resolve(StudentDomainService)


async def get_user_authentication_service():
    """取得使用者認證服務"""
    from app.application.user.authentication_service import UserAuthenticationApplicationService
    container = configure_container()
    await container.initialize()
    return container.resolve(UserAuthenticationApplicationService)


async def get_user_portfolio_service():
    """取得使用者投資組合服務"""
    from app.application.user.portfolio_service import UserPortfolioApplicationService
    container = configure_container()
    await container.initialize()
    return container.resolve(UserPortfolioApplicationService)


async def get_public_service():
    """向後相容：取得公開服務"""
    from app.application.public.services import PublicApplicationService
    container = configure_container()
    await container.initialize()
    return container.resolve(PublicApplicationService)


async def get_rbac_management_service():
    """向後相容：取得RBAC管理服務"""
    from app.application.auth.services import RBACApplicationService
    container = configure_container()
    await container.initialize()
    return container.resolve(RBACApplicationService)