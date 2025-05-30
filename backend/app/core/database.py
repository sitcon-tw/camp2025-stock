from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None

db = Database()

# 連線到 MongoDB
async def connect_to_mongo():
    try:
        logger.info(f"Trying Connecting to MongoDB at: {settings.MONGO_URI}")
        db.client = AsyncIOMotorClient(settings.MONGO_URI)
        db.database = db.client[settings.DATABASE_NAME]
        
        # 測試連線
        await db.client.admin.command('ismaster')
        logger.info(f"Successfully connected to MongoDB database: {settings.DATABASE_NAME}")
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

# 關閉 MongoDB 連線
async def close_mongo_connection():
    try:
        if db.client:
            db.client.close()
            logger.info("MongoDB connection closed")
    except Exception as e:
        logger.error(f"Failed to close MongoDB connection: {e}")


# 取得資料庫 instance
def get_database() -> AsyncIOMotorDatabase:
    if db.database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return db.database


# 取得資料庫名稱
def get_database_name() -> str:
    return settings.DATABASE_NAME


# 集合名稱常數
class Collections:
    USERS = "users"
    GROUPS = "groups"
    POINT_LOGS = "point_logs"
    STOCKS = "stocks"
    STOCK_ORDERS = "stock_orders"
    ANNOUNCEMENTS = "announcements"
    MARKET_CONFIG = "market_config"
    
    @classmethod
    def all_collections(cls) -> list:
        # 取得所有集合名稱
        return [
            cls.USERS, cls.GROUPS, cls.POINT_LOGS,
            cls.STOCKS, cls.STOCK_ORDERS, cls.ANNOUNCEMENTS,
            cls.MARKET_CONFIG
        ]


# 初始化資料庫索引
async def init_database_indexes():
    try:
        database = get_database()
        
        # users
        await database[Collections.USERS].create_index("username", unique=True)
        await database[Collections.USERS].create_index("group_id")
        
        # point_logs
        await database[Collections.POINT_LOGS].create_index("user_id")
        await database[Collections.POINT_LOGS].create_index("created_at")
        
        # stocks
        await database[Collections.STOCKS].create_index("user_id", unique=True)
        
        # stock_orders
        await database[Collections.STOCK_ORDERS].create_index("user_id")
        await database[Collections.STOCK_ORDERS].create_index("created_at")
        await database[Collections.STOCK_ORDERS].create_index("status")
        
        # announcements
        await database[Collections.ANNOUNCEMENTS].create_index("created_at")
        
        # market_config
        await database[Collections.MARKET_CONFIG].create_index("type", unique=True)
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create database indexes: {e}")
