"""
Unit of Work Implementation
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any
import logging
from contextlib import asynccontextmanager

from app.domain.common.repositories import UnitOfWork
from app.domain.common.events import DomainEvent, AggregateRoot
from app.domain.common.exceptions import ConcurrencyException
from app.core.database import get_database

logger = logging.getLogger(__name__)


class MongoUnitOfWork(UnitOfWork):
    """
    MongoDB 工作單元實現
    """
    
    def __init__(self):
        self._db = None
        self._session = None
        self._aggregates: Dict[str, AggregateRoot] = {}
        self._events: List[DomainEvent] = []
        self._in_transaction = False
        self._event_bus = None
    
    async def begin(self):
        """開始事務"""
        if self._in_transaction:
            raise ConcurrencyException("Transaction already in progress", "UnitOfWork", "transaction_state")
        
        self._db = get_database()
        self._session = await self._db.client.start_session()
        await self._session.start_transaction()
        self._in_transaction = True
        
        logger.debug("Transaction started")
    
    async def commit(self):
        """提交事務"""
        if not self._in_transaction:
            raise ConcurrencyException("No transaction in progress", "UnitOfWork", "transaction_state")
        
        try:
            # 提交數據庫事務
            await self._session.commit_transaction()
            
            # 發布領域事件
            await self._publish_events()
            
            # 清理狀態
            self._cleanup()
            
            logger.debug("Transaction committed successfully")
            
        except Exception as e:
            await self.rollback()
            logger.error(f"Error committing transaction: {e}")
            raise
    
    async def rollback(self):
        """回滾事務"""
        if not self._in_transaction:
            return
        
        try:
            await self._session.abort_transaction()
            logger.debug("Transaction rolled back")
        except Exception as e:
            logger.error(f"Error rolling back transaction: {e}")
        finally:
            self._cleanup()
    
    def register_aggregate(self, aggregate: AggregateRoot) -> None:
        """註冊聚合"""
        aggregate_id = str(id(aggregate))  # 使用對象 ID 作為鍵
        self._aggregates[aggregate_id] = aggregate
        
        # 收集領域事件
        if aggregate.has_domain_events():
            self._events.extend(aggregate.get_domain_events())
    
    def get_session(self):
        """獲取數據庫會話"""
        return self._session
    
    def get_database(self):
        """獲取數據庫"""
        return self._db
    
    def set_event_bus(self, event_bus) -> None:
        """設置事件總線"""
        self._event_bus = event_bus
    
    async def _publish_events(self) -> None:
        """發布領域事件"""
        if not self._events or not self._event_bus:
            return
        
        try:
            # 批量發布事件
            await self._event_bus.publish_batch(self._events)
            
            # 清除聚合的事件
            for aggregate in self._aggregates.values():
                aggregate.clear_domain_events()
            
            logger.debug(f"Published {len(self._events)} domain events")
            
        except Exception as e:
            logger.error(f"Error publishing events: {e}")
            raise
    
    def _cleanup(self) -> None:
        """清理狀態"""
        self._in_transaction = False
        self._aggregates.clear()
        self._events.clear()
        
        if self._session:
            self._session.end_session()
            self._session = None
    
    async def __aenter__(self):
        """進入上下文管理器"""
        await self.begin()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器"""
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()


class InMemoryUnitOfWork(UnitOfWork):
    """
    內存工作單元實現
    主要用於測試
    """
    
    def __init__(self):
        self._aggregates: Dict[str, AggregateRoot] = {}
        self._events: List[DomainEvent] = []
        self._in_transaction = False
        self._event_bus = None
        self._committed = False
    
    async def begin(self):
        """開始事務"""
        if self._in_transaction:
            raise ConcurrencyException("Transaction already in progress", "UnitOfWork", "transaction_state")
        
        self._in_transaction = True
        self._committed = False
        logger.debug("In-memory transaction started")
    
    async def commit(self):
        """提交事務"""
        if not self._in_transaction:
            raise ConcurrencyException("No transaction in progress", "UnitOfWork", "transaction_state")
        
        try:
            # 發布領域事件
            await self._publish_events()
            
            self._committed = True
            self._cleanup()
            
            logger.debug("In-memory transaction committed")
            
        except Exception as e:
            await self.rollback()
            logger.error(f"Error committing in-memory transaction: {e}")
            raise
    
    async def rollback(self):
        """回滾事務"""
        if not self._in_transaction:
            return
        
        self._cleanup()
        logger.debug("In-memory transaction rolled back")
    
    def register_aggregate(self, aggregate: AggregateRoot) -> None:
        """註冊聚合"""
        aggregate_id = str(id(aggregate))
        self._aggregates[aggregate_id] = aggregate
        
        # 收集領域事件
        if aggregate.has_domain_events():
            self._events.extend(aggregate.get_domain_events())
    
    def set_event_bus(self, event_bus) -> None:
        """設置事件總線"""
        self._event_bus = event_bus
    
    def was_committed(self) -> bool:
        """是否已提交"""
        return self._committed
    
    async def _publish_events(self) -> None:
        """發布領域事件"""
        if not self._events or not self._event_bus:
            return
        
        try:
            # 批量發布事件
            await self._event_bus.publish_batch(self._events)
            
            # 清除聚合的事件
            for aggregate in self._aggregates.values():
                aggregate.clear_domain_events()
            
            logger.debug(f"Published {len(self._events)} domain events")
            
        except Exception as e:
            logger.error(f"Error publishing events: {e}")
            raise
    
    def _cleanup(self) -> None:
        """清理狀態"""
        self._in_transaction = False
        self._aggregates.clear()
        self._events.clear()
    
    async def __aenter__(self):
        """進入上下文管理器"""
        await self.begin()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器"""
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()


@asynccontextmanager
async def create_unit_of_work(use_transaction: bool = True) -> UnitOfWork:
    """
    創建工作單元的便捷函數
    """
    if use_transaction:
        uow = MongoUnitOfWork()
    else:
        uow = InMemoryUnitOfWork()
    
    async with uow:
        yield uow