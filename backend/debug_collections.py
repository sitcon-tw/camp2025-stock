#!/usr/bin/env python3
"""
資料庫集合結構查詢腳本
用於檢查 point_logs 和 users 集合的實際資料結構
"""

import asyncio
import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import json

# 添加 app 路徑以便導入配置
sys.path.append('/Users/doeshing/Documents/Github/camp2025-stock/backend')

async def connect_to_database():
    """連接到資料庫"""
    # 使用預設的 MongoDB 連接
    mongo_uri = "mongodb://localhost:27017"
    database_name = "sitcon_camp_2025"
    
    try:
        client = AsyncIOMotorClient(mongo_uri)
        database = client[database_name]
        
        # 測試連線
        await client.admin.command('ismaster')
        print(f"✅ 成功連接到 MongoDB 資料庫: {database_name}")
        return client, database
        
    except Exception as e:
        print(f"❌ 無法連接到 MongoDB: {e}")
        return None, None

async def examine_users_collection(database):
    """檢查 users 集合的資料結構"""
    print("\n" + "="*50)
    print("📊 檢查 users 集合")
    print("="*50)
    
    try:
        users_collection = database["users"]
        
        # 統計資料
        count = await users_collection.count_documents({})
        print(f"📈 總使用者數: {count}")
        
        if count == 0:
            print("⚠️ users 集合為空")
            return
        
        # 取得前3筆資料查看結構
        print("\n📋 使用者資料結構範例:")
        async for user in users_collection.find({}).limit(3):
            print(f"\n使用者文件:")
            for key, value in user.items():
                if key == "_id":
                    print(f"  _id: {value} (type: {type(value).__name__})")
                elif key == "id":
                    print(f"  id: {value} (type: {type(value).__name__})")
                else:
                    print(f"  {key}: {value}")
            print("-" * 30)
        
        # 檢查 id 欄位的唯一性和格式
        print("\n🔍 檢查 id 欄位:")
        unique_ids = await users_collection.distinct("id")
        print(f"  不重複的 id 數量: {len(unique_ids)}")
        print(f"  前5個 id 值: {unique_ids[:5]}")
        
        # 檢查是否有 _id 欄位
        pipeline = [
            {"$project": {"_id": 1, "id": 1}},
            {"$limit": 3}
        ]
        print("\n🔍 _id 與 id 欄位對照:")
        async for doc in users_collection.aggregate(pipeline):
            print(f"  _id: {doc['_id']} -> id: {doc.get('id', 'N/A')}")
            
    except Exception as e:
        print(f"❌ 檢查 users 集合時發生錯誤: {e}")

