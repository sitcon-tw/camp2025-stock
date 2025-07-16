"""
Event Publisher Implementation
"""
from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional, Callable, Awaitable
from datetime import datetime
from enum import Enum
import asyncio
import logging
from dataclasses import dataclass
import json

from ...application.common.interfaces import EventPublisher
from ...domain.common.events import DomainEvent
from ...domain.common.exceptions import BusinessRuleException

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """事件優先級"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class EventEnvelope:
    """事件信封"""
    event: DomainEvent
    priority: EventPriority = EventPriority.NORMAL
    retry_count: int = 0
    max_retries: int = 3
    delay_seconds: float = 0.0
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    published_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.published_at is None:
            self.published_at = datetime.utcnow()
        
        if self.correlation_id is None:
            self.correlation_id = getattr(self.event, 'correlation_id', None)
        
        if self.causation_id is None:
            self.causation_id = getattr(self.event, 'causation_id', None)


class EventHandler(ABC):
    """事件處理器接口"""
    
    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """處理事件"""
        pass
    
    @abstractmethod
    def can_handle(self, event: DomainEvent) -> bool:
        """檢查是否可以處理該事件"""
        pass
    
    def get_handler_name(self) -> str:
        """獲取處理器名稱"""
        return self.__class__.__name__


class InMemoryEventPublisher(EventPublisher):
    """內存事件發布器"""
    
    def __init__(self):
        self.handlers: Dict[str, List[EventHandler]] = {}
        self.event_queue: asyncio.Queue[EventEnvelope] = asyncio.Queue()
        self.is_running = False
        self.worker_task: Optional[asyncio.Task] = None
        self.published_events: List[EventEnvelope] = []
        self.failed_events: List[EventEnvelope] = []
        self.event_metrics = EventMetrics()
    
    async def start(self):
        """啟動事件發布器"""
        if self.is_running:
            return
        
        self.is_running = True
        self.worker_task = asyncio.create_task(self._process_events())
        logger.info("Event publisher started")
    
    async def stop(self):
        """停止事件發布器"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Event publisher stopped")
    
    async def publish(self, event: DomainEvent) -> None:
        """發布事件"""
        try:
            envelope = EventEnvelope(event=event)
            await self.event_queue.put(envelope)
            
            logger.debug(f"Event queued: {event.__class__.__name__}")
            
        except Exception as e:
            logger.error(f"Failed to publish event {event.__class__.__name__}: {e}")
            raise BusinessRuleException(f"Failed to publish event: {e}", "event_publish_failed")
    
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """批量發布事件"""
        for event in events:
            await self.publish(event)
    
    async def publish_with_priority(self, event: DomainEvent, priority: EventPriority) -> None:
        """以指定優先級發布事件"""
        envelope = EventEnvelope(event=event, priority=priority)
        await self.event_queue.put(envelope)
    
    async def _process_events(self):
        """處理事件隊列"""
        while self.is_running:
            try:
                # 等待事件，設置超時以便定期檢查是否需要停止
                envelope = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                
                # 處理事件
                await self._handle_event(envelope)
                
            except asyncio.TimeoutError:
                # 超時是正常的，繼續循環
                continue
            except asyncio.CancelledError:
                # 任務被取消，退出循環
                break
            except Exception as e:
                logger.error(f"Error in event processing loop: {e}")
                await asyncio.sleep(1)  # 避免緊密循環
    
    async def _handle_event(self, envelope: EventEnvelope):
        """處理單個事件"""
        event = envelope.event
        event_name = event.__class__.__name__
        
        try:
            # 記錄事件處理開始
            start_time = datetime.utcnow()
            
            # 獲取事件處理器
            handlers = self._get_handlers_for_event(event)
            
            if not handlers:
                logger.warning(f"No handlers found for event: {event_name}")
                return
            
            # 並行處理所有處理器
            tasks = []
            for handler in handlers:
                task = asyncio.create_task(self._invoke_handler(handler, event))
                tasks.append(task)
            
            # 等待所有處理器完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 檢查是否有處理失敗
            failed_handlers = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed_handlers.append((handlers[i], result))
                    logger.error(f"Handler {handlers[i].get_handler_name()} failed for event {event_name}: {result}")
            
            # 記錄事件處理結果
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            if failed_handlers:
                # 有處理器失敗，檢查是否需要重試
                if envelope.retry_count < envelope.max_retries:
                    envelope.retry_count += 1
                    envelope.delay_seconds = min(envelope.delay_seconds * 2 or 1, 60)  # 指數退避
                    
                    # 延遲後重新入隊
                    await asyncio.sleep(envelope.delay_seconds)
                    await self.event_queue.put(envelope)
                    
                    logger.info(f"Event {event_name} queued for retry {envelope.retry_count}/{envelope.max_retries}")
                else:
                    # 超過最大重試次數
                    self.failed_events.append(envelope)
                    logger.error(f"Event {event_name} failed after {envelope.max_retries} retries")
                    
                    # 記錄失敗指標
                    self.event_metrics.record_failed_event(event_name, duration)
            else:
                # 所有處理器成功
                self.published_events.append(envelope)
                logger.debug(f"Event {event_name} processed successfully by {len(handlers)} handlers")
                
                # 記錄成功指標
                self.event_metrics.record_successful_event(event_name, duration, len(handlers))
                
        except Exception as e:
            logger.error(f"Unexpected error handling event {event_name}: {e}")
            self.failed_events.append(envelope)
            self.event_metrics.record_failed_event(event_name, 0)
    
    async def _invoke_handler(self, handler: EventHandler, event: DomainEvent):
        """調用事件處理器"""
        try:
            await handler.handle(event)
        except Exception as e:
            logger.error(f"Handler {handler.get_handler_name()} failed: {e}")
            raise
    
    def _get_handlers_for_event(self, event: DomainEvent) -> List[EventHandler]:
        """獲取事件的處理器"""
        event_name = event.__class__.__name__
        handlers = self.handlers.get(event_name, [])
        
        # 過濾出能處理該事件的處理器
        return [handler for handler in handlers if handler.can_handle(event)]
    
    def subscribe(self, event_type: str, handler: EventHandler):
        """訂閱事件"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
        logger.info(f"Handler {handler.get_handler_name()} subscribed to {event_type}")
    
    def unsubscribe(self, event_type: str, handler: EventHandler):
        """取消訂閱事件"""
        if event_type in self.handlers:
            self.handlers[event_type] = [h for h in self.handlers[event_type] if h != handler]
            logger.info(f"Handler {handler.get_handler_name()} unsubscribed from {event_type}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """獲取事件指標"""
        return {
            "queue_size": self.event_queue.qsize(),
            "published_events": len(self.published_events),
            "failed_events": len(self.failed_events),
            "registered_handlers": sum(len(handlers) for handlers in self.handlers.values()),
            "event_types": list(self.handlers.keys()),
            **self.event_metrics.get_metrics()
        }
    
    def clear_history(self):
        """清除歷史記錄"""
        self.published_events.clear()
        self.failed_events.clear()


class RedisEventPublisher(EventPublisher):
    """Redis 事件發布器"""
    
    def __init__(self, redis_url: str, channel_prefix: str = "events:"):
        self.redis_url = redis_url
        self.channel_prefix = channel_prefix
        self.redis = None
        self.subscribers: Dict[str, List[Callable]] = {}
    
    async def _get_redis(self):
        """獲取 Redis 連接"""
        if not self.redis:
            import aioredis
            self.redis = await aioredis.from_url(self.redis_url)
        return self.redis
    
    async def publish(self, event: DomainEvent) -> None:
        """發布事件"""
        try:
            redis = await self._get_redis()
            
            # 序列化事件
            event_data = {
                "event_type": event.__class__.__name__,
                "event_id": event.event_id,
                "occurred_at": event.occurred_at.isoformat(),
                "data": event.__dict__
            }
            
            serialized_event = json.dumps(event_data, default=str)
            
            # 發布到 Redis
            channel = f"{self.channel_prefix}{event.__class__.__name__}"
            await redis.publish(channel, serialized_event)
            
            logger.debug(f"Event published to Redis: {event.__class__.__name__}")
            
        except Exception as e:
            logger.error(f"Failed to publish event to Redis: {e}")
            raise BusinessRuleException(f"Failed to publish event: {e}", "event_publish_failed")
    
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """批量發布事件"""
        for event in events:
            await self.publish(event)
    
    async def subscribe(self, event_type: str, handler: Callable[[DomainEvent], Awaitable[None]]):
        """訂閱事件"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(handler)
        
        # 啟動 Redis 訂閱
        await self._start_redis_subscription(event_type)
    
    async def _start_redis_subscription(self, event_type: str):
        """啟動 Redis 訂閱"""
        try:
            redis = await self._get_redis()
            pubsub = redis.pubsub()
            
            channel = f"{self.channel_prefix}{event_type}"
            await pubsub.subscribe(channel)
            
            # 在後台處理消息
            asyncio.create_task(self._process_redis_messages(pubsub, event_type))
            
        except Exception as e:
            logger.error(f"Failed to start Redis subscription for {event_type}: {e}")
    
    async def _process_redis_messages(self, pubsub, event_type: str):
        """處理 Redis 消息"""
        try:
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        # 反序列化事件
                        event_data = json.loads(message['data'])
                        
                        # 調用處理器
                        handlers = self.subscribers.get(event_type, [])
                        for handler in handlers:
                            try:
                                await handler(event_data)
                            except Exception as e:
                                logger.error(f"Handler failed for Redis event {event_type}: {e}")
                                
                    except Exception as e:
                        logger.error(f"Failed to process Redis message: {e}")
                        
        except Exception as e:
            logger.error(f"Error in Redis message processing: {e}")
    
    async def cleanup(self):
        """清理資源"""
        if self.redis:
            await self.redis.close()


