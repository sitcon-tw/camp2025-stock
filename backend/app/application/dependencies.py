# 依賴注入容器
# DIP 原則：通過依賴注入實作控制反轉
# SRP 原則：專注於依賴關係的組織和管理

from functools import lru_cache
from app.core.database import get_database
from app.domain.services import (
    UserDomainService, StockTradingService, TransferService, IPOService
)
from app.infrastructure.mongodb_repositories import (
    MongoUserRepository, MongoStockRepository, MongoStockOrderRepository,
    MongoTransferRepository, MongoMarketConfigRepository
)
from app.application.services import (
    UserApplicationService, TradingApplicationService, 
    TransferApplicationService, IPOApplicationService
)


class ServiceContainer:
    """
    服務容器
    DIP 原則：集中管理依賴關係，實作控制反轉
    Singleton 模式：確保依賴關係的一致性
    """
    
    def __init__(self):
        self._db = get_database()
        self._repositories = {}
        self._domain_services = {}
        self._application_services = {}
    
    # Repository 層
    @property
    def user_repository(self) -> MongoUserRepository:
        """用戶資料存取層 - 懶加載"""
        if 'user' not in self._repositories:
            self._repositories['user'] = MongoUserRepository(self._db)
        return self._repositories['user']
    
    @property
    def stock_repository(self) -> MongoStockRepository:
        """股票資料存取層 - 懶加載"""
        if 'stock' not in self._repositories:
            self._repositories['stock'] = MongoStockRepository(self._db)
        return self._repositories['stock']
    
    @property
    def stock_order_repository(self) -> MongoStockOrderRepository:
        """訂單資料存取層 - 懶加載"""
        if 'stock_order' not in self._repositories:
            self._repositories['stock_order'] = MongoStockOrderRepository(self._db)
        return self._repositories['stock_order']
    
    @property
    def transfer_repository(self) -> MongoTransferRepository:
        """轉帳資料存取層 - 懶加載"""
        if 'transfer' not in self._repositories:
            self._repositories['transfer'] = MongoTransferRepository(self._db)
        return self._repositories['transfer']
    
    @property
    def market_config_repository(self) -> MongoMarketConfigRepository:
        """市場設定資料存取層 - 懶加載"""
        if 'market_config' not in self._repositories:
            self._repositories['market_config'] = MongoMarketConfigRepository(self._db)
        return self._repositories['market_config']
    
    # Domain Service 層
    @property
    def user_domain_service(self) -> UserDomainService:
        """用戶領域服務 - 依賴注入"""
        if 'user' not in self._domain_services:
            self._domain_services['user'] = UserDomainService(self.user_repository)
        return self._domain_services['user']
    
    @property
    def stock_trading_service(self) -> StockTradingService:
        """股票交易領域服務 - 依賴注入"""
        if 'stock_trading' not in self._domain_services:
            self._domain_services['stock_trading'] = StockTradingService(
                self.user_repository,
                self.stock_repository,
                self.stock_order_repository,
                self.market_config_repository
            )
        return self._domain_services['stock_trading']
    
    @property
    def transfer_service(self) -> TransferService:
        """轉帳領域服務 - 依賴注入"""
        if 'transfer' not in self._domain_services:
            self._domain_services['transfer'] = TransferService(
                self.user_repository,
                self.transfer_repository
            )
        return self._domain_services['transfer']
    
    @property
    def ipo_service(self) -> IPOService:
        """IPO 領域服務 - 依賴注入"""
        if 'ipo' not in self._domain_services:
            self._domain_services['ipo'] = IPOService(
                self.user_repository,
                self.stock_repository,
                self.market_config_repository
            )
        return self._domain_services['ipo']
    
    # Application Service 層
    @property
    def user_application_service(self) -> UserApplicationService:
        """用戶應用服務 - 依賴注入"""
        if 'user' not in self._application_services:
            self._application_services['user'] = UserApplicationService(
                self.user_domain_service
            )
        return self._application_services['user']
    
    @property
    def trading_application_service(self) -> TradingApplicationService:
        """交易應用服務 - 依賴注入"""
        if 'trading' not in self._application_services:
            self._application_services['trading'] = TradingApplicationService(
                self.stock_trading_service,
                self.user_repository,
                self.stock_repository,
                self.stock_order_repository
            )
        return self._application_services['trading']
    
    @property
    def transfer_application_service(self) -> TransferApplicationService:
        """轉帳應用服務 - 依賴注入"""
        if 'transfer' not in self._application_services:
            self._application_services['transfer'] = TransferApplicationService(
                self.transfer_service,
                self.transfer_repository
            )
        return self._application_services['transfer']
    
    @property
    def ipo_application_service(self) -> IPOApplicationService:
        """IPO 應用服務 - 依賴注入"""
        if 'ipo' not in self._application_services:
            self._application_services['ipo'] = IPOApplicationService(
                self.ipo_service
            )
        return self._application_services['ipo']


# 全域服務容器實例
@lru_cache()
def get_service_container() -> ServiceContainer:
    """
    獲取服務容器單例
    Singleton 模式：確保整個應用中只有一個服務容器實例
    """
    return ServiceContainer()


# FastAPI 依賴注入函數
def get_user_application_service() -> UserApplicationService:
    """DIP 原則：通過依賴注入提供用戶應用服務"""
    return get_service_container().user_application_service


def get_trading_application_service() -> TradingApplicationService:
    """DIP 原則：通過依賴注入提供交易應用服務"""
    return get_service_container().trading_application_service


def get_transfer_application_service() -> TransferApplicationService:
    """DIP 原則：通過依賴注入提供轉帳應用服務"""
    return get_service_container().transfer_application_service


def get_ipo_application_service() -> IPOApplicationService:
    """DIP 原則：通過依賴注入提供 IPO 應用服務"""
    return get_service_container().ipo_application_service