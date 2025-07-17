"""
Infrastructure Layer Repository Implementations
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.core.database import get_database, Collections
from app.domain.user.repositories import UserRepository, PointLogRepository
from app.domain.user.entities import User, PointLog
from app.domain.trading.repositories import StockRepository, OrderRepository, UserStockRepository
from app.domain.trading.entities import Stock, StockOrder, UserStock
from app.domain.system.repositories import StudentRepository, UserDebtRepository
from app.domain.system.entities import Student, UserDebt
from app.domain.common.exceptions import EntityNotFoundException
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MongoUserRepository(UserRepository):
    """MongoDB 使用者存儲庫實現"""
    
    def __init__(self):
        self.db = get_database()
    
    async def find_by_id(self, user_id: ObjectId) -> Optional[User]:
        """根據 ID 查找使用者"""
        try:
            data = await self.db[Collections.USERS].find_one({"_id": user_id})
            return User.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Failed to find user by ID {user_id}: {e}")
            return None
    
    async def find_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """根據 Telegram ID 查找使用者"""
        try:
            data = await self.db[Collections.USERS].find_one({"telegram_id": telegram_id})
            return User.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Failed to find user by telegram ID {telegram_id}: {e}")
            return None
    
    async def find_by_student_id(self, student_id: str) -> Optional[User]:
        """根據學生 ID 查找使用者"""
        try:
            data = await self.db[Collections.USERS].find_one({"student_id": student_id})
            return User.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Failed to find user by student ID {student_id}: {e}")
            return None
    
    async def save(self, user: User) -> User:
        """儲存使用者"""
        try:
            data = user.to_dict()
            if user.id is None:
                # 新增使用者
                result = await self.db[Collections.USERS].insert_one(data)
                user.id = result.inserted_id
            else:
                # 更新使用者
                await self.db[Collections.USERS].replace_one({"_id": user.id}, data)
            return user
        except Exception as e:
            logger.error(f"Failed to save user: {e}")
            raise
    
    async def update(self, user: User) -> bool:
        """更新使用者"""
        try:
            data = user.to_dict()
            result = await self.db[Collections.USERS].replace_one({"_id": user.id}, data)
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            return False
    
    async def delete(self, user_id: ObjectId) -> bool:
        """刪除使用者"""
        try:
            result = await self.db[Collections.USERS].delete_one({"_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            return False
    
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """查找所有使用者"""
        try:
            cursor = self.db[Collections.USERS].find().skip(skip).limit(limit)
            users = []
            async for data in cursor:
                users.append(User.from_dict(data))
            return users
        except Exception as e:
            logger.error(f"Failed to find all users: {e}")
            return []
    
    async def count(self) -> int:
        """計算使用者總數"""
        try:
            return await self.db[Collections.USERS].count_documents({})
        except Exception as e:
            logger.error(f"Failed to count users: {e}")
            return 0
    
    async def find_by_group_id(self, group_id: str) -> List[User]:
        """根據群組 ID 查找使用者"""
        try:
            cursor = self.db[Collections.USERS].find({"group_id": group_id})
            users = []
            async for data in cursor:
                users.append(User.from_dict(data))
            return users
        except Exception as e:
            logger.error(f"Failed to find users by group ID: {e}")
            return []
    
    async def exists(self, user_id: ObjectId) -> bool:
        """檢查使用者是否存在"""
        try:
            count = await self.db[Collections.USERS].count_documents({"_id": user_id})
            return count > 0
        except Exception as e:
            logger.error(f"Failed to check user existence: {e}")
            return False
    
    async def find_by_specification(self, specification: Dict[str, Any]) -> List[User]:
        """根據規格查找使用者"""
        try:
            cursor = self.db[Collections.USERS].find(specification)
            users = []
            async for data in cursor:
                users.append(User.from_dict(data))
            return users
        except Exception as e:
            logger.error(f"Failed to find users by specification: {e}")
            return []
    
    async def find_one_by_specification(self, specification: Dict[str, Any]) -> Optional[User]:
        """根據規格查找單一使用者"""
        try:
            data = await self.db[Collections.USERS].find_one(specification)
            return User.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Failed to find user by specification: {e}")
            return None
    
    async def count_by_specification(self, specification: Dict[str, Any]) -> int:
        """根據規格計算使用者數量"""
        try:
            return await self.db[Collections.USERS].count_documents(specification)
        except Exception as e:
            logger.error(f"Failed to count users by specification: {e}")
            return 0


class MongoPointLogRepository(PointLogRepository):
    """MongoDB 點數記錄存儲庫實現"""
    
    def __init__(self):
        self.db = get_database()
    
    async def save(self, point_log: PointLog) -> PointLog:
        """儲存點數記錄"""
        try:
            data = point_log.to_dict()
            if point_log.id is None:
                result = await self.db[Collections.POINT_LOGS].insert_one(data)
                point_log.id = result.inserted_id
            else:
                await self.db[Collections.POINT_LOGS].replace_one({"_id": point_log.id}, data)
            return point_log
        except Exception as e:
            logger.error(f"Failed to save point log: {e}")
            raise
    
    async def find_by_user_id(self, user_id: ObjectId, skip: int = 0, limit: int = 100) -> List[PointLog]:
        """根據使用者 ID 查找點數記錄"""
        try:
            cursor = self.db[Collections.POINT_LOGS].find({"user_id": user_id}).sort("timestamp", -1).skip(skip).limit(limit)
            logs = []
            async for data in cursor:
                logs.append(PointLog.from_dict(data))
            return logs
        except Exception as e:
            logger.error(f"Failed to find point logs by user ID: {e}")
            return []
    
    async def find_by_user_id_and_type(self, user_id: ObjectId, change_type: str, skip: int = 0, limit: int = 100) -> List[PointLog]:
        """根據使用者 ID 和變更類型查找點數記錄"""
        try:
            cursor = self.db[Collections.POINT_LOGS].find({
                "user_id": user_id,
                "change_type": change_type
            }).sort("timestamp", -1).skip(skip).limit(limit)
            logs = []
            async for data in cursor:
                logs.append(PointLog.from_dict(data))
            return logs
        except Exception as e:
            logger.error(f"Failed to find point logs by user ID and type: {e}")
            return []
    
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[PointLog]:
        """查找所有點數記錄"""
        try:
            cursor = self.db[Collections.POINT_LOGS].find().sort("timestamp", -1).skip(skip).limit(limit)
            logs = []
            async for data in cursor:
                logs.append(PointLog.from_dict(data))
            return logs
        except Exception as e:
            logger.error(f"Failed to find all point logs: {e}")
            return []
    
    async def delete_by_user_id(self, user_id: ObjectId) -> bool:
        """刪除使用者的所有點數記錄"""
        try:
            result = await self.db[Collections.POINT_LOGS].delete_many({"user_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete point logs by user ID: {e}")
            return False
    
    # Repository[PointLog] 抽象方法實現
    async def find_by_id(self, entity_id: ObjectId) -> Optional[PointLog]:
        """根據 ID 查找點數記錄"""
        try:
            data = await self.db[Collections.POINT_LOGS].find_one({"_id": entity_id})
            return PointLog.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Failed to find point log by ID: {e}")
            return None
    
    async def update(self, entity: PointLog) -> PointLog:
        """更新點數記錄"""
        try:
            data = entity.to_dict()
            await self.db[Collections.POINT_LOGS].replace_one({"_id": entity.id}, data)
            return entity
        except Exception as e:
            logger.error(f"Failed to update point log: {e}")
            raise
    
    async def delete(self, entity_id: ObjectId) -> bool:
        """刪除點數記錄"""
        try:
            result = await self.db[Collections.POINT_LOGS].delete_one({"_id": entity_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete point log: {e}")
            return False
    
    async def exists(self, entity_id: ObjectId) -> bool:
        """檢查點數記錄是否存在"""
        try:
            count = await self.db[Collections.POINT_LOGS].count_documents({"_id": entity_id})
            return count > 0
        except Exception as e:
            logger.error(f"Failed to check point log existence: {e}")
            return False
    
    async def count(self) -> int:
        """計算點數記錄總數"""
        try:
            return await self.db[Collections.POINT_LOGS].count_documents({})
        except Exception as e:
            logger.error(f"Failed to count point logs: {e}")
            return 0
    
    # SpecificationRepository[PointLog] 抽象方法實現
    async def find_by_specification(self, specification: Dict[str, Any]) -> List[PointLog]:
        """根據規格查找點數記錄"""
        try:
            cursor = self.db[Collections.POINT_LOGS].find(specification).sort("timestamp", -1)
            logs = []
            async for data in cursor:
                logs.append(PointLog.from_dict(data))
            return logs
        except Exception as e:
            logger.error(f"Failed to find point logs by specification: {e}")
            return []
    
    async def find_one_by_specification(self, specification: Dict[str, Any]) -> Optional[PointLog]:
        """根據規格查找單一點數記錄"""
        try:
            data = await self.db[Collections.POINT_LOGS].find_one(specification)
            return PointLog.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Failed to find point log by specification: {e}")
            return None
    
    async def count_by_specification(self, specification: Dict[str, Any]) -> int:
        """根據規格計算點數記錄數量"""
        try:
            return await self.db[Collections.POINT_LOGS].count_documents(specification)
        except Exception as e:
            logger.error(f"Failed to count point logs by specification: {e}")
            return 0


class MongoStockRepository(StockRepository):
    """MongoDB 股票存儲庫實現"""
    
    def __init__(self):
        self.db = get_database()
    
    async def find_by_symbol(self, symbol: str) -> Optional[Stock]:
        """根據股票代碼查找股票"""
        try:
            # 假設股票信息存儲在 STOCK_CONFIG 或類似的集合中
            data = await self.db[Collections.STOCK_CONFIG].find_one({"symbol": symbol})
            return Stock.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Failed to find stock by symbol {symbol}: {e}")
            return None
    
    async def find_all(self) -> List[Stock]:
        """查找所有股票"""
        try:
            cursor = self.db[Collections.STOCK_CONFIG].find()
            stocks = []
            async for data in cursor:
                stocks.append(Stock.from_dict(data))
            return stocks
        except Exception as e:
            logger.error(f"Failed to find all stocks: {e}")
            return []
    
    async def save(self, stock: Stock) -> Stock:
        """儲存股票"""
        try:
            data = stock.to_dict()
            await self.db[Collections.STOCK_CONFIG].replace_one(
                {"symbol": stock.symbol}, 
                data, 
                upsert=True
            )
            return stock
        except Exception as e:
            logger.error(f"Failed to save stock: {e}")
            raise
    
    async def update(self, stock: Stock) -> bool:
        """更新股票"""
        try:
            data = stock.to_dict()
            result = await self.db[Collections.STOCK_CONFIG].replace_one(
                {"symbol": stock.symbol}, 
                data
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update stock: {e}")
            return False
    
    async def delete_by_symbol(self, symbol: str) -> bool:
        """根據股票代碼刪除股票"""
        try:
            result = await self.db[Collections.STOCK_CONFIG].delete_one({"symbol": symbol})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete stock by symbol: {e}")
            return False
    
    # Repository[Stock] 抽象方法實現
    async def find_by_id(self, entity_id: ObjectId) -> Optional[Stock]:
        """根據 ID 查找股票"""
        try:
            data = await self.db[Collections.STOCK_CONFIG].find_one({"_id": entity_id})
            return Stock.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Failed to find stock by ID: {e}")
            return None
    
    async def update(self, entity: Stock) -> Stock:
        """更新股票實體"""
        try:
            data = entity.to_dict()
            await self.db[Collections.STOCK_CONFIG].replace_one({"symbol": entity.symbol}, data, upsert=True)
            return entity
        except Exception as e:
            logger.error(f"Failed to update stock entity: {e}")
            raise
    
    async def delete(self, entity_id: ObjectId) -> bool:
        """根據 ID 刪除股票"""
        try:
            result = await self.db[Collections.STOCK_CONFIG].delete_one({"_id": entity_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete stock by ID: {e}")
            return False
    
    async def exists(self, entity_id: ObjectId) -> bool:
        """檢查股票是否存在"""
        try:
            count = await self.db[Collections.STOCK_CONFIG].count_documents({"_id": entity_id})
            return count > 0
        except Exception as e:
            logger.error(f"Failed to check stock existence: {e}")
            return False
    
    async def count(self) -> int:
        """計算股票總數"""
        try:
            return await self.db[Collections.STOCK_CONFIG].count_documents({})
        except Exception as e:
            logger.error(f"Failed to count stocks: {e}")
            return 0
    
    # SpecificationRepository[Stock] 抽象方法實現
    async def find_by_specification(self, specification: Dict[str, Any]) -> List[Stock]:
        """根據規格查找股票"""
        try:
            cursor = self.db[Collections.STOCK_CONFIG].find(specification)
            stocks = []
            async for data in cursor:
                stocks.append(Stock.from_dict(data))
            return stocks
        except Exception as e:
            logger.error(f"Failed to find stocks by specification: {e}")
            return []
    
    async def find_one_by_specification(self, specification: Dict[str, Any]) -> Optional[Stock]:
        """根據規格查找單一股票"""
        try:
            data = await self.db[Collections.STOCK_CONFIG].find_one(specification)
            return Stock.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Failed to find stock by specification: {e}")
            return None
    
    async def count_by_specification(self, specification: Dict[str, Any]) -> int:
        """根據規格計算股票數量"""
        try:
            return await self.db[Collections.STOCK_CONFIG].count_documents(specification)
        except Exception as e:
            logger.error(f"Failed to count stocks by specification: {e}")
            return 0


class MongoOrderRepository(OrderRepository):
    """MongoDB 訂單存儲庫實現"""
    
    def __init__(self):
        self.db = get_database()
    
    async def find_by_id(self, order_id: ObjectId) -> Optional[StockOrder]:
        """根據訂單 ID 查找訂單"""
        try:
            data = await self.db[Collections.STOCK_ORDERS].find_one({"_id": order_id})
            return StockOrder.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Failed to find order by ID {order_id}: {e}")
            return None
    
    async def find_by_user_id(self, user_id: ObjectId, skip: int = 0, limit: int = 100) -> List[StockOrder]:
        """根據使用者 ID 查找訂單"""
        try:
            cursor = self.db[Collections.STOCK_ORDERS].find({"user_id": user_id}).sort("created_at", -1).skip(skip).limit(limit)
            orders = []
            async for data in cursor:
                orders.append(StockOrder.from_dict(data))
            return orders
        except Exception as e:
            logger.error(f"Failed to find orders by user ID: {e}")
            return []
    
    async def find_by_symbol(self, symbol: str, skip: int = 0, limit: int = 100) -> List[StockOrder]:
        """根據股票代碼查找訂單"""
        try:
            cursor = self.db[Collections.STOCK_ORDERS].find({"symbol": symbol}).sort("created_at", -1).skip(skip).limit(limit)
            orders = []
            async for data in cursor:
                orders.append(StockOrder.from_dict(data))
            return orders
        except Exception as e:
            logger.error(f"Failed to find orders by symbol: {e}")
            return []
    
    async def find_active_orders(self, symbol: str = None) -> List[StockOrder]:
        """查找活躍訂單"""
        try:
            query = {"status": {"$in": ["pending", "partial_filled"]}}
            if symbol:
                query["symbol"] = symbol
            
            cursor = self.db[Collections.STOCK_ORDERS].find(query).sort("created_at", 1)
            orders = []
            async for data in cursor:
                orders.append(StockOrder.from_dict(data))
            return orders
        except Exception as e:
            logger.error(f"Failed to find active orders: {e}")
            return []
    
    async def find_by_user_and_symbol(self, user_id: ObjectId, symbol: str) -> List[StockOrder]:
        """根據使用者和股票代碼查找訂單"""
        try:
            cursor = self.db[Collections.STOCK_ORDERS].find({
                "user_id": user_id,
                "symbol": symbol
            }).sort("created_at", -1)
            orders = []
            async for data in cursor:
                orders.append(StockOrder.from_dict(data))
            return orders
        except Exception as e:
            logger.error(f"Failed to find orders by user and symbol: {e}")
            return []
    
    async def save(self, order: StockOrder) -> StockOrder:
        """儲存訂單"""
        try:
            data = order.to_dict()
            if order.id is None:
                result = await self.db[Collections.STOCK_ORDERS].insert_one(data)
                order.id = result.inserted_id
            else:
                await self.db[Collections.STOCK_ORDERS].replace_one({"_id": order.id}, data)
            return order
        except Exception as e:
            logger.error(f"Failed to save order: {e}")
            raise
    
    async def update_order(self, order: StockOrder) -> bool:
        """更新訂單 (返回bool)"""
        try:
            data = order.to_dict()
            result = await self.db[Collections.STOCK_ORDERS].replace_one({"_id": order.id}, data)
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update order: {e}")
            return False
    
    async def delete(self, order_id: ObjectId) -> bool:
        """刪除訂單"""
        try:
            result = await self.db[Collections.STOCK_ORDERS].delete_one({"_id": order_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete order: {e}")
            return False
    
    # Repository[StockOrder] 抽象方法實現
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[StockOrder]:
        """查找所有訂單"""
        try:
            cursor = self.db[Collections.STOCK_ORDERS].find().sort("created_at", -1).skip(skip).limit(limit)
            orders = []
            async for data in cursor:
                orders.append(StockOrder.from_dict(data))
            return orders
        except Exception as e:
            logger.error(f"Failed to find all orders: {e}")
            return []
    
    async def update(self, entity: StockOrder) -> StockOrder:
        """更新訂單實體"""
        try:
            data = entity.to_dict()
            await self.db[Collections.STOCK_ORDERS].replace_one({"_id": entity.id}, data)
            return entity
        except Exception as e:
            logger.error(f"Failed to update order entity: {e}")
            raise
    
    async def exists(self, entity_id: ObjectId) -> bool:
        """檢查訂單是否存在"""
        try:
            count = await self.db[Collections.STOCK_ORDERS].count_documents({"_id": entity_id})
            return count > 0
        except Exception as e:
            logger.error(f"Failed to check order existence: {e}")
            return False
    
    async def count(self) -> int:
        """計算訂單總數"""
        try:
            return await self.db[Collections.STOCK_ORDERS].count_documents({})
        except Exception as e:
            logger.error(f"Failed to count orders: {e}")
            return 0
    
    # SpecificationRepository[StockOrder] 抽象方法實現
    async def find_by_specification(self, specification: Dict[str, Any]) -> List[StockOrder]:
        """根據規格查找訂單"""
        try:
            cursor = self.db[Collections.STOCK_ORDERS].find(specification).sort("created_at", -1)
            orders = []
            async for data in cursor:
                orders.append(StockOrder.from_dict(data))
            return orders
        except Exception as e:
            logger.error(f"Failed to find orders by specification: {e}")
            return []
    
    async def find_one_by_specification(self, specification: Dict[str, Any]) -> Optional[StockOrder]:
        """根據規格查找單一訂單"""
        try:
            data = await self.db[Collections.STOCK_ORDERS].find_one(specification)
            return StockOrder.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Failed to find order by specification: {e}")
            return None
    
    async def count_by_specification(self, specification: Dict[str, Any]) -> int:
        """根據規格計算訂單數量"""
        try:
            return await self.db[Collections.STOCK_ORDERS].count_documents(specification)
        except Exception as e:
            logger.error(f"Failed to count orders by specification: {e}")
            return 0


class MongoUserStockRepository(UserStockRepository):
    """MongoDB 使用者股票持有存儲庫實現"""
    
    def __init__(self):
        self.db = get_database()
    
    async def find_by_user_id(self, user_id: ObjectId) -> List[UserStock]:
        """根據使用者 ID 查找股票持有"""
        try:
            cursor = self.db[Collections.STOCKS].find({"user_id": user_id})
            stocks = []
            async for data in cursor:
                stocks.append(UserStock.from_dict(data))
            return stocks
        except Exception as e:
            logger.error(f"Failed to find user stocks by user ID: {e}")
            return []
    
    async def find_by_user_and_symbol(self, user_id: ObjectId, symbol: str) -> Optional[UserStock]:
        """根據使用者和股票代碼查找股票持有"""
        try:
            data = await self.db[Collections.STOCKS].find_one({
                "user_id": user_id,
                "symbol": symbol
            })
            return UserStock.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Failed to find user stock by user and symbol: {e}")
            return None
    
    async def save(self, user_stock: UserStock) -> UserStock:
        """儲存使用者股票持有"""
        try:
            data = user_stock.to_dict()
            await self.db[Collections.STOCKS].replace_one(
                {
                    "user_id": user_stock.user_id,
                    "symbol": user_stock.symbol
                },
                data,
                upsert=True
            )
            return user_stock
        except Exception as e:
            logger.error(f"Failed to save user stock: {e}")
            raise
    
    async def update(self, user_stock: UserStock) -> bool:
        """更新使用者股票持有"""
        try:
            data = user_stock.to_dict()
            result = await self.db[Collections.STOCKS].replace_one(
                {
                    "user_id": user_stock.user_id,
                    "symbol": user_stock.symbol
                },
                data
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update user stock: {e}")
            return False
    
    async def delete(self, user_id: ObjectId, symbol: str) -> bool:
        """刪除使用者股票持有"""
        try:
            result = await self.db[Collections.STOCKS].delete_one({
                "user_id": user_id,
                "symbol": symbol
            })
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete user stock: {e}")
            return False
    
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[UserStock]:
        """查找所有使用者股票持有"""
        try:
            cursor = self.db[Collections.STOCKS].find().skip(skip).limit(limit)
            stocks = []
            async for data in cursor:
                stocks.append(UserStock.from_dict(data))
            return stocks
        except Exception as e:
            logger.error(f"Failed to find all user stocks: {e}")
            return []
    
    # Repository[UserStock] 抽象方法實現
    async def find_by_id(self, entity_id: ObjectId) -> Optional[UserStock]:
        """根據 ID 查找使用者股票持有"""
        try:
            data = await self.db[Collections.STOCKS].find_one({"_id": entity_id})
            return UserStock.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Failed to find user stock by ID: {e}")
            return None
    
    async def exists(self, entity_id: ObjectId) -> bool:
        """檢查使用者股票持有是否存在"""
        try:
            result = await self.db[Collections.STOCKS].find_one({"_id": entity_id}, {"_id": 1})
            return result is not None
        except Exception as e:
            logger.error(f"Failed to check user stock existence: {e}")
            return False
    
    async def count(self) -> int:
        """統計使用者股票持有數量"""
        try:
            return await self.db[Collections.STOCKS].count_documents({})
        except Exception as e:
            logger.error(f"Failed to count user stocks: {e}")
            return 0
    
    # SpecificationRepository[UserStock] 抽象方法實現
    async def find_by_specification(self, specification: Dict[str, Any]) -> List[UserStock]:
        """根據規格查找使用者股票持有"""
        try:
            cursor = self.db[Collections.STOCKS].find(specification)
            stocks = []
            async for data in cursor:
                stocks.append(UserStock.from_dict(data))
            return stocks
        except Exception as e:
            logger.error(f"Failed to find user stocks by specification: {e}")
            return []
    
    async def find_one_by_specification(self, specification: Dict[str, Any]) -> Optional[UserStock]:
        """根據規格查找單一使用者股票持有"""
        try:
            data = await self.db[Collections.STOCKS].find_one(specification)
            return UserStock.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Failed to find user stock by specification: {e}")
            return None
    
    async def count_by_specification(self, specification: Dict[str, Any]) -> int:
        """根據規格統計使用者股票持有數量"""
        try:
            return await self.db[Collections.STOCKS].count_documents(specification)
        except Exception as e:
            logger.error(f"Failed to count user stocks by specification: {e}")
            return 0


class MongoStudentRepository(StudentRepository):
    """MongoDB 學生儲存庫實現"""
    
    def __init__(self):
        self.db = get_database()
    
    async def find_by_id(self, student_id: ObjectId) -> Optional[Student]:
        """根據 ID 查找學生"""
        try:
            data = await self.db[Collections.STUDENTS].find_one({"_id": student_id})
            return Student.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Failed to find student by ID: {e}")
            return None
    
    async def find_by_student_id(self, student_id: str) -> Optional[Student]:
        """根據學生 ID 查找學生"""
        try:
            data = await self.db[Collections.STUDENTS].find_one({"student_id": student_id})
            return Student.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Failed to find student by student ID: {e}")
            return None
    
    async def find_by_telegram_id(self, telegram_id: int) -> Optional[Student]:
        """根據 Telegram ID 查找學生"""
        try:
            data = await self.db[Collections.STUDENTS].find_one({"telegram_id": telegram_id})
            return Student.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Failed to find student by telegram ID: {e}")
            return None
    
    async def find_by_group_id(self, group_id: str) -> List[Student]:
        """根據群組 ID 查找學生"""
        try:
            cursor = self.db[Collections.STUDENTS].find({"group_id": group_id})
            students = []
            async for data in cursor:
                students.append(Student.from_dict(data))
            return students
        except Exception as e:
            logger.error(f"Failed to find students by group ID: {e}")
            return []
    
    async def find_active_students(self, skip: int = 0, limit: int = 100) -> List[Student]:
        """查找活躍學生"""
        try:
            cursor = self.db[Collections.STUDENTS].find({"is_active": True}).skip(skip).limit(limit)
            students = []
            async for data in cursor:
                students.append(Student.from_dict(data))
            return students
        except Exception as e:
            logger.error(f"Failed to find active students: {e}")
            return []
    
    async def count_active_students(self) -> int:
        """計算活躍學生數量"""
        try:
            return await self.db[Collections.STUDENTS].count_documents({"is_active": True})
        except Exception as e:
            logger.error(f"Failed to count active students: {e}")
            return 0
    
    async def save(self, student: Student) -> Student:
        """儲存學生"""
        try:
            data = student.to_dict()
            if student.id is None:
                result = await self.db[Collections.STUDENTS].insert_one(data)
                student.id = result.inserted_id
            else:
                await self.db[Collections.STUDENTS].replace_one({"_id": student.id}, data)
            return student
        except Exception as e:
            logger.error(f"Failed to save student: {e}")
            raise
    
    async def update(self, student: Student) -> bool:
        """更新學生"""
        try:
            data = student.to_dict()
            result = await self.db[Collections.STUDENTS].replace_one({"_id": student.id}, data)
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update student: {e}")
            return False
    
    async def delete(self, student_id: ObjectId) -> bool:
        """刪除學生"""
        try:
            result = await self.db[Collections.STUDENTS].delete_one({"_id": student_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete student: {e}")
            return False
    
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Student]:
        """查找所有學生"""
        try:
            cursor = self.db[Collections.STUDENTS].find().skip(skip).limit(limit)
            students = []
            async for data in cursor:
                students.append(Student.from_dict(data))
            return students
        except Exception as e:
            logger.error(f"Failed to find all students: {e}")
            return []
    
    async def exists(self, student_id: ObjectId) -> bool:
        """檢查學生是否存在"""
        try:
            count = await self.db[Collections.STUDENTS].count_documents({"_id": student_id})
            return count > 0
        except Exception as e:
            logger.error(f"Failed to check student existence: {e}")
            return False
    
    async def count(self) -> int:
        """計算學生總數"""
        try:
            return await self.db[Collections.STUDENTS].count_documents({})
        except Exception as e:
            logger.error(f"Failed to count students: {e}")
            return 0
    
    async def find_by_specification(self, specification: Dict[str, Any]) -> List[Student]:
        """根據規格查找學生"""
        try:
            cursor = self.db[Collections.STUDENTS].find(specification)
            students = []
            async for data in cursor:
                students.append(Student.from_dict(data))
            return students
        except Exception as e:
            logger.error(f"Failed to find students by specification: {e}")
            return []
    
    async def find_one_by_specification(self, specification: Dict[str, Any]) -> Optional[Student]:
        """根據規格查找單一學生"""
        try:
            data = await self.db[Collections.STUDENTS].find_one(specification)
            return Student.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Failed to find student by specification: {e}")
            return None
    
    async def count_by_specification(self, specification: Dict[str, Any]) -> int:
        """根據規格計算學生數量"""
        try:
            return await self.db[Collections.STUDENTS].count_documents(specification)
        except Exception as e:
            logger.error(f"Failed to count students by specification: {e}")
            return 0


class MongoUserDebtRepository(UserDebtRepository):
    """MongoDB 使用者債務儲存庫實現"""
    
    def __init__(self):
        self.db = get_database()
    
    async def find_by_id(self, debt_id: ObjectId) -> Optional[UserDebt]:
        """根據 ID 查找債務"""
        try:
            data = await self.db[Collections.USER_DEBTS].find_one({"_id": debt_id})
            return UserDebt.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Failed to find debt by ID: {e}")
            return None
    
    async def save(self, debt: UserDebt) -> UserDebt:
        """儲存債務"""
        try:
            data = debt.to_dict()
            if debt.id is None:
                result = await self.db[Collections.USER_DEBTS].insert_one(data)
                debt.id = result.inserted_id
            else:
                await self.db[Collections.USER_DEBTS].replace_one({"_id": debt.id}, data)
            return debt
        except Exception as e:
            logger.error(f"Failed to save debt: {e}")
            raise
    
    async def update(self, debt: UserDebt) -> bool:
        """更新債務"""
        try:
            data = debt.to_dict()
            result = await self.db[Collections.USER_DEBTS].replace_one({"_id": debt.id}, data)
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update debt: {e}")
            return False
    
    async def delete(self, debt_id: ObjectId) -> bool:
        """刪除債務"""
        try:
            result = await self.db[Collections.USER_DEBTS].delete_one({"_id": debt_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete debt: {e}")
            return False
    
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[UserDebt]:
        """查找所有債務"""
        try:
            cursor = self.db[Collections.USER_DEBTS].find().skip(skip).limit(limit).sort("created_at", -1)
            debts = []
            async for data in cursor:
                debts.append(UserDebt.from_dict(data))
            return debts
        except Exception as e:
            logger.error(f"Failed to find all debts: {e}")
            return []
    
    async def exists(self, debt_id: ObjectId) -> bool:
        """檢查債務是否存在"""
        try:
            count = await self.db[Collections.USER_DEBTS].count_documents({"_id": debt_id})
            return count > 0
        except Exception as e:
            logger.error(f"Failed to check debt existence: {e}")
            return False
    
    async def count(self) -> int:
        """計算債務總數"""
        try:
            return await self.db[Collections.USER_DEBTS].count_documents({})
        except Exception as e:
            logger.error(f"Failed to count debts: {e}")
            return 0
    
    async def find_by_user_id(self, user_id: ObjectId) -> List[UserDebt]:
        """根據使用者 ID 查找債務"""
        try:
            cursor = self.db[Collections.USER_DEBTS].find({"user_id": user_id}).sort("created_at", -1)
            debts = []
            async for data in cursor:
                debts.append(UserDebt.from_dict(data))
            return debts
        except Exception as e:
            logger.error(f"Failed to find debts by user ID: {e}")
            return []
    
    async def find_active_debts(self, skip: int = 0, limit: int = 100) -> List[UserDebt]:
        """查找活躍債務"""
        try:
            cursor = self.db[Collections.USER_DEBTS].find({"status": "active"}).skip(skip).limit(limit).sort("created_at", -1)
            debts = []
            async for data in cursor:
                debts.append(UserDebt.from_dict(data))
            return debts
        except Exception as e:
            logger.error(f"Failed to find active debts: {e}")
            return []
    
    async def find_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[UserDebt]:
        """根據狀態查找債務"""
        try:
            cursor = self.db[Collections.USER_DEBTS].find({"status": status}).skip(skip).limit(limit).sort("created_at", -1)
            debts = []
            async for data in cursor:
                debts.append(UserDebt.from_dict(data))
            return debts
        except Exception as e:
            logger.error(f"Failed to find debts by status: {e}")
            return []
    
    # calculate_total_debt method moved to DebtDomainService
    # Business logic should not be in infrastructure layer
    
    async def mark_as_resolved(self, debt_id: ObjectId, resolved_by: ObjectId) -> bool:
        """標記債務為已解決"""
        try:
            result = await self.db[Collections.USER_DEBTS].update_one(
                {"_id": debt_id},
                {
                    "$set": {
                        "status": "resolved",
                        "resolved_by": resolved_by,
                        "resolved_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to mark debt as resolved: {e}")
            return False
    
    async def find_by_specification(self, specification: Dict[str, Any]) -> List[UserDebt]:
        """根據規格查找債務"""
        try:
            cursor = self.db[Collections.USER_DEBTS].find(specification)
            debts = []
            async for data in cursor:
                debts.append(UserDebt.from_dict(data))
            return debts
        except Exception as e:
            logger.error(f"Failed to find debts by specification: {e}")
            return []
    
    async def find_one_by_specification(self, specification: Dict[str, Any]) -> Optional[UserDebt]:
        """根據規格查找單一債務"""
        try:
            data = await self.db[Collections.USER_DEBTS].find_one(specification)
            return UserDebt.from_dict(data) if data else None
        except Exception as e:
            logger.error(f"Failed to find debt by specification: {e}")
            return None
    
    async def count_by_specification(self, specification: Dict[str, Any]) -> int:
        """根據規格計算債務數量"""
        try:
            return await self.db[Collections.USER_DEBTS].count_documents(specification)
        except Exception as e:
            logger.error(f"Failed to count debts by specification: {e}")
            return 0