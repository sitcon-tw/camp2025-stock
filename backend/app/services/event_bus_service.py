"""
事件匯流服務 - 分散式事件驅動架構的核心組件
處理系統內部事件的發布、訂閱和路由
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import uuid

logger = logging.getLogger(__name__)

class EventType(Enum):
    """事件類型定義"""
    # 交易事件
    ORDER_CREATED = "order_created"
    ORDER_MATCHED = "order_matched"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_FAILED = "order_failed"
    
    # 使用者事件
    USER_POINTS_UPDATED = "user_points_updated"
    USER_PORTFOLIO_UPDATED = "user_portfolio_updated"
    USER_LOGIN = "user_login"
    
    # 市場事件
    MARKET_OPENED = "market_opened"
    MARKET_CLOSED = "market_closed"
    PRICE_UPDATED = "price_updated"
    
    # 系統事件
    SYSTEM_MAINTENANCE = "system_maintenance"
    SHARD_REBALANCED = "shard_rebalanced"
    QUEUE_OVERFLOW = "queue_overflow"
    
    # 轉帳事件
    TRANSFER_INITIATED = "transfer_initiated"
    TRANSFER_COMPLETED = "transfer_completed"
    TRANSFER_FAILED = "transfer_failed"

@dataclass
class EventPayload:
    """事件載荷基類"""
    event_id: str
    event_type: EventType
    source_service: str
    timestamp: datetime
    data: Dict[str, Any]
    user_id: Optional[str] = None
    shard_id: Optional[int] = None
    correlation_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

class EventHandler:
    """事件處理器抽象類"""
    
    def __init__(self, name: str, event_types: List[EventType]):
        self.name = name
        self.event_types = event_types
        self.processed_count = 0
        self.error_count = 0
        self.last_processed = None
    
    async def handle_event(self, event: EventPayload) -> bool:
        """處理事件，返回是否成功"""
        raise NotImplementedError

class EventBusService:
    """
    事件匯流服務
    
    功能：
    1. 事件發布和訂閱
    2. 事件路由和分發
    3. 事件持久化和重放
    4. 錯誤處理和重試
    5. 事件統計和監控
    """
    
    def __init__(self, max_event_history: int = 10000):
        self.handlers: Dict[EventType, List[EventHandler]] = defaultdict(list)
        self.event_history: deque = deque(maxlen=max_event_history)
        self.pending_events: Dict[str, EventPayload] = {}
        
        # 事件統計
        self.stats = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0,
            "events_retried": 0,
            "handler_errors": defaultdict(int)
        }
        
        # 事件處理任務
        self.event_processor_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # 事件隊列
        self.event_queue: asyncio.Queue = asyncio.Queue()
        
        logger.info("EventBusService initialized")
    
    async def start(self):
        """啟動事件匯流服務"""
        if self.is_running:
            logger.warning("EventBusService is already running")
            return
        
        self.is_running = True
        self.event_processor_task = asyncio.create_task(self._process_events_loop())
        logger.info("EventBusService started")
    
    async def stop(self):
        """停止事件匯流服務"""
        self.is_running = False
        
        if self.event_processor_task:
            self.event_processor_task.cancel()
            try:
                await self.event_processor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("EventBusService stopped")
    
    def subscribe(self, handler: EventHandler):
        """訂閱事件處理器"""
        for event_type in handler.event_types:
            self.handlers[event_type].append(handler)
            logger.info(f"Handler {handler.name} subscribed to {event_type.value}")
    
    def unsubscribe(self, handler: EventHandler):
        """取消訂閱事件處理器"""
        for event_type in handler.event_types:
            if handler in self.handlers[event_type]:
                self.handlers[event_type].remove(handler)
                logger.info(f"Handler {handler.name} unsubscribed from {event_type.value}")
    
    async def publish(self, 
                     event_type: EventType, 
                     data: Dict[str, Any],
                     source_service: str = "unknown",
                     user_id: Optional[str] = None,
                     shard_id: Optional[int] = None,
                     correlation_id: Optional[str] = None) -> str:
        """發布事件"""
        
        event_id = str(uuid.uuid4())
        event = EventPayload(
            event_id=event_id,
            event_type=event_type,
            source_service=source_service,
            timestamp=datetime.now(timezone.utc),
            data=data,
            user_id=user_id,
            shard_id=shard_id,
            correlation_id=correlation_id
        )
        
        # 將事件加入處理隊列
        await self.event_queue.put(event)
        self.stats["events_published"] += 1
        
        logger.debug(f"Event {event_type.value} published with ID {event_id}")
        return event_id
    
    async def _process_events_loop(self):
        """事件處理循環"""
        while self.is_running:
            try:
                # 等待事件（帶超時避免阻塞）
                event = await asyncio.wait_for(
                    self.event_queue.get(), 
                    timeout=1.0
                )
                
                await self._process_event(event)
                
            except asyncio.TimeoutError:
                # 超時是正常的，繼續循環
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event processing loop: {e}")
                await asyncio.sleep(0.1)
    
    async def _process_event(self, event: EventPayload):
        """處理單個事件"""
        
        # 記錄事件到歷史
        self.event_history.append(event)
        
        # 獲取該事件類型的所有處理器
        handlers = self.handlers.get(event.event_type, [])
        
        if not handlers:
            logger.warning(f"No handlers registered for event type {event.event_type.value}")
            return
        
        # 併發處理所有處理器
        tasks = []
        for handler in handlers:
            task = asyncio.create_task(
                self._handle_event_with_retry(handler, event)
            )
            tasks.append(task)
        
        # 等待所有處理器完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 統計結果
        success_count = sum(1 for r in results if r is True)
        error_count = len(results) - success_count
        
        self.stats["events_processed"] += 1
        
        if error_count > 0:
            self.stats["events_failed"] += 1
            logger.error(f"Event {event.event_id} had {error_count} handler errors")
        
        logger.debug(f"Event {event.event_id} processed by {success_count}/{len(handlers)} handlers")
    
    async def _handle_event_with_retry(self, handler: EventHandler, event: EventPayload) -> bool:
        """帶重試的事件處理"""
        
        for attempt in range(event.max_retries + 1):
            try:
                success = await handler.handle_event(event)
                
                if success:
                    handler.processed_count += 1
                    handler.last_processed = datetime.now(timezone.utc)
                    return True
                else:
                    raise Exception(f"Handler {handler.name} returned False")
                    
            except Exception as e:
                handler.error_count += 1
                self.stats["handler_errors"][handler.name] += 1
                
                if attempt < event.max_retries:
                    # 重試
                    event.retry_count += 1
                    self.stats["events_retried"] += 1
                    
                    # 指數退避
                    delay = 0.1 * (2 ** attempt)
                    await asyncio.sleep(delay)
                    
                    logger.warning(f"Retrying event {event.event_id} for handler {handler.name} (attempt {attempt + 1})")
                    continue
                else:
                    # 最終失敗
                    logger.error(f"Event {event.event_id} failed permanently for handler {handler.name}: {e}")
                    return False
        
        return False
    
    async def get_event_by_id(self, event_id: str) -> Optional[EventPayload]:
        """根據ID獲取事件"""
        for event in self.event_history:
            if event.event_id == event_id:
                return event
        return None
    
    def get_events_by_type(self, event_type: EventType, limit: int = 100) -> List[EventPayload]:
        """根據類型獲取事件"""
        events = []
        for event in reversed(self.event_history):
            if event.event_type == event_type:
                events.append(event)
                if len(events) >= limit:
                    break
        return events
    
    def get_events_by_user(self, user_id: str, limit: int = 100) -> List[EventPayload]:
        """根據使用者ID獲取事件"""
        events = []
        for event in reversed(self.event_history):
            if event.user_id == user_id:
                events.append(event)
                if len(events) >= limit:
                    break
        return events
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取統計信息"""
        handler_stats = {}
        for event_type, handlers in self.handlers.items():
            handler_stats[event_type.value] = [
                {
                    "name": handler.name,
                    "processed_count": handler.processed_count,
                    "error_count": handler.error_count,
                    "last_processed": handler.last_processed.isoformat() if handler.last_processed else None
                }
                for handler in handlers
            ]
        
        return {
            "is_running": self.is_running,
            "event_queue_size": self.event_queue.qsize(),
            "event_history_size": len(self.event_history),
            "registered_handlers": sum(len(handlers) for handlers in self.handlers.values()),
            "handler_stats": handler_stats,
            "stats": self.stats.copy()
        }
    
    async def replay_events(self, 
                          event_type: Optional[EventType] = None,
                          user_id: Optional[str] = None,
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None):
        """重放事件"""
        
        events_to_replay = []
        
        for event in self.event_history:
            # 過濾條件
            if event_type and event.event_type != event_type:
                continue
            if user_id and event.user_id != user_id:
                continue
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue
            
            events_to_replay.append(event)
        
        logger.info(f"Replaying {len(events_to_replay)} events")
        
        # 按時間順序重放
        for event in sorted(events_to_replay, key=lambda e: e.timestamp):
            await self._process_event(event)
            await asyncio.sleep(0.001)  # 避免過快重放

