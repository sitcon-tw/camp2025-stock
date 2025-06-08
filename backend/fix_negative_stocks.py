#!/usr/bin/env python3
"""
修復負股票持有量的腳本
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 從環境變數或使用預設值
MONGO_URI = os.getenv("CAMP_MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("CAMP_DATABASE_NAME", "sitcon_camp_2025")

async def fix_negative_stocks():
    """修復負股票持有量"""
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DATABASE_NAME]
    
    try:
        # 查找所有負股票持有量的記錄
        negative_stocks_cursor = db.stocks.find({"stock_amount": {"$lt": 0}})
        negative_stocks = await negative_stocks_cursor.to_list(length=None)
        
        logger.info(f"找到 {len(negative_stocks)} 個負股票持有記錄")
        
        if not negative_stocks:
            logger.info("沒有發現負股票持有量，無需修復")
            return
        
        # 顯示負股票詳情
        for stock in negative_stocks:
            user_id = stock.get("user_id")
            amount = stock.get("stock_amount", 0)
            
            # 獲取使用者訊息
            user = await db.users.find_one({"_id": user_id})
            username = user.get("name", "Unknown") if user else "Unknown"
            
            logger.info(f"使用者 {username} (ID: {user_id}) 持有 {amount} 股")
        
        # 詢問是否要修復
        print("\n選擇修復方式:")
        print("1. 將所有負股票設為 0")
        print("2. 取消所有相關使用者的待成交賣單，然後將負股票設為 0") 
        print("3. 僅顯示問題，不修復")
        print("4. 退出")
        
        choice = input("請選擇 (1-4): ").strip()
        
        if choice == "1":
            # 將負股票設為 0
            result = await db.stocks.update_many(
                {"stock_amount": {"$lt": 0}},
                {"$set": {"stock_amount": 0}}
            )
            logger.info(f"已修復 {result.modified_count} 個負股票記錄，全部設為 0 股")
            
        elif choice == "2":
            # 取消相關使用者的待成交賣單，然後將負股票設為 0
            negative_user_ids = [stock["user_id"] for stock in negative_stocks]
            
            # 取消這些使用者的待成交賣單
            cancel_result = await db.stock_orders.update_many(
                {
                    "user_id": {"$in": negative_user_ids},
                    "side": "sell",
                    "status": "pending"
                },
                {
                    "$set": {
                        "status": "cancelled",
                        "cancelled_at": datetime.now(timezone.utc),
                        "cancel_reason": "系統修復：負股票持有量"
                    }
                }
            )
            logger.info(f"已取消 {cancel_result.modified_count} 個待成交賣單")
            
            # 將負股票設為 0
            fix_result = await db.stocks.update_many(
                {"stock_amount": {"$lt": 0}},
                {"$set": {"stock_amount": 0}}
            )
            logger.info(f"已修復 {fix_result.modified_count} 個負股票記錄，全部設為 0 股")
            
        elif choice == "3":
            logger.info("僅顯示問題，未進行修復")
            
        elif choice == "4":
            logger.info("退出修復程序")
            return
            
        else:
            logger.error("無效選擇")
            return
            
        # 驗證修復結果
        remaining_negative = await db.stocks.count_documents({"stock_amount": {"$lt": 0}})
        if remaining_negative == 0:
            logger.info("✅ 修復完成，所有負股票問題已解決")
        else:
            logger.warning(f"⚠️ 仍有 {remaining_negative} 個負股票記錄")
            
    except Exception as e:
        logger.error(f"修復過程中發生錯誤: {e}")
    finally:
        client.close()

async def show_stock_summary():
    """顯示股票持有摘要"""
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DATABASE_NAME]
    
    try:
        # 統計股票持有情況
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_users": {"$sum": 1},
                    "positive_stocks": {
                        "$sum": {
                            "$cond": [{"$gt": ["$stock_amount", 0]}, 1, 0]
                        }
                    },
                    "zero_stocks": {
                        "$sum": {
                            "$cond": [{"$eq": ["$stock_amount", 0]}, 1, 0]
                        }
                    },
                    "negative_stocks": {
                        "$sum": {
                            "$cond": [{"$lt": ["$stock_amount", 0]}, 1, 0]
                        }
                    },
                    "total_stock_amount": {"$sum": "$stock_amount"},
                    "min_stock": {"$min": "$stock_amount"},
                    "max_stock": {"$max": "$stock_amount"}
                }
            }
        ]
        
        result = await db.stocks.aggregate(pipeline).to_list(1)
        
        if result:
            stats = result[0]
            logger.info("=== 股票持有摘要 ===")
            logger.info(f"總使用者數: {stats['total_users']}")
            logger.info(f"正股票使用者: {stats['positive_stocks']}")
            logger.info(f"零股票使用者: {stats['zero_stocks']}")
            logger.info(f"負股票使用者: {stats['negative_stocks']}")
            logger.info(f"總股票數量: {stats['total_stock_amount']}")
            logger.info(f"最小持股: {stats['min_stock']}")
            logger.info(f"最大持股: {stats['max_stock']}")
        else:
            logger.info("沒有找到股票持有記錄")
            
    except Exception as e:
        logger.error(f"查詢過程中發生錯誤: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        asyncio.run(show_stock_summary())
    else:
        asyncio.run(fix_negative_stocks())