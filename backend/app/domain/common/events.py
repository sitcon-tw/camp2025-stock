"""
Domain Events Infrastructure
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, Callable, Awaitable
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T', bound='DomainEvent')


class DomainEvent(ABC):
    """
    領域事件基類
    所有領域事件都應該繼承此類
    """
    
    def __init__(self, **kwargs):
        self.event_id = kwargs.get('event_id', str(uuid4()))
        self.occurred_at = kwargs.get('occurred_at', datetime.utcnow())
        self.event_version = kwargs.get('event_version', 1)
        self.correlation_id = kwargs.get('correlation_id', None)
    
    @property
    def event_type(self) -> str:
        """事件類型"""
        return self.__class__.__name__
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
            "event_version": self.event_version,
            "correlation_id": self.correlation_id,
            "data": self._get_event_data()
        }
    
    @abstractmethod
    def _get_event_data(self) -> Dict[str, Any]:
        """獲取事件數據"""
        pass


class DomainEventHandler(ABC, Generic[T]):
    """
    領域事件處理器基類
    """
    
    @abstractmethod
    async def handle(self, event: T) -> None:
        """處理事件"""
        pass
    
    @property
    @abstractmethod
    def event_type(self) -> Type[T]:
        """處理的事件類型"""
        pass


class DomainEventBus(ABC):
    """
    領域事件總線介面
    """
    
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """發布事件"""
        pass
    
    @abstractmethod
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """批量發布事件"""
        pass
    
    @abstractmethod
    def subscribe(self, event_type: Type[T], handler: DomainEventHandler[T]) -> None:
        """訂閱事件"""
        pass
    
    @abstractmethod
    def unsubscribe(self, event_type: Type[T], handler: DomainEventHandler[T]) -> None:
        """取消訂閱事件"""
        pass
    
    @abstractmethod
    async def start(self) -> None:
        """啟動事件總線"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """停止事件總線"""
        pass


class EventStore(ABC):
    """
    事件存儲介面
    """
    
    @abstractmethod
    async def save_event(self, event: DomainEvent) -> None:
        """保存事件"""
        pass
    
    @abstractmethod
    async def save_events(self, events: List[DomainEvent]) -> None:
        """批量保存事件"""
        pass
    
    @abstractmethod
    async def get_events(self, aggregate_id: str, from_version: int = 0) -> List[DomainEvent]:
        """獲取聚合的事件"""
        pass
    
    @abstractmethod
    async def get_events_by_type(self, event_type: str, skip: int = 0, limit: int = 100) -> List[DomainEvent]:
        """根據類型獲取事件"""
        pass


class EventDispatcher:
    """
    事件調度器
    負責將事件分發給相應的處理器
    """
    
    def __init__(self):
        self._handlers: Dict[Type[DomainEvent], List[DomainEventHandler]] = {}
        self._middleware: List[Callable[[DomainEvent], Awaitable[None]]] = []
    
    def register_handler(self, event_type: Type[T], handler: DomainEventHandler[T]) -> None:
        """註冊事件處理器"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.info(f"Registered handler {handler.__class__.__name__} for event {event_type.__name__}")
    
    def unregister_handler(self, event_type: Type[T], handler: DomainEventHandler[T]) -> None:
        """取消註冊事件處理器"""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)
            if not self._handlers[event_type]:
                del self._handlers[event_type]
            logger.info(f"Unregistered handler {handler.__class__.__name__} for event {event_type.__name__}")
    
    def add_middleware(self, middleware: Callable[[DomainEvent], Awaitable[None]]) -> None:
        """添加中間件"""
        self._middleware.append(middleware)
    
    async def dispatch(self, event: DomainEvent) -> None:
        """分發事件"""
        try:
            # 執行中間件
            for middleware in self._middleware:
                await middleware(event)
            
            # 查找處理器
            event_type = type(event)
            handlers = self._handlers.get(event_type, [])
            
            if not handlers:
                logger.warning(f"No handlers registered for event {event_type.__name__}")
                return
            
            # 執行處理器
            for handler in handlers:
                try:
                    await handler.handle(event)
                    logger.debug(f"Event {event.event_type} handled by {handler.__class__.__name__}")
                except Exception as e:
                    logger.error(f"Error handling event {event.event_type} with {handler.__class__.__name__}: {e}")
                    # 根據配置決定是否繼續處理其他處理器
                    # 這裡選擇繼續處理，避免單個處理器失敗影響其他處理器
                    continue
        
        except Exception as e:
            logger.error(f"Error dispatching event {event.event_type}: {e}")
            raise


