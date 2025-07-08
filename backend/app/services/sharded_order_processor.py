"""
分片訂單處理器 - 整合使用者分片和事件驅動架構
結合分片服務和事件匯流，實現高性能分散式訂單處理
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import uuid

from .sharding_service import UserShardingService, ShardContext, get_sharding_service
from .event_bus_service import EventBusService, EventType, get_event_bus_service
from .order_queue_service import OrderQueueService, OrderPriority, QueuedOrder

logger = logging.getLogger(__name__)

class ProcessingResult(Enum):
    """處理結果狀態"""
    SUCCESS = "success"
    QUEUED = "queued"
    FAILED = "failed"
    RETRY = "retry"

@dataclass
class ShardedProcessingResult:
    """分片處理結果"""
    status: ProcessingResult
    shard_id: int
    order_id: str
    message: str
    processing_time: float
    retry_count: int = 0
    event_id: Optional[str] = None

class ShardedOrderProcessor:
    """
    分片訂單處理器
    
    功能：
    1. 根據使用者分片路由訂單
    2. 每個分片獨立處理，避免跨分片衝突
    3. 整合事件驅動架構
    4. 支援快速路徑和佇列回退
    5. 分片負載均衡和監控
    """
    
    def __init__(self, 
                 user_service,
                 sharding_service: UserShardingService,
                 event_bus_service: EventBusService,
                 num_shards: int = 16):
        self.user_service = user_service
        self.sharding_service = sharding_service
        self.event_bus_service = event_bus_service
        self.num_shards = num_shards
        
        # 每個分片的訂單佇列
        self.shard_queues: Dict[int, OrderQueueService] = {}
        
        # 分片處理統計
        self.shard_stats = {
            "total_orders": 0,
            "successful_orders": 0,
            "queued_orders": 0,
            "failed_orders": 0,
            "fast_path_success": 0,
            "queue_fallback": 0
        }
        
        # 初始化分片佇列
        self._initialize_shard_queues()
        
        logger.info(f"ShardedOrderProcessor initialized with {num_shards} shards")
    
    def _initialize_shard_queues(self):
        """初始化每個分片的訂單佇列"""
        for shard_id in range(self.num_shards):
            queue_service = OrderQueueService(self.user_service)
            self.shard_queues[shard_id] = queue_service
            logger.debug(f"Initialized queue for shard {shard_id}")
    
    async def start_all_processors(self):
        """啟動所有分片的處理器"""
        tasks = []
        for shard_id, queue_service in self.shard_queues.items():
            task = asyncio.create_task(queue_service.start_queue_processor())
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        logger.info("All shard processors started")
    
    async def stop_all_processors(self):
        """停止所有分片的處理器"""
        tasks = []
        for shard_id, queue_service in self.shard_queues.items():
            task = asyncio.create_task(queue_service.stop_queue_processor())
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        logger.info("All shard processors stopped")
    
    async def process_market_order(self, user_id: str, order_data: dict) -> ShardedProcessingResult:
        """處理市價單"""
        return await self._process_order(
            user_id=user_id,
            order_data=order_data,
            operation_type="market_order",
            priority=OrderPriority.HIGH
        )
    
    async def process_limit_order(self, user_id: str, order_data: dict) -> ShardedProcessingResult:
        """處理限價單"""
        return await self._process_order(
            user_id=user_id,
            order_data=order_data,
            operation_type="limit_order",
            priority=OrderPriority.MEDIUM
        )
    
    async def process_transfer(self, user_id: str, transfer_data: dict) -> ShardedProcessingResult:
        """處理轉帳"""
        return await self._process_order(
            user_id=user_id,
            order_data=transfer_data,
            operation_type="transfer",
            priority=OrderPriority.MEDIUM
        )
    
    async def process_cancel_order(self, user_id: str, cancel_data: dict) -> ShardedProcessingResult:
        """處理取消訂單"""
        return await self._process_order(
            user_id=user_id,
            order_data=cancel_data,
            operation_type="cancel",
            priority=OrderPriority.LOW
        )
    
    async def _process_order(self, 
                           user_id: str, 
                           order_data: dict,
                           operation_type: str,
                           priority: OrderPriority) -> ShardedProcessingResult:
        """通用訂單處理邏輯"""
        
        start_time = asyncio.get_event_loop().time()
        order_id = str(uuid.uuid4())
        
        # 獲取使用者分片
        shard_id = self.sharding_service.get_user_shard(user_id)
        
        # 發布訂單創建事件
        event_id = await self.event_bus_service.publish(
            event_type=EventType.ORDER_CREATED,
            data={
                "order_id": order_id,
                "user_id": user_id,
                "operation_type": operation_type,
                "order_data": order_data,
                "priority": priority.name
            },
            source_service="ShardedOrderProcessor",
            user_id=user_id,
            shard_id=shard_id
        )
        
        self.shard_stats["total_orders"] += 1
        
        try:
            # 使用分片上下文進行處理
            async with ShardContext(self.sharding_service, shard_id, operation_type) as ctx:
                
                # 嘗試快速路徑（直接處理）
                try:
                    result = await self._try_fast_path(user_id, order_data, operation_type, shard_id)
                    
                    if result:
                        # 快速路徑成功
                        processing_time = asyncio.get_event_loop().time() - start_time
                        self.shard_stats["fast_path_success"] += 1
                        self.shard_stats["successful_orders"] += 1
                        
                        # 發布成功事件
                        await self.event_bus_service.publish(
                            event_type=EventType.ORDER_MATCHED,
                            data={
                                "order_id": order_id,
                                "user_id": user_id,
                                "result": result,
                                "processing_time": processing_time
                            },
                            source_service="ShardedOrderProcessor",
                            user_id=user_id,
                            shard_id=shard_id,
                            correlation_id=event_id
                        )
                        
                        return ShardedProcessingResult(
                            status=ProcessingResult.SUCCESS,
                            shard_id=shard_id,
                            order_id=order_id,
                            message=f"Order processed successfully in fast path",
                            processing_time=processing_time,
                            event_id=event_id
                        )
                
                except Exception as e:
                    # 快速路徑失敗，回退到佇列
                    logger.warning(f"Fast path failed for order {order_id}: {e}")
                    self.shard_stats["queue_fallback"] += 1
                    
                    # 將訂單加入對應分片的佇列
                    queue_service = self.shard_queues[shard_id]
                    await queue_service.enqueue_order(
                        order_id=order_id,
                        user_id=user_id,
                        operation_type=operation_type,
                        data=order_data,
                        priority=priority
                    )
                    
                    processing_time = asyncio.get_event_loop().time() - start_time
                    self.shard_stats["queued_orders"] += 1
                    
                    return ShardedProcessingResult(
                        status=ProcessingResult.QUEUED,
                        shard_id=shard_id,
                        order_id=order_id,
                        message=f"Order queued for processing in shard {shard_id}",
                        processing_time=processing_time,
                        event_id=event_id
                    )
        
        except Exception as e:
            # 處理過程中發生錯誤
            processing_time = asyncio.get_event_loop().time() - start_time
            self.shard_stats["failed_orders"] += 1
            
            # 發布失敗事件
            await self.event_bus_service.publish(
                event_type=EventType.ORDER_FAILED,
                data={
                    "order_id": order_id,
                    "user_id": user_id,
                    "error": str(e),
                    "processing_time": processing_time
                },
                source_service="ShardedOrderProcessor",
                user_id=user_id,
                shard_id=shard_id,
                correlation_id=event_id
            )
            
            logger.error(f"Order {order_id} failed: {e}")
            
            return ShardedProcessingResult(
                status=ProcessingResult.FAILED,
                shard_id=shard_id,
                order_id=order_id,
                message=f"Order processing failed: {str(e)}",
                processing_time=processing_time,
                event_id=event_id
            )
    
    async def _try_fast_path(self, user_id: str, order_data: dict, operation_type: str, shard_id: int) -> Optional[dict]:
        """嘗試快速路徑處理"""
        
        from bson import ObjectId
        
        try:
            if operation_type == "market_order":
                # 市價單快速處理
                user_oid = ObjectId(user_id)
                result = await self.user_service._execute_market_order(user_oid, order_data)
                
                if result.success:
                    return {
                        "success": True,
                        "message": result.message,
                        "data": result.data
                    }
                else:
                    raise Exception(result.message)
            
            elif operation_type == "limit_order":
                # 限價單快速處理
                # 這裡可以實現限價單的快速處理邏輯
                raise Exception("Limit order not implemented in fast path")
            
            elif operation_type == "transfer":
                # 轉帳快速處理
                # 這裡可以實現轉帳的快速處理邏輯
                raise Exception("Transfer not implemented in fast path")
            
            elif operation_type == "cancel":
                # 取消訂單快速處理
                # 這裡可以實現取消訂單的快速處理邏輯
                raise Exception("Cancel order not implemented in fast path")
            
            else:
                raise Exception(f"Unknown operation type: {operation_type}")
        
        except Exception as e:
            logger.debug(f"Fast path failed for {operation_type}: {e}")
            raise
    
    async def get_shard_status(self, shard_id: int) -> Optional[dict]:
        """獲取特定分片的狀態"""
        if shard_id not in self.shard_queues:
            return None
        
        queue_service = self.shard_queues[shard_id]
        shard_info = self.sharding_service.get_shard_info(shard_id)
        
        return {
            "shard_id": shard_id,
            "shard_info": {
                "status": shard_info.status.value if shard_info else "unknown",
                "load": shard_info.load if shard_info else 0,
                "max_load": shard_info.max_load if shard_info else 0
            },
            "queue_status": queue_service.get_queue_status(),
            "users_in_shard": len(self.sharding_service.get_users_in_shard(shard_id))
        }
    
    async def get_overall_status(self) -> dict:
        """獲取整體狀態"""
        
        # 收集所有分片的狀態
        shard_statuses = {}
        for shard_id in range(self.num_shards):
            shard_statuses[f"shard_{shard_id}"] = await self.get_shard_status(shard_id)
        
        # 獲取分片服務統計
        sharding_stats = self.sharding_service.get_shard_statistics()
        
        # 獲取事件匯流統計
        event_bus_stats = self.event_bus_service.get_statistics()
        
        return {
            "processor_stats": self.shard_stats.copy(),
            "sharding_stats": sharding_stats,
            "event_bus_stats": event_bus_stats,
            "shard_statuses": shard_statuses,
            "total_shards": self.num_shards
        }
    
    async def rebalance_shards(self):
        """重新平衡分片"""
        logger.info("Starting shard rebalancing...")
        
        # 停止所有處理器
        await self.stop_all_processors()
        
        # 執行分片服務的重新平衡
        await self.sharding_service.rebalance_shards()
        
        # 重新啟動處理器
        await self.start_all_processors()
        
        # 發布重新平衡事件
        await self.event_bus_service.publish(
            event_type=EventType.SHARD_REBALANCED,
            data={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "num_shards": self.num_shards,
                "stats": self.shard_stats.copy()
            },
            source_service="ShardedOrderProcessor"
        )
        
        logger.info("Shard rebalancing completed")
    
    async def process_batch_orders(self, orders: List[dict]) -> List[ShardedProcessingResult]:
        """批量處理訂單"""
        
        # 按分片分組訂單
        shard_orders = {}
        for order in orders:
            user_id = order["user_id"]
            shard_id = self.sharding_service.get_user_shard(user_id)
            
            if shard_id not in shard_orders:
                shard_orders[shard_id] = []
            shard_orders[shard_id].append(order)
        
        # 併發處理各分片的訂單
        tasks = []
        for shard_id, shard_order_list in shard_orders.items():
            for order in shard_order_list:
                task = asyncio.create_task(
                    self._process_order(
                        user_id=order["user_id"],
                        order_data=order["order_data"],
                        operation_type=order["operation_type"],
                        priority=OrderPriority(order.get("priority", 2))
                    )
                )
                tasks.append(task)
        
        # 等待所有訂單處理完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理異常結果
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(ShardedProcessingResult(
                    status=ProcessingResult.FAILED,
                    shard_id=-1,
                    order_id="unknown",
                    message=f"Batch processing error: {str(result)}",
                    processing_time=0.0
                ))
            else:
                processed_results.append(result)
        
        return processed_results

# 全域分片訂單處理器實例
_sharded_order_processor: Optional[ShardedOrderProcessor] = None

def get_sharded_order_processor() -> Optional[ShardedOrderProcessor]:
    """獲取分片訂單處理器實例"""
    return _sharded_order_processor

async def initialize_sharded_order_processor(user_service, num_shards: int = 16) -> ShardedOrderProcessor:
    """初始化分片訂單處理器"""
    global _sharded_order_processor
    
    # 獲取必要的服務
    sharding_service = get_sharding_service()
    event_bus_service = get_event_bus_service()
    
    if not sharding_service:
        raise Exception("Sharding service not initialized")
    
    if not event_bus_service:
        raise Exception("Event bus service not initialized")
    
    # 停止現有處理器
    if _sharded_order_processor:
        await _sharded_order_processor.stop_all_processors()
    
    # 創建新的處理器
    _sharded_order_processor = ShardedOrderProcessor(
        user_service=user_service,
        sharding_service=sharding_service,
        event_bus_service=event_bus_service,
        num_shards=num_shards
    )
    
    # 啟動處理器
    await _sharded_order_processor.start_all_processors()
    
    logger.info(f"Sharded order processor initialized with {num_shards} shards")
    return _sharded_order_processor