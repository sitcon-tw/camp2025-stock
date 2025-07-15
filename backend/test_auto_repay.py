#!/usr/bin/env python3
"""
測試自動償還欠款機制
"""

import asyncio
import sys
import os
from bson import ObjectId

# 添加 app 目錄到路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import connect_to_mongo, get_database, Collections
from app.services.admin_service import AdminService
from app.schemas.public import GivePointsRequest

async def test_auto_repay():
    """測試自動償還欠款機制"""
    print("🧪 測試自動償還欠款機制...")
    
    # 初始化資料庫連接
    await connect_to_mongo()
    db = get_database()
    admin_service = AdminService(db)
    
    # 測試使用者 - 萬宸星
    test_user_id = "686cd6bacfd2989c617b59ee"
    
    try:
        user_oid = ObjectId(test_user_id)
        
        # 檢查使用者目前狀態
        print("\n📊 使用者目前狀態:")
        user = await db[Collections.USERS].find_one({'_id': user_oid})
        print(f"姓名: {user.get('name')}")
        print(f"點數: {user.get('points', 0)}")
        print(f"欠款: {user.get('owed_points', 0)}")
        print(f"凍結: {user.get('frozen', False)}")
        
        # 測試給予 10 點（應該自動償還欠款）
        print("\n💰 測試給予 10 點...")
        request = GivePointsRequest(
            type="user",
            username=user.get('name'),  # 使用姓名
            amount=10
        )
        
        result = await admin_service.give_points(request)
        print(f"給予點數結果: {result}")
        
        # 檢查更新後的狀態
        print("\n📊 更新後的使用者狀態:")
        user_after = await db[Collections.USERS].find_one({'_id': user_oid})
        print(f"姓名: {user_after.get('name')}")
        print(f"點數: {user_after.get('points', 0)}")
        print(f"欠款: {user_after.get('owed_points', 0)}")
        print(f"凍結: {user_after.get('frozen', False)}")
        print(f"實際可用餘額: {user_after.get('points', 0) - user_after.get('owed_points', 0)}")
        
        # 計算變化
        points_change = user_after.get('points', 0) - user.get('points', 0)
        debt_change = user.get('owed_points', 0) - user_after.get('owed_points', 0)
        
        print(f"\n📈 變化摘要:")
        print(f"點數變化: +{points_change}")
        print(f"欠款減少: {debt_change}")
        print(f"用於償還: {debt_change} 點")
        print(f"剩餘增加: {points_change} 點")
        
        # 驗證邏輯
        if debt_change + points_change == 10:
            print("✅ 自動償還邏輯正確！")
        else:
            print("❌ 自動償還邏輯有問題！")
            
        print("\n✅ 測試完成！")
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_auto_repay())