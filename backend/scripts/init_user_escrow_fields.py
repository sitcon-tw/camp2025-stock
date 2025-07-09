#!/usr/bin/env python3
"""
初始化用戶圈存欄位腳本
為所有現有用戶添加 escrow_amount 欄位，預設值為 0
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config_refactored import config
from app.core.database import Collections

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_user_escrow_fields():
    """為所有用戶初始化圈存欄位"""
    try:
        # 連接到 MongoDB
        client = AsyncIOMotorClient(config.database.mongo_uri)
        db = client[config.database.database_name]
        
        # 測試連接
        await client.admin.command('ismaster')
        logger.info(f"Successfully connected to MongoDB database: {config.database.database_name}")
        
        # 為所有用戶添加 escrow_amount 欄位
        result = await db[Collections.USERS].update_many(
            {"escrow_amount": {"$exists": False}},  # 只更新沒有此欄位的用戶
            {"$set": {"escrow_amount": 0}}
        )
        
        logger.info(f"Updated {result.modified_count} users with escrow_amount field")
        
        # 驗證更新結果
        total_users = await db[Collections.USERS].count_documents({})
        users_with_escrow = await db[Collections.USERS].count_documents({"escrow_amount": {"$exists": True}})
        
        logger.info(f"Total users: {total_users}")
        logger.info(f"Users with escrow_amount field: {users_with_escrow}")
        
        if users_with_escrow == total_users:
            logger.info("✅ All users now have escrow_amount field initialized")
        else:
            logger.warning(f"⚠️ Some users still missing escrow_amount field: {total_users - users_with_escrow}")
        
        # 關閉連接
        client.close()
        
    except Exception as e:
        logger.error(f"Failed to initialize user escrow fields: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(init_user_escrow_fields())