# 預定義的事件處理器

class OrderEventHandler(EventHandler):
    """訂單事件處理器"""
    
    def __init__(self, user_service, order_service):
        super().__init__("OrderEventHandler", [
            EventType.ORDER_CREATED,
            EventType.ORDER_MATCHED,
            EventType.ORDER_CANCELLED,
            EventType.ORDER_FAILED
        ])
        self.user_service = user_service
        self.order_service = order_service
    
    async def handle_event(self, event: EventPayload) -> bool:
        """處理訂單事件"""
        try:
            if event.event_type == EventType.ORDER_CREATED:
                return await self._handle_order_created(event)
            elif event.event_type == EventType.ORDER_MATCHED:
                return await self._handle_order_matched(event)
            elif event.event_type == EventType.ORDER_CANCELLED:
                return await self._handle_order_cancelled(event)
            elif event.event_type == EventType.ORDER_FAILED:
                return await self._handle_order_failed(event)
            
            return False
        except Exception as e:
            logger.error(f"Error handling order event: {e}")
            return False
    
    async def _handle_order_created(self, event: EventPayload) -> bool:
        """處理訂單創建事件"""
        logger.info(f"Order created: {event.data}")
        # 實現訂單創建後的業務邏輯
        return True
    
    async def _handle_order_matched(self, event: EventPayload) -> bool:
        """處理訂單匹配事件"""
        logger.info(f"Order matched: {event.data}")
        # 實現訂單匹配後的業務邏輯
        return True
    
    async def _handle_order_cancelled(self, event: EventPayload) -> bool:
        """處理訂單取消事件"""
        logger.info(f"Order cancelled: {event.data}")
        # 實現訂單取消後的業務邏輯
        return True
    
    async def _handle_order_failed(self, event: EventPayload) -> bool:
        """處理訂單失敗事件"""
        logger.error(f"Order failed: {event.data}")
        # 實現訂單失敗後的業務邏輯
        return True