class EventMetrics:
    """事件指標"""
    
    def __init__(self):
        self.total_events = 0
        self.successful_events = 0
        self.failed_events = 0
        self.total_handlers = 0
        self.average_processing_time = 0.0
        self.event_counts_by_type: Dict[str, int] = {}
    
    def record_successful_event(self, event_type: str, duration: float, handler_count: int):
        """記錄成功事件"""
        self.total_events += 1
        self.successful_events += 1
        self.total_handlers += handler_count
        
        # 更新平均處理時間
        total_time = self.average_processing_time * (self.total_events - 1) + duration
        self.average_processing_time = total_time / self.total_events
        
        # 更新事件類型計數
        self.event_counts_by_type[event_type] = self.event_counts_by_type.get(event_type, 0) + 1
    
    def record_failed_event(self, event_type: str, duration: float):
        """記錄失敗事件"""
        self.total_events += 1
        self.failed_events += 1
        
        # 更新平均處理時間
        total_time = self.average_processing_time * (self.total_events - 1) + duration
        self.average_processing_time = total_time / self.total_events
        
        # 更新事件類型計數
        self.event_counts_by_type[event_type] = self.event_counts_by_type.get(event_type, 0) + 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """獲取指標"""
        return {
            "total_events": self.total_events,
            "successful_events": self.successful_events,
            "failed_events": self.failed_events,
            "success_rate": self.successful_events / max(1, self.total_events),
            "total_handlers": self.total_handlers,
            "average_processing_time": self.average_processing_time,
            "event_counts_by_type": self.event_counts_by_type
        }


