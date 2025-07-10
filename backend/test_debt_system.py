#!/usr/bin/env python3
"""
測試債務管理系統
"""

import asyncio
import sys
import os
from bson import ObjectId

# 添加 app 目錄到路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import get_database, Collections, connect_to_mongo
from app.services.debt_service import DebtService
from app.services.user_service import UserService
from app.core.user_validation import UserValidationService

async def test_debt_system():
    """測試債務管理系統的基本功能"""
    print("🧪 開始測試債務管理系統...")
    
    # 初始化資料庫連接
    await connect_to_mongo()
    db = get_database()
    debt_service = DebtService(db)
    user_service = UserService(db)
    validation_service = UserValidationService(db)
    
    # 測試用戶 - 使用你提供的欠款用戶資料
    test_user_id = "686cd6bacfd2989c617b59ee"
    
    try:
        user_oid = ObjectId(test_user_id)
        
        print(f"\n📊 測試用戶 ID: {test_user_id}")
        
        # 1. 測試獲取用戶債務信息
        print("\n1️⃣ 測試獲取用戶債務信息...")
        debt_info = await debt_service.get_user_debt_info(user_oid)
        print(f"債務信息: {debt_info}")
        
        # 2. 測試用戶狀態驗證
        print("\n2️⃣ 測試用戶狀態驗證...")
        status_result = await validation_service.validate_user_status(user_oid)
        print(f"用戶狀態: {status_result}")
        
        # 3. 測試消費驗證
        print("\n3️⃣ 測試消費驗證...")
        spend_result = await validation_service.validate_user_can_spend(user_oid, 100)
        print(f"可否消費 100 點: {spend_result}")
        
        # 4. 測試交易驗證
        print("\n4️⃣ 測試交易驗證...")
        trade_result = await validation_service.validate_user_can_trade(user_oid, "buy", 10)
        print(f"可否買入 10 股: {trade_result}")
        
        # 5. 測試扣除點數（應該失敗）
        print("\n5️⃣ 測試扣除點數（應該失敗）...")
        deduct_result = await user_service._safe_deduct_points(user_oid, 50, "測試扣除")
        print(f"扣除 50 點結果: {deduct_result}")
        
        # 6. 測試獲取所有欠款用戶
        print("\n6️⃣ 測試獲取所有欠款用戶...")
        debtors_result = await debt_service.get_all_debtors()
        print(f"欠款用戶數量: {debtors_result.get('total_debtors', 0)}")
        print(f"總欠款金額: {debtors_result.get('total_debt', 0)}")
        
        # 7. 測試償還部分欠款（如果用戶有足夠點數）
        if debt_info.get('success') and debt_info.get('points', 0) > 0:
            print("\n7️⃣ 測試償還部分欠款...")
            repay_amount = min(debt_info['points'], 1)  # 償還 1 點或全部可用點數
            repay_result = await debt_service.repay_debt(user_oid, repay_amount)
            print(f"償還 {repay_amount} 點結果: {repay_result}")
        
        print("\n✅ 債務管理系統測試完成！")
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

async def test_normal_user():
    """測試正常用戶（無欠款）的功能"""
    print("\n🔍 測試正常用戶功能...")
    
    db = get_database()
    validation_service = UserValidationService(db)
    
    # 查找一個沒有欠款的用戶
    users_cursor = db[Collections.USERS].find({
        "$or": [
            {"owed_points": {"$exists": False}},
            {"owed_points": {"$lte": 0}}
        ],
        "enabled": True,
        "frozen": {"$ne": True}
    }).limit(1)
    
    users = await users_cursor.to_list(length=1)
    
    if not users:
        print("⚠️ 沒有找到正常用戶進行測試")
        return
    
    user = users[0]
    user_oid = user["_id"]
    
    print(f"測試用戶: {user.get('name', 'Unknown')} (ID: {user_oid})")
    print(f"點數: {user.get('points', 0)}, 欠款: {user.get('owed_points', 0)}")
    
    # 測試狀態驗證
    status_result = await validation_service.validate_user_status(user_oid)
    print(f"用戶狀態: {status_result}")
    
    # 測試小額消費驗證
    if user.get('points', 0) >= 10:
        spend_result = await validation_service.validate_user_can_spend(user_oid, 10)
        print(f"可否消費 10 點: {spend_result}")

if __name__ == "__main__":
    async def main():
        await test_debt_system()
        await test_normal_user()
    
    asyncio.run(main())