"""
Infrastructure Setup and Integration
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from .config import get_config, ApplicationConfig
from .external.cache import create_cache_service
from .external.notification import create_notification_service
from .events.publisher import create_event_publisher, set_event_publisher
from .persistence.unit_of_work import create_unit_of_work
from ..application.common.interfaces import (
    CacheService,
    NotificationService,
    EventPublisher,
    UnitOfWork
)

logger = logging.getLogger(__name__)


class InfrastructureContainer:
    """基礎設施容器"""
    
    def __init__(self):
        self.config: Optional[ApplicationConfig] = None
        self.cache_service: Optional[CacheService] = None
        self.notification_service: Optional[NotificationService] = None
        self.event_publisher: Optional[EventPublisher] = None
        self.unit_of_work: Optional[UnitOfWork] = None
        self._initialized = False
    
    async def initialize(self):
        """初始化基礎設施"""
        if self._initialized:
            return
        
        logger.info("Initializing infrastructure components...")
        
        try:
            # 1. 加載配置
            self.config = get_config()
            logger.info(f"Configuration loaded for environment: {self.config.environment.value}")
            
            # 2. 設置日誌
            self._setup_logging()
            
            # 3. 初始化緩存服務
            self.cache_service = create_cache_service(self.config.cache.to_dict())
            logger.info(f"Cache service initialized with type: {self.config.cache.type}")
            
            # 4. 初始化通知服務
            self.notification_service = create_notification_service(self.config.notification.to_dict())
            logger.info("Notification service initialized")
            
            # 5. 初始化事件發布器
            self.event_publisher = create_event_publisher(self.config.events.to_dict())
            set_event_publisher(self.event_publisher)
            
            # 如果是內存事件發布器，啟動它
            if hasattr(self.event_publisher, 'start'):
                await self.event_publisher.start()
            
            logger.info(f"Event publisher initialized with type: {self.config.events.type}")
            
            # 6. 初始化 UnitOfWork
            self.unit_of_work = create_unit_of_work({'type': 'mongo'})
            logger.info("Unit of Work initialized")
            
            self._initialized = True
            logger.info("Infrastructure initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize infrastructure: {e}")
            await self.cleanup()
            raise
    
    def _setup_logging(self):
        """設置日誌配置"""
        logging_config = self.config.logging
        
        # 設置日誌級別
        log_level = getattr(logging, logging_config.level.upper(), logging.INFO)
        
        # 配置根日誌記錄器
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # 清除現有的處理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 格式化器
        formatter = logging.Formatter(logging_config.format)
        
        # 控制台輸出
        if logging_config.console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # 文件輸出
        if logging_config.file_path:
            from logging.handlers import RotatingFileHandler
            
            file_handler = RotatingFileHandler(
                logging_config.file_path,
                maxBytes=logging_config.max_file_size * 1024 * 1024,
                backupCount=logging_config.backup_count
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        logger.info(f"Logging configured with level: {logging_config.level}")
    
    async def cleanup(self):
        """清理資源"""
        if not self._initialized:
            return
        
        logger.info("Cleaning up infrastructure components...")
        
        try:
            # 清理事件發布器
            if self.event_publisher:
                if hasattr(self.event_publisher, 'stop'):
                    await self.event_publisher.stop()
                elif hasattr(self.event_publisher, 'cleanup'):
                    await self.event_publisher.cleanup()
            
            # 清理通知服務
            if self.notification_service:
                if hasattr(self.notification_service, 'cleanup'):
                    await self.notification_service.cleanup()
            
            # 清理緩存服務
            if self.cache_service:
                if hasattr(self.cache_service, 'cleanup'):
                    await self.cache_service.cleanup()
            
            logger.info("Infrastructure cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during infrastructure cleanup: {e}")
        
        finally:
            self._initialized = False
    
    def get_cache_service(self) -> CacheService:
        """獲取緩存服務"""
        if not self.cache_service:
            raise RuntimeError("Cache service not initialized")
        return self.cache_service
    
    def get_notification_service(self) -> NotificationService:
        """獲取通知服務"""
        if not self.notification_service:
            raise RuntimeError("Notification service not initialized")
        return self.notification_service
    
    def get_event_publisher(self) -> EventPublisher:
        """獲取事件發布器"""
        if not self.event_publisher:
            raise RuntimeError("Event publisher not initialized")
        return self.event_publisher
    
    def get_unit_of_work(self) -> UnitOfWork:
        """獲取 UnitOfWork"""
        if not self.unit_of_work:
            raise RuntimeError("Unit of Work not initialized")
        return self.unit_of_work
    
    def get_config(self) -> ApplicationConfig:
        """獲取配置"""
        if not self.config:
            raise RuntimeError("Configuration not loaded")
        return self.config
    
    def is_initialized(self) -> bool:
        """檢查是否已初始化"""
        return self._initialized
    
    @asynccontextmanager
    async def lifespan(self):
        """生命週期上下文管理器"""
        await self.initialize()
        try:
            yield self
        finally:
            await self.cleanup()


# 全局基礎設施容器
_global_infrastructure: Optional[InfrastructureContainer] = None


def get_infrastructure() -> InfrastructureContainer:
    """獲取全局基礎設施容器"""
    global _global_infrastructure
    if _global_infrastructure is None:
        _global_infrastructure = InfrastructureContainer()
    return _global_infrastructure


async def initialize_infrastructure():
    """初始化基礎設施"""
    infrastructure = get_infrastructure()
    await infrastructure.initialize()


async def cleanup_infrastructure():
    """清理基礎設施"""
    infrastructure = get_infrastructure()
    await infrastructure.cleanup()


@asynccontextmanager
async def infrastructure_lifespan():
    """基礎設施生命週期管理器"""
    infrastructure = get_infrastructure()
    async with infrastructure.lifespan():
        yield infrastructure


class InfrastructureHealthChecker:
    """基礎設施健康檢查器"""
    
    def __init__(self, container: InfrastructureContainer):
        self.container = container
    
    async def check_health(self) -> Dict[str, Any]:
        """檢查基礎設施健康狀態"""
        health_status = {
            "status": "healthy",
            "components": {},
            "timestamp": asyncio.get_event_loop().time()
        }
        
        try:
            # 檢查配置
            health_status["components"]["config"] = {
                "status": "healthy" if self.container.config else "unhealthy",
                "environment": self.container.config.environment.value if self.container.config else None
            }
            
            # 檢查緩存服務
            cache_status = await self._check_cache_service()
            health_status["components"]["cache"] = cache_status
            
            # 檢查通知服務
            notification_status = await self._check_notification_service()
            health_status["components"]["notification"] = notification_status
            
            # 檢查事件發布器
            event_status = await self._check_event_publisher()
            health_status["components"]["event_publisher"] = event_status
            
            # 檢查 UnitOfWork
            uow_status = await self._check_unit_of_work()
            health_status["components"]["unit_of_work"] = uow_status
            
            # 確定整體狀態
            component_statuses = [comp["status"] for comp in health_status["components"].values()]
            if any(status == "unhealthy" for status in component_statuses):
                health_status["status"] = "unhealthy"
            elif any(status == "degraded" for status in component_statuses):
                health_status["status"] = "degraded"
            
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
            logger.error(f"Health check failed: {e}")
        
        return health_status
    
    async def _check_cache_service(self) -> Dict[str, Any]:
        """檢查緩存服務"""
        try:
            if not self.container.cache_service:
                return {"status": "unhealthy", "message": "Cache service not initialized"}
            
            # 嘗試設置和獲取測試值
            test_key = "health_check_test"
            test_value = "ok"
            
            await self.container.cache_service.set(test_key, test_value, ttl=60)
            retrieved_value = await self.container.cache_service.get(test_key)
            
            if retrieved_value == test_value:
                await self.container.cache_service.delete(test_key)
                return {"status": "healthy", "type": self.container.config.cache.type}
            else:
                return {"status": "degraded", "message": "Cache read/write test failed"}
                
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def _check_notification_service(self) -> Dict[str, Any]:
        """檢查通知服務"""
        try:
            if not self.container.notification_service:
                return {"status": "unhealthy", "message": "Notification service not initialized"}
            
            # 通知服務通常難以進行健康檢查而不發送實際通知
            # 這裡只檢查服務是否已初始化
            return {"status": "healthy", "channels": self.container.config.notification.default_channels}
            
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def _check_event_publisher(self) -> Dict[str, Any]:
        """檢查事件發布器"""
        try:
            if not self.container.event_publisher:
                return {"status": "unhealthy", "message": "Event publisher not initialized"}
            
            # 檢查事件發布器指標
            if hasattr(self.container.event_publisher, 'get_metrics'):
                metrics = self.container.event_publisher.get_metrics()
                return {"status": "healthy", "type": self.container.config.events.type, "metrics": metrics}
            
            return {"status": "healthy", "type": self.container.config.events.type}
            
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def _check_unit_of_work(self) -> Dict[str, Any]:
        """檢查 UnitOfWork"""
        try:
            if not self.container.unit_of_work:
                return {"status": "unhealthy", "message": "Unit of Work not initialized"}
            
            # 檢查是否可以創建事務
            if hasattr(self.container.unit_of_work, 'is_in_transaction'):
                return {"status": "healthy", "type": "mongo"}
            
            return {"status": "healthy", "type": "mongo"}
            
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


async def get_infrastructure_health() -> Dict[str, Any]:
    """獲取基礎設施健康狀態"""
    infrastructure = get_infrastructure()
    health_checker = InfrastructureHealthChecker(infrastructure)
    return await health_checker.check_health()


# 便利函數
async def get_cache_service() -> CacheService:
    """獲取緩存服務"""
    return get_infrastructure().get_cache_service()


async def get_notification_service() -> NotificationService:
    """獲取通知服務"""
    return get_infrastructure().get_notification_service()


async def get_event_publisher_service() -> EventPublisher:
    """獲取事件發布器服務"""
    return get_infrastructure().get_event_publisher()


async def get_unit_of_work_service() -> UnitOfWork:
    """獲取 UnitOfWork 服務"""
    return get_infrastructure().get_unit_of_work()