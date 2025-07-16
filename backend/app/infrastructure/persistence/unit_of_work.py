"""
Unit of Work Implementation
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Set
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClient, AsyncIOMotorSession
from contextlib import asynccontextmanager
import logging
from datetime import datetime
from enum import Enum

from ...application.common.interfaces import UnitOfWork
from ...domain.common.exceptions import BusinessRuleException

logger = logging.getLogger(__name__)


class TransactionState(Enum):
    """事務狀態"""
    INACTIVE = "inactive"
    ACTIVE = "active"
    COMMITTED = "committed"
    ABORTED = "aborted"


class TransactionContext:
    """事務上下文"""
    
    def __init__(self, transaction_id: str):
        self.transaction_id = transaction_id
        self.state = TransactionState.INACTIVE
        self.started_at: Optional[datetime] = None
        self.committed_at: Optional[datetime] = None
        self.aborted_at: Optional[datetime] = None
        self.operations: List[Dict[str, Any]] = []
        self.savepoints: Dict[str, Any] = {}
    
    def start(self):
        """開始事務"""
        self.state = TransactionState.ACTIVE
        self.started_at = datetime.utcnow()
    
    def commit(self):
        """提交事務"""
        self.state = TransactionState.COMMITTED
        self.committed_at = datetime.utcnow()
    
    def abort(self):
        """中止事務"""
        self.state = TransactionState.ABORTED
        self.aborted_at = datetime.utcnow()
    
    def add_operation(self, operation: Dict[str, Any]):
        """添加操作記錄"""
        self.operations.append({
            **operation,
            "timestamp": datetime.utcnow()
        })
    
    def is_active(self) -> bool:
        """檢查事務是否活躍"""
        return self.state == TransactionState.ACTIVE
    
    def get_duration(self) -> Optional[float]:
        """獲取事務持續時間"""
        if not self.started_at:
            return None
        
        end_time = self.committed_at or self.aborted_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()


class MongoUnitOfWork(UnitOfWork):
    """MongoDB Unit of Work 實現"""
    
    def __init__(self, client: AsyncIOMotorClient, database: AsyncIOMotorDatabase):
        self.client = client
        self.database = database
        self.session: Optional[AsyncIOMotorSession] = None
        self.transaction_context: Optional[TransactionContext] = None
        self.is_nested = False
        self.nested_transactions: List[TransactionContext] = []
    
    async def begin(self) -> None:
        """開始事務"""
        if self.session is not None:
            # 已經在事務中，創建嵌套事務
            await self._begin_nested()
            return
        
        try:
            # 開始新會話
            self.session = await self.client.start_session()
            
            # 創建事務上下文
            transaction_id = self._generate_transaction_id()
            self.transaction_context = TransactionContext(transaction_id)
            
            # 開始事務
            await self.session.start_transaction()
            self.transaction_context.start()
            
            logger.info(f"Transaction started: {transaction_id}")
            
        except Exception as e:
            logger.error(f"Failed to start transaction: {e}")
            await self._cleanup_session()
            raise BusinessRuleException(f"Failed to start transaction: {e}", "transaction_start_failed")
    
    async def _begin_nested(self) -> None:
        """開始嵌套事務"""
        if not self.transaction_context or not self.transaction_context.is_active():
            raise BusinessRuleException("No active transaction for nested transaction", "no_active_transaction")
        
        # 創建嵌套事務上下文
        nested_transaction_id = self._generate_transaction_id()
        nested_context = TransactionContext(nested_transaction_id)
        nested_context.start()
        
        # 保存當前事務上下文
        self.nested_transactions.append(self.transaction_context)
        self.transaction_context = nested_context
        self.is_nested = True
        
        logger.info(f"Nested transaction started: {nested_transaction_id}")
    
    async def commit(self) -> None:
        """提交事務"""
        if self.transaction_context is None:
            raise BusinessRuleException("No active transaction to commit", "no_active_transaction")
        
        if not self.transaction_context.is_active():
            raise BusinessRuleException("Transaction is not active", "transaction_not_active")
        
        try:
            if self.is_nested:
                # 提交嵌套事務
                await self._commit_nested()
            else:
                # 提交主事務
                await self._commit_main()
            
            logger.info(f"Transaction committed: {self.transaction_context.transaction_id}")
            
        except Exception as e:
            logger.error(f"Failed to commit transaction: {e}")
            await self.rollback()
            raise BusinessRuleException(f"Failed to commit transaction: {e}", "transaction_commit_failed")
    
    async def _commit_nested(self) -> None:
        """提交嵌套事務"""
        self.transaction_context.commit()
        
        # 恢復父事務上下文
        if self.nested_transactions:
            parent_context = self.nested_transactions.pop()
            # 將嵌套事務的操作合併到父事務
            parent_context.operations.extend(self.transaction_context.operations)
            self.transaction_context = parent_context
            
            if not self.nested_transactions:
                self.is_nested = False
    
    async def _commit_main(self) -> None:
        """提交主事務"""
        if self.session:
            await self.session.commit_transaction()
        
        self.transaction_context.commit()
        await self._cleanup_session()
    
    async def rollback(self) -> None:
        """回滾事務"""
        if self.transaction_context is None:
            logger.warning("No active transaction to rollback")
            return
        
        try:
            if self.is_nested:
                # 回滾嵌套事務
                await self._rollback_nested()
            else:
                # 回滾主事務
                await self._rollback_main()
            
            logger.info(f"Transaction rolled back: {self.transaction_context.transaction_id}")
            
        except Exception as e:
            logger.error(f"Failed to rollback transaction: {e}")
            await self._cleanup_session()
            raise
    
    async def _rollback_nested(self) -> None:
        """回滾嵌套事務"""
        self.transaction_context.abort()
        
        # 恢復父事務上下文
        if self.nested_transactions:
            self.transaction_context = self.nested_transactions.pop()
            
            if not self.nested_transactions:
                self.is_nested = False
    
    async def _rollback_main(self) -> None:
        """回滾主事務"""
        if self.session:
            await self.session.abort_transaction()
        
        self.transaction_context.abort()
        await self._cleanup_session()
    
    async def _cleanup_session(self) -> None:
        """清理會話"""
        if self.session:
            await self.session.end_session()
            self.session = None
        
        self.transaction_context = None
        self.is_nested = False
        self.nested_transactions.clear()
    
    def get_session(self) -> Optional[AsyncIOMotorSession]:
        """獲取當前會話"""
        return self.session
    
    def get_transaction_context(self) -> Optional[TransactionContext]:
        """獲取事務上下文"""
        return self.transaction_context
    
    def is_in_transaction(self) -> bool:
        """檢查是否在事務中"""
        return (self.transaction_context is not None and 
                self.transaction_context.is_active())
    
    def add_operation(self, operation_type: str, collection: str, document_id: str, data: Any = None):
        """添加操作記錄"""
        if self.transaction_context:
            self.transaction_context.add_operation({
                "type": operation_type,
                "collection": collection,
                "document_id": document_id,
                "data": data
            })
    
    def _generate_transaction_id(self) -> str:
        """生成事務 ID"""
        from bson import ObjectId
        return str(ObjectId())
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        await self.begin()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()


class InMemoryUnitOfWork(UnitOfWork):
    """內存 Unit of Work 實現（用於測試）"""
    
    def __init__(self):
        self.is_active = False
        self.operations: List[Dict[str, Any]] = []
        self.should_rollback = False
    
    async def begin(self) -> None:
        """開始事務"""
        self.is_active = True
        self.operations.clear()
        self.should_rollback = False
        logger.info("In-memory transaction started")
    
    async def commit(self) -> None:
        """提交事務"""
        if not self.is_active:
            raise BusinessRuleException("No active transaction", "no_active_transaction")
        
        if self.should_rollback:
            raise BusinessRuleException("Transaction marked for rollback", "transaction_rollback_required")
        
        self.is_active = False
        logger.info("In-memory transaction committed")
    
    async def rollback(self) -> None:
        """回滾事務"""
        if not self.is_active:
            logger.warning("No active transaction to rollback")
            return
        
        self.is_active = False
        self.operations.clear()
        logger.info("In-memory transaction rolled back")
    
    def mark_for_rollback(self):
        """標記事務需要回滾"""
        self.should_rollback = True
    
    def add_operation(self, operation: Dict[str, Any]):
        """添加操作記錄"""
        if self.is_active:
            self.operations.append({
                **operation,
                "timestamp": datetime.utcnow()
            })
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        await self.begin()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()


class UnitOfWorkManager:
    """Unit of Work 管理器"""
    
    def __init__(self, unit_of_work: UnitOfWork):
        self.unit_of_work = unit_of_work
        self.active_transactions: Dict[str, TransactionContext] = {}
    
    @asynccontextmanager
    async def transaction(self):
        """事務上下文管理器"""
        async with self.unit_of_work:
            yield self.unit_of_work
    
    async def execute_in_transaction(self, operation):
        """在事務中執行操作"""
        async with self.transaction():
            if asyncio.iscoroutinefunction(operation):
                return await operation()
            else:
                return operation()
    
    def get_current_transaction(self) -> Optional[TransactionContext]:
        """獲取當前事務"""
        if hasattr(self.unit_of_work, 'get_transaction_context'):
            return self.unit_of_work.get_transaction_context()
        return None
    
    def is_in_transaction(self) -> bool:
        """檢查是否在事務中"""
        if hasattr(self.unit_of_work, 'is_in_transaction'):
            return self.unit_of_work.is_in_transaction()
        return False


class TransactionMetrics:
    """事務指標"""
    
    def __init__(self):
        self.total_transactions = 0
        self.successful_transactions = 0
        self.failed_transactions = 0
        self.rollback_transactions = 0
        self.nested_transactions = 0
        self.average_duration = 0.0
        self.longest_transaction = 0.0
        self.shortest_transaction = float('inf')
    
    def record_transaction(self, context: TransactionContext):
        """記錄事務"""
        self.total_transactions += 1
        
        if context.state == TransactionState.COMMITTED:
            self.successful_transactions += 1
        elif context.state == TransactionState.ABORTED:
            self.failed_transactions += 1
            self.rollback_transactions += 1
        
        # 記錄持續時間
        duration = context.get_duration()
        if duration is not None:
            self.longest_transaction = max(self.longest_transaction, duration)
            self.shortest_transaction = min(self.shortest_transaction, duration)
            
            # 計算平均持續時間
            total_duration = self.average_duration * (self.total_transactions - 1) + duration
            self.average_duration = total_duration / self.total_transactions
    
    def get_metrics(self) -> Dict[str, Any]:
        """獲取指標"""
        return {
            "total_transactions": self.total_transactions,
            "successful_transactions": self.successful_transactions,
            "failed_transactions": self.failed_transactions,
            "rollback_transactions": self.rollback_transactions,
            "success_rate": self.successful_transactions / max(1, self.total_transactions),
            "average_duration": self.average_duration,
            "longest_transaction": self.longest_transaction,
            "shortest_transaction": self.shortest_transaction if self.shortest_transaction != float('inf') else 0.0
        }


# 工廠函數
def create_unit_of_work(config: Dict[str, Any]) -> UnitOfWork:
    """創建 Unit of Work"""
    uow_type = config.get('type', 'mongo')
    
    if uow_type == 'mongo':
        from ...core.database import get_database, get_client
        client = get_client()
        database = get_database()
        return MongoUnitOfWork(client, database)
    elif uow_type == 'memory':
        return InMemoryUnitOfWork()
    else:
        raise ValueError(f"Unsupported UnitOfWork type: {uow_type}")


# 全局事務指標
transaction_metrics = TransactionMetrics()


import asyncio