# 便利的事件處理器裝飾器
def event_handler(event_type: str):
    """事件處理器裝飾器"""
    def decorator(func):
        class FunctionEventHandler(EventHandler):
            async def handle(self, event: DomainEvent) -> None:
                await func(event)
            
            def can_handle(self, event: DomainEvent) -> bool:
                return event.__class__.__name__ == event_type
        
        return FunctionEventHandler()
    return decorator


# 工廠函數
def create_event_publisher(config: Dict[str, Any]) -> EventPublisher:
    """創建事件發布器"""
    publisher_type = config.get('type', 'memory')
    
    if publisher_type == 'memory':
        return InMemoryEventPublisher()
    elif publisher_type == 'redis':
        return RedisEventPublisher(
            redis_url=config['redis_url'],
            channel_prefix=config.get('channel_prefix', 'events:')
        )
    else:
        raise ValueError(f"Unsupported event publisher type: {publisher_type}")


# 全局事件發布器實例
_global_publisher: Optional[EventPublisher] = None


def get_event_publisher() -> EventPublisher:
    """獲取全局事件發布器"""
    global _global_publisher
    if _global_publisher is None:
        _global_publisher = InMemoryEventPublisher()
    return _global_publisher


def set_event_publisher(publisher: EventPublisher):
    """設置全局事件發布器"""
    global _global_publisher
    _global_publisher = publisher