class UserEventHandler(EventHandler):
    """使用者事件處理器"""
    
    def __init__(self, user_service, notification_service=None):
        super().__init__("UserEventHandler", [
            EventType.USER_POINTS_UPDATED,
            EventType.USER_PORTFOLIO_UPDATED,
            EventType.USER_LOGIN
        ])
        self.user_service = user_service
        self.notification_service = notification_service
    
    async def handle_event(self, event: EventPayload) -> bool:
        """處理使用者事件"""
        try:
            if event.event_type == EventType.USER_POINTS_UPDATED:
                return await self._handle_points_updated(event)
            elif event.event_type == EventType.USER_PORTFOLIO_UPDATED:
                return await self._handle_portfolio_updated(event)
            elif event.event_type == EventType.USER_LOGIN:
                return await self._handle_user_login(event)
            
            return False
        except Exception as e:
            logger.error(f"Error handling user event: {e}")
            return False
    
    async def _handle_points_updated(self, event: EventPayload) -> bool:
        """處理使用者點數更新事件"""
        logger.info(f"User points updated: {event.data}")
        # 可以在這裡觸發通知或其他業務邏輯
        return True
    
    async def _handle_portfolio_updated(self, event: EventPayload) -> bool:
        """處理使用者組合更新事件"""
        logger.info(f"User portfolio updated: {event.data}")
        return True
    
    async def _handle_user_login(self, event: EventPayload) -> bool:
        """處理使用者登入事件"""
        logger.info(f"User login: {event.data}")
        return True

class MarketEventHandler(EventHandler):
    """市場事件處理器"""
    
    def __init__(self, market_service):
        super().__init__("MarketEventHandler", [
            EventType.MARKET_OPENED,
            EventType.MARKET_CLOSED,
            EventType.PRICE_UPDATED
        ])
        self.market_service = market_service
    
    async def handle_event(self, event: EventPayload) -> bool:
        """處理市場事件"""
        try:
            if event.event_type == EventType.MARKET_OPENED:
                return await self._handle_market_opened(event)
            elif event.event_type == EventType.MARKET_CLOSED:
                return await self._handle_market_closed(event)
            elif event.event_type == EventType.PRICE_UPDATED:
                return await self._handle_price_updated(event)
            
            return False
        except Exception as e:
            logger.error(f"Error handling market event: {e}")
            return False
    
    async def _handle_market_opened(self, event: EventPayload) -> bool:
        """處理市場開放事件"""
        logger.info(f"Market opened: {event.data}")
        return True
    
    async def _handle_market_closed(self, event: EventPayload) -> bool:
        """處理市場關閉事件"""
        logger.info(f"Market closed: {event.data}")
        return True
    
    async def _handle_price_updated(self, event: EventPayload) -> bool:
        """處理價格更新事件"""
        logger.debug(f"Price updated: {event.data}")
        return True

# 全域事件匯流服務實例
_event_bus_service: Optional[EventBusService] = None

def get_event_bus_service() -> Optional[EventBusService]:
    """獲取事件匯流服務實例"""
    return _event_bus_service

async def initialize_event_bus_service(max_event_history: int = 10000) -> EventBusService:
    """初始化事件匯流服務"""
    global _event_bus_service
    
    if _event_bus_service:
        await _event_bus_service.stop()
    
    _event_bus_service = EventBusService(max_event_history)
    await _event_bus_service.start()
    
    logger.info("Event bus service initialized")
    return _event_bus_service