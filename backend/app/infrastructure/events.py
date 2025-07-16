"""
Infrastructure Event Implementations
"""
from __future__ import annotations
from typing import List, Dict, Type, TypeVar, Any, Optional
import asyncio
import logging
from datetime import datetime

from app.domain.common.events import (
    DomainEvent, DomainEventBus, DomainEventHandler, 
    EventStore, EventDispatcher
)
from app.domain.common.exceptions import ConfigurationException

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=DomainEvent)


class InMemoryEventBus(DomainEventBus):
    """
    內存事件總線實現
    適用於單機部署或開發環境
    """
    
    def __init__(self):
        self._dispatcher = EventDispatcher()
        self._event_store: Optional[EventStore] = None
        self._running = False
        self._event_queue: asyncio.Queue[DomainEvent] = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
    
    async def publish(self, event: DomainEvent) -> None:
        """發布事件"""
        if not self._running:
            raise ConfigurationException("Event bus is not running", "event_bus_state", "not_running")
        
        logger.debug(f"Publishing event {event.event_type} with ID {event.event_id}")
        
        # 保存事件到事件存儲
        if self._event_store:
            await self._event_store.save_event(event)
        
        # 添加到處理隊列
        await self._event_queue.put(event)
    
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """批量發布事件"""
        if not self._running:
            raise ConfigurationException("Event bus is not running", "event_bus_state", "not_running")
        
        logger.debug(f"Publishing {len(events)} events")
        
        # 批量保存事件
        if self._event_store:
            await self._event_store.save_events(events)
        
        # 批量添加到處理隊列
        for event in events:
            await self._event_queue.put(event)
    
    def subscribe(self, event_type: Type[T], handler: DomainEventHandler[T]) -> None:
        """訂閱事件"""
        self._dispatcher.register_handler(event_type, handler)
    
    def unsubscribe(self, event_type: Type[T], handler: DomainEventHandler[T]) -> None:
        """取消訂閱事件"""
        self._dispatcher.unregister_handler(event_type, handler)
    
    async def start(self) -> None:
        """啟動事件總線"""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._event_worker())
        logger.info("Event bus started")
    
    async def stop(self) -> None:
        """停止事件總線"""
        if not self._running:
            return
        
        self._running = False
        
        # 等待工作任務完成
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Event bus stopped")
    
    async def _event_worker(self) -> None:
        """事件工作線程"""
        while self._running:
            try:
                # 等待事件，超時後檢查是否還在運行
                try:
                    event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # 處理事件
                await self._dispatcher.dispatch(event)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event worker: {e}")
                # 繼續處理其他事件
                continue
    
    def set_event_store(self, event_store: EventStore) -> None:
        """設置事件存儲"""
        self._event_store = event_store
    
    def add_middleware(self, middleware) -> None:
        """添加中間件"""
        self._dispatcher.add_middleware(middleware)


