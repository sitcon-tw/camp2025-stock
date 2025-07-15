"""
分散式系統整合器 - 整合所有分散式組件
提供統一的初始化、配置和管理接口
"""

import asyncio
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timezone

from .sharding_service import initialize_sharding_service, get_sharding_service
from .event_bus_service import (
    initialize_event_bus_service, 
    get_event_bus_service,
    OrderEventHandler,
    UserEventHandler,
    MarketEventHandler
)
from .sharded_order_processor import initialize_sharded_order_processor, get_sharded_order_processor
from .order_queue_service import initialize_order_queue_service, get_order_queue_service

logger = logging.getLogger(__name__)

class DistributedSystemConfig:
    """分散式系統配置"""
    
    def __init__(self):
        # 分片配置
        self.num_shards = 16
        self.shard_max_load = 1000
        
        # 事件匯流配置
        self.max_event_history = 10000
        self.event_retry_max = 3
        
        # 佇列配置
        self.queue_batch_size = 100
        self.queue_timeout = 30.0
        
        # 性能配置
        self.enable_fast_path = True
        self.enable_batch_processing = True
        self.enable_auto_rebalancing = True
        
        # 監控配置
        self.metrics_interval = 60.0  # 秒
        self.health_check_interval = 30.0  # 秒

class DistributedSystemIntegrator:
    """
    分散式系統整合器
    
    功能：
    1. 統一初始化所有分散式組件
    2. 配置組件間的協作關係
    3. 提供系統健康檢查
    4. 處理系統重啟和故障恢復
    5. 統一的監控和統計接口
    """
    
    def __init__(self, config: DistributedSystemConfig = None):
        self.config = config or DistributedSystemConfig()
        self.is_initialized = False
        self.start_time = None
        
        # 服務引用
        self.user_service = None
        self.sharding_service = None
        self.event_bus_service = None
        self.order_queue_service = None
        self.sharded_order_processor = None
        
        # 系統統計
        self.system_stats = {
            "initialization_time": None,
            "uptime": 0,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0,
            "last_health_check": None,
            "health_status": "unknown"
        }
        
        # 後台任務
        self.background_tasks = []
        
        logger.info("DistributedSystemIntegrator created")
    
    async def initialize(self, user_service) -> bool:
        """初始化整個分散式系統"""
        
        if self.is_initialized:
            logger.warning("Distributed system already initialized")
            return True
        
        try:
            start_time = datetime.now(timezone.utc)
            logger.info("Starting distributed system initialization...")
            
            self.user_service = user_service
            
            # 第一步：初始化分片服務
            logger.info("Initializing sharding service...")
            self.sharding_service = initialize_sharding_service(self.config.num_shards)
            
            # 第二步：初始化事件匯流服務
            logger.info("Initializing event bus service...")
            self.event_bus_service = await initialize_event_bus_service(self.config.max_event_history)
            
            # 第三步：註冊事件處理器
            logger.info("Registering event handlers...")
            await self._register_event_handlers()
            
            # 第四步：初始化訂單佇列服務
            logger.info("Initializing order queue service...")
            self.order_queue_service = await initialize_order_queue_service(user_service)
            
            # 第五步：初始化分片訂單處理器
            logger.info("Initializing sharded order processor...")
            self.sharded_order_processor = await initialize_sharded_order_processor(
                user_service, 
                self.config.num_shards
            )
            
            # 第六步：啟動後台任務
            logger.info("Starting background tasks...")
            await self._start_background_tasks()
            
            # 記錄初始化完成
            end_time = datetime.now(timezone.utc)
            initialization_time = (end_time - start_time).total_seconds()
            
            self.is_initialized = True
            self.start_time = start_time
            self.system_stats["initialization_time"] = initialization_time
            self.system_stats["health_status"] = "healthy"
            
            logger.info(f"Distributed system initialized successfully in {initialization_time:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize distributed system: {e}")
            await self._cleanup_partial_initialization()
            return False
    
    async def _register_event_handlers(self):
        """註冊事件處理器"""
        
        # 訂單事件處理器
        order_handler = OrderEventHandler(
            user_service=self.user_service,
            order_service=None  # 暫時沒有獨立的訂單服務
        )
        self.event_bus_service.subscribe(order_handler)
        
        # 使用者事件處理器
        user_handler = UserEventHandler(
            user_service=self.user_service,
            notification_service=None  # 暫時沒有通知服務
        )
        self.event_bus_service.subscribe(user_handler)
        
        # 市場事件處理器
        market_handler = MarketEventHandler(
            market_service=self.user_service  # 暫時使用使用者服務
        )
        self.event_bus_service.subscribe(market_handler)
        
        logger.info("Event handlers registered successfully")
    
    async def _start_background_tasks(self):
        """啟動後台任務"""
        
        # 系統健康檢查任務
        if self.config.health_check_interval > 0:
            health_task = asyncio.create_task(self._health_check_loop())
            self.background_tasks.append(health_task)
        
        # 自動重新平衡任務
        if self.config.enable_auto_rebalancing:
            rebalance_task = asyncio.create_task(self._auto_rebalance_loop())
            self.background_tasks.append(rebalance_task)
        
        # 統計更新任務
        if self.config.metrics_interval > 0:
            metrics_task = asyncio.create_task(self._metrics_update_loop())
            self.background_tasks.append(metrics_task)
        
        logger.info(f"Started {len(self.background_tasks)} background tasks")
    
    async def _health_check_loop(self):
        """健康檢查循環"""
        while self.is_initialized:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                
                health_status = await self.check_system_health()
                self.system_stats["health_status"] = health_status["overall_status"]
                self.system_stats["last_health_check"] = datetime.now(timezone.utc)
                
                if health_status["overall_status"] != "healthy":
                    logger.warning(f"System health check failed: {health_status}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
    
    async def _auto_rebalance_loop(self):
        """自動重新平衡循環"""
        while self.is_initialized:
            try:
                await asyncio.sleep(300)  # 每5分鐘檢查一次
                
                # 檢查是否需要重新平衡
                if await self._should_rebalance():
                    logger.info("Auto-rebalancing triggered")
                    await self.rebalance_system()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto-rebalance loop error: {e}")
    
    async def _metrics_update_loop(self):
        """統計更新循環"""
        while self.is_initialized:
            try:
                await asyncio.sleep(self.config.metrics_interval)
                
                # 更新系統統計
                if self.start_time:
                    self.system_stats["uptime"] = (
                        datetime.now(timezone.utc) - self.start_time
                    ).total_seconds()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics update loop error: {e}")
    
    async def _should_rebalance(self) -> bool:
        """判斷是否需要重新平衡"""
        try:
            # 獲取分片統計
            sharding_stats = self.sharding_service.get_shard_statistics()
            
            # 如果有分片負載超過閾值，則需要重新平衡
            for shard_id, shard_detail in sharding_stats.get("shard_details", {}).items():
                load_percentage = shard_detail["load"] / max(shard_detail["max_load"], 1) * 100
                if load_percentage > 80:  # 80% 負載閾值
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking rebalance condition: {e}")
            return False
    
    async def shutdown(self):
        """關閉分散式系統"""
        
        if not self.is_initialized:
            logger.warning("Distributed system not initialized")
            return
        
        logger.info("Shutting down distributed system...")
        
        # 停止後台任務
        for task in self.background_tasks:
            task.cancel()
        
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        # 停止各個服務
        if self.sharded_order_processor:
            await self.sharded_order_processor.stop_all_processors()
        
        if self.order_queue_service:
            await self.order_queue_service.stop_queue_processor()
        
        if self.event_bus_service:
            await self.event_bus_service.stop()
        
        self.is_initialized = False
        logger.info("Distributed system shutdown completed")
    
    async def _cleanup_partial_initialization(self):
        """清理部分初始化的組件"""
        try:
            if self.sharded_order_processor:
                await self.sharded_order_processor.stop_all_processors()
            
            if self.order_queue_service:
                await self.order_queue_service.stop_queue_processor()
            
            if self.event_bus_service:
                await self.event_bus_service.stop()
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def check_system_health(self) -> Dict[str, Any]:
        """檢查系統健康狀態"""
        
        health_status = {
            "overall_status": "healthy",
            "components": {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "issues": []
        }
        
        try:
            # 檢查分片服務
            if self.sharding_service:
                sharding_stats = self.sharding_service.get_shard_statistics()
                health_status["components"]["sharding"] = {
                    "status": "healthy",
                    "active_shards": sharding_stats.get("active_shards", 0),
                    "total_shards": sharding_stats.get("total_shards", 0)
                }
            
            # 檢查事件匯流服務
            if self.event_bus_service:
                event_stats = self.event_bus_service.get_statistics()
                health_status["components"]["event_bus"] = {
                    "status": "healthy" if event_stats.get("is_running", False) else "unhealthy",
                    "queue_size": event_stats.get("event_queue_size", 0),
                    "registered_handlers": event_stats.get("registered_handlers", 0)
                }
            
            # 檢查訂單佇列服務
            if self.order_queue_service:
                queue_stats = self.order_queue_service.get_queue_status()
                health_status["components"]["order_queue"] = {
                    "status": "healthy" if queue_stats.get("is_running", False) else "unhealthy",
                    "queue_size": queue_stats.get("total_queue_size", 0),
                    "locked_users": queue_stats.get("locked_users", 0)
                }
            
            # 檢查分片訂單處理器
            if self.sharded_order_processor:
                processor_stats = await self.sharded_order_processor.get_overall_status()
                health_status["components"]["sharded_processor"] = {
                    "status": "healthy",
                    "total_orders": processor_stats.get("processor_stats", {}).get("total_orders", 0),
                    "success_rate": self._calculate_success_rate(processor_stats.get("processor_stats", {}))
                }
            
            # 檢查整體狀態
            unhealthy_components = [
                comp for comp, status in health_status["components"].items()
                if status.get("status") != "healthy"
            ]
            
            if unhealthy_components:
                health_status["overall_status"] = "unhealthy"
                health_status["issues"].extend(unhealthy_components)
        
        except Exception as e:
            health_status["overall_status"] = "error"
            health_status["issues"].append(f"Health check error: {str(e)}")
        
        return health_status
    
    def _calculate_success_rate(self, stats: Dict[str, Any]) -> float:
        """計算成功率"""
        total = stats.get("total_orders", 0)
        successful = stats.get("successful_orders", 0)
        
        if total == 0:
            return 100.0
        
        return (successful / total) * 100.0
    
    async def rebalance_system(self):
        """重新平衡整個系統"""
        
        if not self.is_initialized:
            logger.error("Cannot rebalance uninitialized system")
            return
        
        try:
            logger.info("Starting system rebalancing...")
            
            # 重新平衡分片
            if self.sharded_order_processor:
                await self.sharded_order_processor.rebalance_shards()
            
            logger.info("System rebalancing completed")
            
        except Exception as e:
            logger.error(f"System rebalancing failed: {e}")
    
    async def get_system_statistics(self) -> Dict[str, Any]:
        """獲取系統統計資訊"""
        
        stats = {
            "system_stats": self.system_stats.copy(),
            "initialization_status": self.is_initialized,
            "config": {
                "num_shards": self.config.num_shards,
                "max_event_history": self.config.max_event_history,
                "enable_fast_path": self.config.enable_fast_path,
                "enable_batch_processing": self.config.enable_batch_processing,
                "enable_auto_rebalancing": self.config.enable_auto_rebalancing
            }
        }
        
        if self.is_initialized:
            # 添加各組件統計
            if self.sharding_service:
                stats["sharding_stats"] = self.sharding_service.get_shard_statistics()
            
            if self.event_bus_service:
                stats["event_bus_stats"] = self.event_bus_service.get_statistics()
            
            if self.order_queue_service:
                stats["order_queue_stats"] = self.order_queue_service.get_queue_status()
            
            if self.sharded_order_processor:
                stats["processor_stats"] = await self.sharded_order_processor.get_overall_status()
        
        return stats
    
    # 便捷方法
    async def process_market_order(self, user_id: str, order_data: dict):
        """處理市價單"""
        if not self.is_initialized or not self.sharded_order_processor:
            raise Exception("Distributed system not initialized")
        
        self.system_stats["total_requests"] += 1
        
        try:
            result = await self.sharded_order_processor.process_market_order(user_id, order_data)
            
            if result.status.value == "success":
                self.system_stats["successful_requests"] += 1
            else:
                self.system_stats["failed_requests"] += 1
            
            return result
            
        except Exception as e:
            self.system_stats["failed_requests"] += 1
            raise
    
    async def process_transfer(self, user_id: str, transfer_data: dict):
        """處理轉帳"""
        if not self.is_initialized or not self.sharded_order_processor:
            raise Exception("Distributed system not initialized")
        
        self.system_stats["total_requests"] += 1
        
        try:
            result = await self.sharded_order_processor.process_transfer(user_id, transfer_data)
            
            if result.status.value == "success":
                self.system_stats["successful_requests"] += 1
            else:
                self.system_stats["failed_requests"] += 1
            
            return result
            
        except Exception as e:
            self.system_stats["failed_requests"] += 1
            raise

# 全域分散式系統整合器實例
_distributed_system: Optional[DistributedSystemIntegrator] = None

def get_distributed_system() -> Optional[DistributedSystemIntegrator]:
    """獲取分散式系統整合器實例"""
    return _distributed_system

def get_distributed_system_integrator() -> Optional[DistributedSystemIntegrator]:
    """DistributedSystemIntegrator 的依賴注入函數"""
    return _distributed_system

async def initialize_distributed_system(user_service, 
                                       config: DistributedSystemConfig = None) -> DistributedSystemIntegrator:
    """初始化分散式系統"""
    global _distributed_system
    
    # 如果已存在，先關閉
    if _distributed_system:
        await _distributed_system.shutdown()
    
    # 創建新的整合器
    _distributed_system = DistributedSystemIntegrator(config)
    
    # 初始化系統
    success = await _distributed_system.initialize(user_service)
    
    if not success:
        raise Exception("Failed to initialize distributed system")
    
    logger.info("Distributed system initialized successfully")
    return _distributed_system

async def shutdown_distributed_system():
    """關閉分散式系統"""
    global _distributed_system
    
    if _distributed_system:
        await _distributed_system.shutdown()
        _distributed_system = None