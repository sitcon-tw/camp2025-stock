"""
基礎設施服務模組

包含：
- DistributedSystemIntegrator: 分散式系統整合器
- EventBusService: 事件總線服務
- ShardedOrderProcessor: 分片訂單處理器
- ShardingService: 分片服務
- OrderQueueService: 訂單佇列服務
"""

from .distributed_system_integrator import DistributedSystemIntegrator, get_distributed_system_integrator
from .event_bus_service import EventBusService, get_event_bus_service
from .sharded_order_processor import ShardedOrderProcessor, get_sharded_order_processor
from .sharding_service import ShardingService, get_sharding_service
from .order_queue_service import OrderQueueService, get_order_queue_service

__all__ = [
    "DistributedSystemIntegrator",
    "get_distributed_system_integrator",
    "EventBusService", 
    "get_event_bus_service",
    "ShardedOrderProcessor",
    "get_sharded_order_processor",
    "ShardingService",
    "get_sharding_service",
    "OrderQueueService",
    "get_order_queue_service"
]