async def examine_point_logs_collection(database):
    """檢查 point_logs 集合的資料結構"""
    print("\n" + "="*50)
    print("📊 檢查 point_logs 集合")
    print("="*50)
    
    try:
        point_logs_collection = database["point_logs"]
        
        # 統計資料
        count = await point_logs_collection.count_documents({})
        print(f"📈 總點數記錄數: {count}")
        
        if count == 0:
            print("⚠️ point_logs 集合為空")
            return
        
        # 取得前3筆資料查看結構
        print("\n📋 點數記錄資料結構範例:")
        async for log in point_logs_collection.find({}).limit(3):
            print(f"\n點數記錄文件:")
            for key, value in log.items():
                if key == "_id":
                    print(f"  _id: {value} (type: {type(value).__name__})")
                elif key == "user_id":
                    print(f"  user_id: {value} (type: {type(value).__name__})")
                elif key == "created_at":
                    print(f"  created_at: {value} (type: {type(value).__name__})")
                else:
                    print(f"  {key}: {value}")
            print("-" * 30)
        
        # 檢查 user_id 欄位的值類型和分佈
        print("\n🔍 檢查 user_id 欄位:")
        unique_user_ids = await point_logs_collection.distinct("user_id")
        print(f"  不重複的 user_id 數量: {len(unique_user_ids)}")
        print(f"  前5個 user_id 值: {unique_user_ids[:5]}")
        
        # 分析 user_id 的類型
        pipeline = [
            {"$group": {"_id": {"$type": "$user_id"}, "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        print("\n📊 user_id 欄位類型分佈:")
        async for result in point_logs_collection.aggregate(pipeline):
            print(f"  類型 '{result['_id']}': {result['count']} 筆記錄")
            
    except Exception as e:
        print(f"❌ 檢查 point_logs 集合時發生錯誤: {e}")

async def check_user_id_relationship(database):
    """檢查 users.id 與 point_logs.user_id 之間的關聯"""
    print("\n" + "="*50)
    print("🔗 檢查 users.id 與 point_logs.user_id 關聯")
    print("="*50)
    
    try:
        users_collection = database["users"]
        point_logs_collection = database["point_logs"]
        
        # 取得所有使用者的 id
        user_ids = await users_collection.distinct("id")
        print(f"📈 users 集合中的 id 數量: {len(user_ids)}")
        
        # 取得所有點數記錄的 user_id
        log_user_ids = await point_logs_collection.distinct("user_id")
        print(f"📈 point_logs 集合中的 user_id 數量: {len(log_user_ids)}")
        
        # 找出在 point_logs 中但不在 users 中的 user_id
        orphaned_logs = set(log_user_ids) - set(user_ids)
        if orphaned_logs:
            print(f"⚠️ 孤立的點數記錄 (在 point_logs 但不在 users): {len(orphaned_logs)} 個")
            print(f"   前5個孤立的 user_id: {list(orphaned_logs)[:5]}")
        else:
            print("✅ 所有 point_logs 的 user_id 都在 users 集合中找得到")
        
        # 找出有點數記錄的使用者
        users_with_logs = set(user_ids) & set(log_user_ids)
        print(f"📊 有點數記錄的使用者: {len(users_with_logs)} 個")
        
        # 檢查一些具體的關聯範例
        print("\n🔍 關聯範例檢查:")
        sample_user_ids = list(users_with_logs)[:3]
        for user_id in sample_user_ids:
            # 查詢該使用者在 users 集合中的資料
            user_doc = await users_collection.find_one({"id": user_id})
            if user_doc:
                print(f"\n  使用者 ID: {user_id}")
                print(f"    users 集合中的名稱: {user_doc.get('name', 'N/A')}")
                
                # 查詢該使用者的點數記錄數量
                log_count = await point_logs_collection.count_documents({"user_id": user_id})
                print(f"    點數記錄數量: {log_count}")
                
                # 顯示最新的一筆點數記錄
                latest_log = await point_logs_collection.find_one(
                    {"user_id": user_id}, 
                    sort=[("created_at", -1)]
                )
                if latest_log:
                    print(f"    最新記錄: {latest_log.get('action', 'N/A')} {latest_log.get('amount', 'N/A')} 點")
                    print(f"    記錄時間: {latest_log.get('created_at', 'N/A')}")
            
    except Exception as e:
        print(f"❌ 檢查關聯時發生錯誤: {e}")

async def main():
    """主函數"""
    print("🔍 SITCON Camp 2025 - 資料庫集合結構檢查")
    print("目的: 確認 point_logs 和 users 集合的資料結構及關聯")
    
    # 連接資料庫
    client, database = await connect_to_database()
    if not database:
        return
    
    try:
        # 檢查集合是否存在
        collections = await database.list_collection_names()
        print(f"\n📋 資料庫中的集合: {collections}")
        
        if "users" not in collections:
            print("❌ users 集合不存在")
            return
        
        if "point_logs" not in collections:
            print("❌ point_logs 集合不存在")
            return
        
        # 依序檢查各集合
        await examine_users_collection(database)
        await examine_point_logs_collection(database)
        await check_user_id_relationship(database)
        
        print("\n" + "="*50)
        print("🎯 檢查完成！")
        print("="*50)
        print("現在你可以根據以上資訊確認:")
        print("1. users 集合中 id 欄位的格式")
        print("2. point_logs 集合中 user_id 欄位的格式")
        print("3. 兩者之間的關聯是否正確")
        
    except Exception as e:
        print(f"❌ 執行過程中發生錯誤: {e}")
    finally:
        if client:
            client.close()
            print("\n🔚 資料庫連線已關閉")

if __name__ == "__main__":
    asyncio.run(main())