class AggregateRoot:
    """
    聚合根基類
    支援領域事件的聚合根
    """
    
    def __init__(self):
        self._domain_events: List[DomainEvent] = []
        self._version: int = 0
    
    def add_domain_event(self, event: DomainEvent) -> None:
        """添加領域事件"""
        self._domain_events.append(event)
    
    def get_domain_events(self) -> List[DomainEvent]:
        """獲取領域事件"""
        return self._domain_events.copy()
    
    def clear_domain_events(self) -> None:
        """清除領域事件"""
        self._domain_events.clear()
    
    def has_domain_events(self) -> bool:
        """是否有領域事件"""
        return len(self._domain_events) > 0
    
    @property
    def version(self) -> int:
        """版本號"""
        return self._version
    
    def increment_version(self) -> None:
        """增加版本號"""
        self._version += 1


# 具體的領域事件

class UserCreatedEvent(DomainEvent):
    """使用者創建事件"""
    
    def __init__(self, user_id: str, telegram_id: int, username: str, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.telegram_id = telegram_id
        self.username = username
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "telegram_id": self.telegram_id,
            "username": self.username
        }


class PointsChangedEvent(DomainEvent):
    """點數變更事件"""
    
    def __init__(self, user_id: str, old_points: int, new_points: int, change_amount: int, change_type: str, description: str, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.old_points = old_points
        self.new_points = new_points
        self.change_amount = change_amount
        self.change_type = change_type
        self.description = description
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "old_points": self.old_points,
            "new_points": self.new_points,
            "change_amount": self.change_amount,
            "change_type": self.change_type,
            "description": self.description
        }


class OrderCreatedEvent(DomainEvent):
    """訂單創建事件"""
    
    def __init__(self, order_id: str, user_id: str, symbol: str, order_type: str, quantity: int, price: int, **kwargs):
        super().__init__(**kwargs)
        self.order_id = order_id
        self.user_id = user_id
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.price = price
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "symbol": self.symbol,
            "order_type": self.order_type,
            "quantity": self.quantity,
            "price": self.price
        }


class OrderExecutedEvent(DomainEvent):
    """訂單執行事件"""
    
    def __init__(self, order_id: str, user_id: str, symbol: str, executed_quantity: int, executed_price: int, total_amount: int, **kwargs):
        super().__init__(**kwargs)
        self.order_id = order_id
        self.user_id = user_id
        self.symbol = symbol
        self.executed_quantity = executed_quantity
        self.executed_price = executed_price
        self.total_amount = total_amount
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "symbol": self.symbol,
            "executed_quantity": self.executed_quantity,
            "executed_price": self.executed_price,
            "total_amount": self.total_amount
        }


class MarketOpenedEvent(DomainEvent):
    """市場開放事件"""
    
    def __init__(self, opened_by: str, reason: str, **kwargs):
        super().__init__(**kwargs)
        self.opened_by = opened_by
        self.reason = reason
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "opened_by": self.opened_by,
            "reason": self.reason
        }


class MarketClosedEvent(DomainEvent):
    """市場關閉事件"""
    
    def __init__(self, closed_by: str, reason: str, **kwargs):
        super().__init__(**kwargs)
        self.closed_by = closed_by
        self.reason = reason
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "closed_by": self.closed_by,
            "reason": self.reason
        }


class StudentRegisteredEvent(DomainEvent):
    """學生註冊事件"""
    
    def __init__(self, student_id: str, real_name: str, group_id: str, **kwargs):
        super().__init__(**kwargs)
        self.student_id = student_id
        self.real_name = real_name
        self.group_id = group_id
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "student_id": self.student_id,
            "real_name": self.real_name,
            "group_id": self.group_id
        }


class DebtCreatedEvent(DomainEvent):
    """債務創建事件"""
    
    def __init__(self, debt_id: str, user_id: str, amount: int, description: str, **kwargs):
        super().__init__(**kwargs)
        self.debt_id = debt_id
        self.user_id = user_id
        self.amount = amount
        self.description = description
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "debt_id": self.debt_id,
            "user_id": self.user_id,
            "amount": self.amount,
            "description": self.description
        }


class DebtResolvedEvent(DomainEvent):
    """債務解決事件"""
    
    def __init__(self, debt_id: str, user_id: str, resolved_by: str, amount: int, **kwargs):
        super().__init__(**kwargs)
        self.debt_id = debt_id
        self.user_id = user_id
        self.resolved_by = resolved_by
        self.amount = amount
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "debt_id": self.debt_id,
            "user_id": self.user_id,
            "resolved_by": self.resolved_by,
            "amount": self.amount
        }