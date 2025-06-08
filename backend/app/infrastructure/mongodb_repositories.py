# MongoDB Repository 實作
# DIP 原則：實作領域層定義的抽象介面
# SRP 原則：每個 Repository 專注於特定實體的資料存取

from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.domain.entities import User, Stock, StockOrder, Transfer
from app.domain.repositories import (
    UserRepository, StockRepository, StockOrderRepository, 
    TransferRepository, MarketConfigRepository
)
from app.core.database import Collections
import logging

logger = logging.getLogger(__name__)


class MongoUserRepository(UserRepository):
    """
    MongoDB 使用者資料存取實作
    DIP 原則：實作抽象介面，提供具體的 MongoDB 實作
    SRP 原則：專注於使用者資料的 MongoDB 操作
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[Collections.USERS]
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """根據用戶名獲取使用者"""
        try:
            doc = await self.collection.find_one({"username": username})
            return self._document_to_entity(doc) if doc else None
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            return None
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """根據ID獲取使用者"""
        try:
            doc = await self.collection.find_one({"id": user_id})
            return self._document_to_entity(doc) if doc else None
        except Exception as e:
            logger.error(f"Error getting user by id {user_id}: {e}")
            return None
    
    async def save(self, user: User) -> None:
        """保存使用者"""
        try:
            doc = self._entity_to_document(user)
            await self.collection.update_one(
                {"id": user.user_id},
                {"$set": doc},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error saving user {user.user_id}: {e}")
            raise
    
    async def create(self, user: User) -> str:
        """創建新使用者，返回 user_id"""
        try:
            doc = self._entity_to_document(user)
            await self.collection.insert_one(doc)
            return user.user_id
        except Exception as e:
            logger.error(f"Error creating user {user.username}: {e}")
            raise
    
    async def update_points(self, user_id: str, new_points: int) -> None:
        """更新使用者點數"""
        try:
            await self.collection.update_one(
                {"id": user_id},
                {"$set": {"points": new_points, "updated_at": datetime.now()}}
            )
        except Exception as e:
            logger.error(f"Error updating points for user {user_id}: {e}")
            raise
    
    def _document_to_entity(self, doc: dict) -> User:
        """將 MongoDB 文件轉換為領域實體"""
        return User(
            user_id=doc.get("id"),
            username=doc.get("username"),
            email=doc.get("email"),
            team=doc.get("team"),
            points=doc.get("points", 0),
            telegram_id=doc.get("telegram_id"),
            is_active=doc.get("is_active", True),
            created_at=doc.get("created_at")
        )
    
    def _entity_to_document(self, user: User) -> dict:
        """將領域實體轉換為 MongoDB 文件"""
        return {
            "id": user.user_id,
            "username": user.username,
            "email": user.email,
            "team": user.team,
            "points": user.points,
            "telegram_id": user.telegram_id,
            "is_active": user.is_active,
            "created_at": user.created_at or datetime.now(),
            "updated_at": datetime.now()
        }


class MongoStockRepository(StockRepository):
    """
    MongoDB 股票資料存取實作
    SRP 原則：專注於股票資料的 MongoDB 操作
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[Collections.STOCKS]
    
    async def get_by_user_id(self, user_id: str) -> Optional[Stock]:
        """獲取使用者股票持倉"""
        try:
            doc = await self.collection.find_one({"user_id": user_id})
            return self._document_to_entity(doc) if doc else None
        except Exception as e:
            logger.error(f"Error getting stock for user {user_id}: {e}")
            return None
    
    async def save(self, stock: Stock) -> None:
        """保存股票持倉"""
        try:
            doc = self._entity_to_document(stock)
            await self.collection.update_one(
                {"user_id": stock.user_id},
                {"$set": doc},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error saving stock for user {stock.user_id}: {e}")
            raise
    
    async def update_quantity(self, user_id: str, new_quantity: int, new_avg_cost: float) -> None:
        """更新股票數量和平均成本"""
        try:
            await self.collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "quantity": new_quantity,
                        "avg_cost": new_avg_cost,
                        "updated_at": datetime.now()
                    }
                },
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error updating stock quantity for user {user_id}: {e}")
            raise
    
    def _document_to_entity(self, doc: dict) -> Stock:
        """將 MongoDB 文件轉換為領域實體"""
        return Stock(
            user_id=doc.get("user_id"),
            quantity=doc.get("quantity", 0),
            avg_cost=Decimal(str(doc.get("avg_cost", 0))),
            updated_at=doc.get("updated_at")
        )
    
    def _entity_to_document(self, stock: Stock) -> dict:
        """將領域實體轉換為 MongoDB 文件"""
        return {
            "user_id": stock.user_id,
            "quantity": stock.quantity,
            "avg_cost": float(stock.avg_cost),
            "updated_at": stock.updated_at or datetime.now()
        }