class MongoEventStore(EventStore):
    """
    MongoDB 事件存儲實現
    """
    
    def __init__(self):
        self._collection = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """初始化事件存儲"""
        if self._initialized:
            return
        
        from app.core.database import get_database
        db = get_database()
        self._collection = db["domain_events"]
        
        # 創建索引
        await self._collection.create_index([("event_type", 1), ("occurred_at", -1)])
        await self._collection.create_index([("aggregate_id", 1), ("version", 1)])
        
        self._initialized = True
        logger.info("MongoDB event store initialized")
    
    async def save_event(self, event: DomainEvent) -> None:
        """保存事件"""
        if not self._initialized:
            await self.initialize()
        
        event_doc = {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "occurred_at": event.occurred_at,
            "event_version": event.event_version,
            "correlation_id": event.correlation_id,
            "data": event._get_event_data()
        }
        
        await self._collection.insert_one(event_doc)
    
    async def save_events(self, events: List[DomainEvent]) -> None:
        """批量保存事件"""
        if not self._initialized:
            await self.initialize()
        
        if not events:
            return
        
        event_docs = []
        for event in events:
            event_doc = {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "occurred_at": event.occurred_at,
                "event_version": event.event_version,
                "correlation_id": event.correlation_id,
                "data": event._get_event_data()
            }
            event_docs.append(event_doc)
        
        await self._collection.insert_many(event_docs)
    
    async def get_events(self, aggregate_id: str, from_version: int = 0) -> List[DomainEvent]:
        """獲取聚合的事件"""
        if not self._initialized:
            await self.initialize()
        
        cursor = self._collection.find({
            "data.aggregate_id": aggregate_id,
            "event_version": {"$gte": from_version}
        }).sort("event_version", 1)
        
        events = []
        async for doc in cursor:
            # 這裡需要根據事件類型重構事件對象
            # 簡化實現，實際項目中需要事件序列化/反序列化機制
            events.append(doc)
        
        return events
    
    async def get_events_by_type(self, event_type: str, skip: int = 0, limit: int = 100) -> List[DomainEvent]:
        """根據類型獲取事件"""
        if not self._initialized:
            await self.initialize()
        
        cursor = self._collection.find({
            "event_type": event_type
        }).sort("occurred_at", -1).skip(skip).limit(limit)
        
        events = []
        async for doc in cursor:
            events.append(doc)
        
        return events


class RedisEventBus(DomainEventBus):
    """
    Redis 事件總線實現
    適用於分布式環境
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self._redis_url = redis_url
        self._redis = None
        self._dispatcher = EventDispatcher()
        self._running = False
        self._subscriber_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """啟動事件總線"""
        if self._running:
            return
        
        import redis.asyncio as redis
        self._redis = redis.from_url(self._redis_url)
        
        self._running = True
        self._subscriber_task = asyncio.create_task(self._subscribe_worker())
        logger.info("Redis event bus started")
    
    async def stop(self) -> None:
        """停止事件總線"""
        if not self._running:
            return
        
        self._running = False
        
        if self._subscriber_task:
            self._subscriber_task.cancel()
            try:
                await self._subscriber_task
            except asyncio.CancelledError:
                pass
        
        if self._redis:
            await self._redis.close()
        
        logger.info("Redis event bus stopped")
    
    async def publish(self, event: DomainEvent) -> None:
        """發布事件"""
        if not self._running:
            raise ConfigurationException("Event bus is not running", "event_bus_state", "not_running")
        
        import json
        event_data = json.dumps(event.to_dict())
        await self._redis.publish("domain_events", event_data)
    
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """批量發布事件"""
        for event in events:
            await self.publish(event)
    
    def subscribe(self, event_type: Type[T], handler: DomainEventHandler[T]) -> None:
        """訂閱事件"""
        self._dispatcher.register_handler(event_type, handler)
    
    def unsubscribe(self, event_type: Type[T], handler: DomainEventHandler[T]) -> None:
        """取消訂閱事件"""
        self._dispatcher.unregister_handler(event_type, handler)
    
    async def _subscribe_worker(self) -> None:
        """訂閱工作線程"""
        pubsub = self._redis.pubsub()
        await pubsub.subscribe("domain_events")
        
        while self._running:
            try:
                message = await pubsub.get_message(timeout=1.0)
                if message and message["type"] == "message":
                    import json
                    event_data = json.loads(message["data"])
                    # 這裡需要根據事件類型重構事件對象
                    # 簡化實現，實際項目中需要完整的事件序列化機制
                    logger.debug(f"Received event: {event_data}")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in Redis subscriber: {e}")
                continue
        
        await pubsub.unsubscribe("domain_events")
        await pubsub.close()


# 事件處理器中間件

async def logging_middleware(event: DomainEvent) -> None:
    """日誌中間件"""
    logger.info(f"Processing event {event.event_type} (ID: {event.event_id})")


async def metrics_middleware(event: DomainEvent) -> None:
    """指標中間件"""
    # 這裡可以添加指標收集邏輯
    pass


async def audit_middleware(event: DomainEvent) -> None:
    """審計中間件"""
    # 這裡可以添加審計邏輯
    pass