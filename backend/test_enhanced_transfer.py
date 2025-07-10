#!/usr/bin/env python3
"""
測試增強的轉帳功能（包含接收方債務償還）
"""

import asyncio
import sys
import os
from bson import ObjectId

# 添加 app 目錄到路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import connect_to_mongo, get_database, Collections
from app.services.transfer_service import TransferService
from app.schemas.user import TransferRequest

async def test_enhanced_transfer():
    """測試增強的轉帳功能"""
    print("🧪 測試增強的轉帳功能（包含接收方債務償還）...")
    
    # 初始化資料庫連接
    await connect_to_mongo()
    db = get_database()
    transfer_service = TransferService(db)
    
    # 查找一個有欠款的用戶作為接收方
    debtor = await db[Collections.USERS].find_one({"owed_points": {"$gt": 0}})
    
    if not debtor:
        print("⚠️ 沒有找到有欠款的用戶進行測試")
        return
    
    # 查找一個沒有欠款的用戶作為發送方
    sender = await db[Collections.USERS].find_one({
        "$or": [
            {"owed_points": {"$exists": False}},
            {"owed_points": {"$lte": 0}}
        ],
        "enabled": True,
        "frozen": {"$ne": True},
        "points": {"$gte": 100}  # 至少有100點
    })
    
    if not sender:
        print("⚠️ 沒有找到合適的發送方用戶進行測試")
        return
    
    print(f"\n📊 測試設置:")
    print(f"發送方: {sender.get('name')} (ID: {sender['_id']})")
    print(f"  點數: {sender.get('points', 0)}")
    print(f"  欠款: {sender.get('owed_points', 0)}")
    
    print(f"接收方: {debtor.get('name')} (ID: {debtor['_id']})")
    print(f"  點數: {debtor.get('points', 0)}")
    print(f"  欠款: {debtor.get('owed_points', 0)}")
    print(f"  凍結: {debtor.get('frozen', False)}")
    
    # 測試轉帳 50 點
    transfer_amount = 50
    print(f"\n💰 測試轉帳 {transfer_amount} 點...")
    
    request = TransferRequest(
        to_username=debtor.get('name'),
        amount=transfer_amount
    )
    
    try:
        result = await transfer_service.transfer_points(str(sender['_id']), request)
        print(f"轉帳結果: {result}")
        
        if result.success:
            # 檢查轉帳後的狀態
            print(f"\n📊 轉帳後狀態:")
            
            sender_after = await db[Collections.USERS].find_one({'_id': sender['_id']})
            debtor_after = await db[Collections.USERS].find_one({'_id': debtor['_id']})
            
            print(f"發送方: {sender_after.get('name')}")
            print(f"  點數: {sender.get('points', 0)} → {sender_after.get('points', 0)}")
            
            print(f"接收方: {debtor_after.get('name')}")
            print(f"  點數: {debtor.get('points', 0)} → {debtor_after.get('points', 0)}")
            print(f"  欠款: {debtor.get('owed_points', 0)} → {debtor_after.get('owed_points', 0)}")
            print(f"  凍結: {debtor.get('frozen', False)} → {debtor_after.get('frozen', False)}")
            
            # 計算債務償還
            debt_repaid = debtor.get('owed_points', 0) - debtor_after.get('owed_points', 0)
            if debt_repaid > 0:
                print(f"✅ 自動償還欠款: {debt_repaid} 點")
            else:
                print("ℹ️ 沒有自動償還欠款（接收方沒有欠款）")
                
        print("\n✅ 增強轉帳功能測試完成！")
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_enhanced_transfer())