class MongoStockOrderRepository(StockOrderRepository):
    """
    MongoDB 股票訂單資料存取實作
    SRP 原則：專注於訂單資料的 MongoDB 操作
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[Collections.STOCK_ORDERS]
    
    async def create(self, order: StockOrder) -> str:
        """創建新訂單"""
        try:
            doc = self._entity_to_document(order)
            await self.collection.insert_one(doc)
            return order.order_id
        except Exception as e:
            logger.error(f"Error creating order {order.order_id}: {e}")
            raise
    
    async def get_by_id(self, order_id: str) -> Optional[StockOrder]:
        """根據ID獲取訂單"""
        try:
            doc = await self.collection.find_one({"order_id": order_id})
            return self._document_to_entity(doc) if doc else None
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return None
    
    async def get_by_user_id(self, user_id: str, limit: int = 20) -> List[StockOrder]:
        """獲取使用者訂單歷史"""
        try:
            cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
            docs = await cursor.to_list(length=limit)
            return [self._document_to_entity(doc) for doc in docs]
        except Exception as e:
            logger.error(f"Error getting orders for user {user_id}: {e}")
            return []
    
    async def get_pending_orders(self) -> List[StockOrder]:
        """獲取所有待處理訂單"""
        try:
            cursor = self.collection.find({"status": "pending"}).sort("created_at", 1)
            docs = await cursor.to_list(length=None)
            return [self._document_to_entity(doc) for doc in docs]
        except Exception as e:
            logger.error(f"Error getting pending orders: {e}")
            return []
    
    async def update_status(self, order_id: str, status: str, executed_price: Optional[float] = None) -> None:
        """更新訂單狀態"""
        try:
            update_doc = {"status": status, "updated_at": datetime.now()}
            if executed_price:
                update_doc["executed_price"] = executed_price
                update_doc["executed_at"] = datetime.now()
            
            await self.collection.update_one(
                {"order_id": order_id},
                {"$set": update_doc}
            )
        except Exception as e:
            logger.error(f"Error updating order status {order_id}: {e}")
            raise
    
    def _document_to_entity(self, doc: dict) -> StockOrder:
        """將 MongoDB 文件轉換為領域實體"""
        price = None
        if doc.get("price"):
            price = Decimal(str(doc.get("price")))
        
        return StockOrder(
            order_id=doc.get("order_id"),
            user_id=doc.get("user_id"),
            order_type=doc.get("order_type"),
            side=doc.get("side"),
            quantity=doc.get("quantity"),
            price=price,
            status=doc.get("status", "pending"),
            created_at=doc.get("created_at"),
            executed_at=doc.get("executed_at")
        )
    
    def _entity_to_document(self, order: StockOrder) -> dict:
        """將領域實體轉換為 MongoDB 文件"""
        doc = {
            "order_id": order.order_id,
            "user_id": order.user_id,
            "order_type": order.order_type,
            "side": order.side,
            "quantity": order.quantity,
            "status": order.status,
            "created_at": order.created_at or datetime.now()
        }
        
        if order.price:
            doc["price"] = float(order.price)
        if order.executed_at:
            doc["executed_at"] = order.executed_at
        
        return doc


class MongoTransferRepository(TransferRepository):
    """
    MongoDB 轉帳資料存取實作
    SRP 原則：專注於轉帳資料的 MongoDB 操作
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[Collections.POINT_LOGS]  # 使用 point_logs 集合
    
    async def create(self, transfer: Transfer) -> str:
        """創建轉帳記錄"""
        try:
            doc = self._entity_to_document(transfer)
            await self.collection.insert_one(doc)
            return transfer.transfer_id
        except Exception as e:
            logger.error(f"Error creating transfer {transfer.transfer_id}: {e}")
            raise
    
    async def get_by_id(self, transfer_id: str) -> Optional[Transfer]:
        """根據ID獲取轉帳記錄"""
        try:
            doc = await self.collection.find_one({"transfer_id": transfer_id})
            return self._document_to_entity(doc) if doc else None
        except Exception as e:
            logger.error(f"Error getting transfer {transfer_id}: {e}")
            return None
    
    async def get_by_user_id(self, user_id: str, limit: int = 20) -> List[Transfer]:
        """獲取使用者轉帳歷史"""
        try:
            cursor = self.collection.find({
                "$or": [{"from_user_id": user_id}, {"to_user_id": user_id}],
                "type": "transfer"
            }).sort("created_at", -1).limit(limit)
            docs = await cursor.to_list(length=limit)
            return [self._document_to_entity(doc) for doc in docs]
        except Exception as e:
            logger.error(f"Error getting transfers for user {user_id}: {e}")
            return []
    
    def _document_to_entity(self, doc: dict) -> Transfer:
        """將 MongoDB 文件轉換為領域實體"""
        return Transfer(
            transfer_id=doc.get("transfer_id"),
            from_user_id=doc.get("from_user_id"),
            to_user_id=doc.get("to_user_id"),
            amount=doc.get("amount"),
            fee=doc.get("fee", 0),
            note=doc.get("note"),
            status=doc.get("status", "pending"),
            created_at=doc.get("created_at")
        )
    
    def _entity_to_document(self, transfer: Transfer) -> dict:
        """將領域實體轉換為 MongoDB 文件"""
        return {
            "transfer_id": transfer.transfer_id,
            "type": "transfer",
            "from_user_id": transfer.from_user_id,
            "to_user_id": transfer.to_user_id,
            "amount": transfer.amount,
            "fee": transfer.fee,
            "note": transfer.note,
            "status": transfer.status,
            "created_at": transfer.created_at or datetime.now()
        }


class MongoMarketConfigRepository(MarketConfigRepository):
    """
    MongoDB 市場設定資料存取實作
    SRP 原則：專注於市場設定資料的 MongoDB 操作
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[Collections.MARKET_CONFIG]
    
    async def get_ipo_config(self) -> Optional[dict]:
        """獲取 IPO 設定"""
        try:
            return await self.collection.find_one({"type": "ipo_status"})
        except Exception as e:
            logger.error(f"Error getting IPO config: {e}")
            return None
    
    async def update_ipo_config(self, config: dict) -> None:
        """更新 IPO 設定"""
        try:
            await self.collection.update_one(
                {"type": "ipo_status"},
                {"$set": config},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error updating IPO config: {e}")
            raise
    
    async def get_market_price(self) -> Optional[float]:
        """獲取當前市場價格"""
        try:
            config = await self.collection.find_one({"type": "market_price"})
            return config.get("price") if config else None
        except Exception as e:
            logger.error(f"Error getting market price: {e}")
            return None