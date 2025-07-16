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
import logging

logger = logging.getLogger(__name__)


class MongoUserRepository(UserRepository):
    """MongoDB 使用者存儲庫實現"""
    
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self.db = db or get_database()
    
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


class MongoPointLogRepository(PointLogRepository):
    """MongoDB 點數記錄存儲庫實現"""
    
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self.db = db or get_database()
    
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


class MongoStockRepository(StockRepository):
    """MongoDB 股票存儲庫實現"""
    
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self.db = db or get_database()
    
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
    
    async def delete(self, symbol: str) -> bool:
        """刪除股票"""
        try:
            result = await self.db[Collections.STOCK_CONFIG].delete_one({"symbol": symbol})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete stock: {e}")
            return False


class MongoOrderRepository(OrderRepository):
    """MongoDB 訂單存儲庫實現"""
    
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self.db = db or get_database()
    
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
    
    async def update(self, order: StockOrder) -> bool:
        """更新訂單"""
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


class MongoUserStockRepository(UserStockRepository):
    """MongoDB 使用者股票持有存儲庫實現"""
    
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self.db = db or get_database()
    
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