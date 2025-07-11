from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config_refactored import config
import logging

# 設定 pymongo 日誌等級為 WARNING 以減少 heartbeat 輸出
logging.getLogger("pymongo.topology").setLevel(logging.WARNING)
logging.getLogger("pymongo.connection").setLevel(logging.WARNING)
logging.getLogger("pymongo.heartbeat").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None

db = Database()

# 連線到 MongoDB
async def connect_to_mongo():
    try:
        logger.info(f"Trying Connecting to MongoDB at: {config.database.mongo_uri}")
        db.client = AsyncIOMotorClient(config.database.mongo_uri)
        db.database = db.client[config.database.database_name]
        
        # 測試連線
        await db.client.admin.command('ismaster')
        logger.info(f"Successfully connected to MongoDB database: {config.database.database_name}")
        
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
def get_CAMP_DATABASE_NAME() -> str:
    return config.database.database_name


# 集合名稱常數
class Collections:
    USERS = "users"
    GROUPS = "groups"
    POINT_LOGS = "point_logs"
    STOCKS = "stocks"
    STOCK_ORDERS = "stock_orders"
    TRADES = "trades"
    ANNOUNCEMENTS = "announcements"
    MARKET_CONFIG = "market_config"
    PVP_CHALLENGES = "pvp_challenges"
    QR_CODES = "qr_codes"
    PENDING_NOTIFICATIONS = "pending_notifications"
    
    @classmethod
    def all_collections(cls) -> list:
        # 取得所有集合名稱
        return [
            cls.USERS, cls.GROUPS, cls.POINT_LOGS,
            cls.STOCKS, cls.STOCK_ORDERS, cls.TRADES,
            cls.ANNOUNCEMENTS, cls.MARKET_CONFIG, cls.PVP_CHALLENGES,
            cls.QR_CODES, cls.PENDING_NOTIFICATIONS
        ]


# 初始化資料庫索引
async def init_database_indexes():
    try:
        database = get_database()
        
        # users - 新的id-based系統
        await database[Collections.USERS].create_index("id", unique=True)  # 永久ID索引
        await database[Collections.USERS].create_index("name")  # 使用者名稱索引（非唯一）
        await database[Collections.USERS].create_index("team")  # 隊伍索引
        await database[Collections.USERS].create_index("enabled")  # 啟用狀態索引
        
        # point_logs
        await database[Collections.POINT_LOGS].create_index("user_id")
        await database[Collections.POINT_LOGS].create_index("created_at")
        
        # stocks
        await database[Collections.STOCKS].create_index("user_id", unique=True)
        
        # stock_orders
        await database[Collections.STOCK_ORDERS].create_index("user_id")
        await database[Collections.STOCK_ORDERS].create_index("created_at")
        await database[Collections.STOCK_ORDERS].create_index("status")
        
        # trades
        await database[Collections.TRADES].create_index("buy_user_id")
        await database[Collections.TRADES].create_index("sell_user_id")
        await database[Collections.TRADES].create_index("created_at")
        await database[Collections.TRADES].create_index("price")
        
        # announcements
        await database[Collections.ANNOUNCEMENTS].create_index("created_at")
        
        # market_config
        await database[Collections.MARKET_CONFIG].create_index("type", unique=True)
        
        # pending_notifications
        await database[Collections.PENDING_NOTIFICATIONS].create_index("user_id")
        await database[Collections.PENDING_NOTIFICATIONS].create_index("created_at")
        await database[Collections.PENDING_NOTIFICATIONS].create_index("notification_type")
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create database indexes: {e}")
