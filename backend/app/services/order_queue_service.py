"""
訂單佇列服務 - 用於處理高併發交易
解決同時修改問題的佇列實現
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from collections import deque
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class OrderPriority(Enum):
    """訂單優先級"""
    HIGH = 1      # 市價單
    MEDIUM = 2    # 限價單
    LOW = 3       # 其他操作

@dataclass
class QueuedOrder:
    """佇列中的訂單"""
    order_id: str
    user_id: str
    operation_type: str  # "market_order", "limit_order", "transfer", "cancel"
    data: dict
    priority: OrderPriority
    created_at: datetime
    retry_count: int = 0
    max_retries: int = 3

class OrderQueueService:
    """
    訂單佇列服務
    
    功能：
    1. 按優先級處理訂單
    2. 避免同時修改同一用戶資料
    3. 批量處理相關訂單
    4. 失敗重試機制
    """
    
    def __init__(self, user_service):
        self.user_service = user_service
        
        # 按優先級分組的佇列
        self.priority_queues: Dict[OrderPriority, deque] = {
            OrderPriority.HIGH: deque(),
            OrderPriority.MEDIUM: deque(),
            OrderPriority.LOW: deque()
        }
        
        # 用戶鎖定集合 - 避免同時處理同一用戶的訂單
        self.locked_users: set = set()
        
        # 處理中的訂單
        self.processing_orders: Dict[str, QueuedOrder] = {}
        
        # 佇列處理任務
        self.queue_processor_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # 統計
        self.stats = {
            "processed": 0,
            "failed": 0,
            "retried": 0,
            "queue_size": 0
        }
    
    async def start_queue_processor(self):
        """啟動佇列處理器"""
        if self.is_running:
            logger.warning("Queue processor is already running")
            return
        
        self.is_running = True
        self.queue_processor_task = asyncio.create_task(self._process_queue_loop())
        logger.info("Order queue processor started")
    
    async def stop_queue_processor(self):
        """停止佇列處理器"""
        self.is_running = False
        if self.queue_processor_task:
            self.queue_processor_task.cancel()
            try:
                await self.queue_processor_task
            except asyncio.CancelledError:
                pass
        logger.info("Order queue processor stopped")
    
    async def enqueue_order(self, 
                          order_id: str,
                          user_id: str, 
                          operation_type: str,
                          data: dict,
                          priority: OrderPriority = OrderPriority.MEDIUM) -> bool:
        """將訂單加入佇列"""
        
        queued_order = QueuedOrder(
            order_id=order_id,
            user_id=user_id,
            operation_type=operation_type,
            data=data,
            priority=priority,
            created_at=datetime.now(timezone.utc)
        )
        
        # 加入對應優先級的佇列
        self.priority_queues[priority].append(queued_order)
        self.stats["queue_size"] = self._get_total_queue_size()
        
        logger.info(f"Order {order_id} enqueued with priority {priority.name}")
        return True
    
    async def _process_queue_loop(self):
        """佇列處理循環"""
        while self.is_running:
            try:
                # 按優先級處理訂單
                order = self._get_next_order()
                
                if order:
                    await self._process_order(order)
                else:
                    # 沒有訂單時短暫休息
                    await asyncio.sleep(0.01)  # 10ms
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in queue processing loop: {e}")
                await asyncio.sleep(0.1)  # 錯誤時稍長休息
    
    def _get_next_order(self) -> Optional[QueuedOrder]:
        """獲取下一個要處理的訂單（按優先級）"""
        
        # 按優先級順序檢查
        for priority in [OrderPriority.HIGH, OrderPriority.MEDIUM, OrderPriority.LOW]:
            queue = self.priority_queues[priority]
            
            # 找到第一個未被鎖定用戶的訂單
            for i, order in enumerate(queue):
                if order.user_id not in self.locked_users:
                    # 從佇列中移除
                    del queue[i]
                    self.stats["queue_size"] = self._get_total_queue_size()
                    return order
        
        return None
    
    async def _process_order(self, order: QueuedOrder):
        """處理單個訂單"""
        
        # 鎖定用戶
        self.locked_users.add(order.user_id)
        self.processing_orders[order.order_id] = order
        
        try:
            logger.info(f"Processing order {order.order_id} for user {order.user_id}")
            
            # 根據操作類型處理
            if order.operation_type == "market_order":
                await self._process_market_order(order)
            elif order.operation_type == "limit_order":
                await self._process_limit_order(order)
            elif order.operation_type == "transfer":
                await self._process_transfer(order)
            elif order.operation_type == "cancel":
                await self._process_cancel_order(order)
            else:
                logger.error(f"Unknown operation type: {order.operation_type}")
            
            self.stats["processed"] += 1
            logger.info(f"Order {order.order_id} processed successfully")
            
        except Exception as e:
            logger.error(f"Error processing order {order.order_id}: {e}")
            
            # 重試邏輯
            if order.retry_count < order.max_retries:
                order.retry_count += 1
                self.stats["retried"] += 1
                
                # 重新加入佇列（降低優先級）
                retry_priority = OrderPriority.LOW
                self.priority_queues[retry_priority].append(order)
                
                logger.info(f"Order {order.order_id} queued for retry ({order.retry_count}/{order.max_retries})")
            else:
                self.stats["failed"] += 1
                logger.error(f"Order {order.order_id} failed permanently after {order.max_retries} retries")
        
        finally:
            # 解鎖用戶
            self.locked_users.discard(order.user_id)
            self.processing_orders.pop(order.order_id, None)
    
    async def _process_market_order(self, order: QueuedOrder):
        """處理市價單"""
        from bson import ObjectId
        user_oid = ObjectId(order.user_id)
        result = await self.user_service._execute_market_order(user_oid, order.data)
        
        if not result.success:
            raise Exception(f"Market order failed: {result.message}")
    
    async def _process_limit_order(self, order: QueuedOrder):
        """處理限價單"""
        # 實現限價單處理邏輯
        pass
    
    async def _process_transfer(self, order: QueuedOrder):
        """處理轉帳"""
        # 實現轉帳處理邏輯
        pass
    
    async def _process_cancel_order(self, order: QueuedOrder):
        """處理取消訂單"""
        # 實現取消訂單邏輯
        pass
    
    def _get_total_queue_size(self) -> int:
        """獲取總佇列大小"""
        return sum(len(queue) for queue in self.priority_queues.values())
    
    def get_queue_status(self) -> dict:
        """獲取佇列狀態"""
        return {
            "is_running": self.is_running,
            "total_queue_size": self._get_total_queue_size(),
            "priority_queues": {
                priority.name: len(queue) 
                for priority, queue in self.priority_queues.items()
            },
            "locked_users": len(self.locked_users),
            "processing_orders": len(self.processing_orders),
            "stats": self.stats.copy()
        }
    
    async def enqueue_market_order(self, user_id: str, order_data: dict) -> str:
        """快捷方法：加入市價單到佇列"""
        import uuid
        order_id = str(uuid.uuid4())
        
        await self.enqueue_order(
            order_id=order_id,
            user_id=user_id,
            operation_type="market_order",
            data=order_data,
            priority=OrderPriority.HIGH  # 市價單高優先級
        )
        
        return order_id
    
    async def enqueue_limit_order(self, user_id: str, order_data: dict) -> str:
        """快捷方法：加入限價單到佇列"""
        import uuid
        order_id = str(uuid.uuid4())
        
        await self.enqueue_order(
            order_id=order_id,
            user_id=user_id,
            operation_type="limit_order",
            data=order_data,
            priority=OrderPriority.MEDIUM  # 限價單中等優先級
        )
        
        return order_id

# 全域佇列服務實例
_order_queue_service: Optional[OrderQueueService] = None

def get_order_queue_service() -> Optional[OrderQueueService]:
    """獲取訂單佇列服務實例"""
    return _order_queue_service

def set_order_queue_service(service: OrderQueueService):
    """設定訂單佇列服務實例"""
    global _order_queue_service
    _order_queue_service = service

async def initialize_order_queue_service(user_service):
    """初始化訂單佇列服務"""
    global _order_queue_service
    
    if _order_queue_service:
        await _order_queue_service.stop_queue_processor()
    
    _order_queue_service = OrderQueueService(user_service)
    await _order_queue_service.start_queue_processor()
    
    logger.info("Order queue service initialized")
    return _order_queue_service