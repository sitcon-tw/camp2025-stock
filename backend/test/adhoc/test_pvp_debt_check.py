#!/usr/bin/env python3
"""
測試 PvP 功能的債務檢查邏輯
"""

import asyncio
import sys
import os
from bson import ObjectId

# 添加 app 目錄到路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import connect_to_mongo, get_database, Collections
from app.services.user_service import UserService

async def test_pvp_debt_check():
    """測試 PvP 功能的債務檢查邏輯"""
    print("🧪 測試 PvP 功能的債務檢查邏輯...")
    
    # 初始化資料庫連接
    await connect_to_mongo()
    db = get_database()
    user_service = UserService(db)
    
    # 查找一個有欠款的使用者
    debtor = await db[Collections.USERS].find_one({"owed_points": {"$gt": 0}})
    
    if not debtor:
        print("⚠️ 沒有找到有欠款的使用者進行測試")
        return
    
    # 查找一個沒有欠款的正常使用者
    normal_user = await db[Collections.USERS].find_one({
        "$or": [
            {"owed_points": {"$exists": False}},
            {"owed_points": {"$lte": 0}}
        ],
        "enabled": True,
        "frozen": {"$ne": True},
        "points": {"$gte": 100}  # 至少有100點
    })
    
    if not normal_user:
        print("⚠️ 沒有找到合適的正常使用者進行測試")
        return
    
    print(f"\n📊 測試使用者狀態:")
    print(f"有欠款使用者: {debtor.get('name')} (Telegram ID: {debtor.get('telegram_id')})")
    print(f"  點數: {debtor.get('points', 0)}")
    print(f"  欠款: {debtor.get('owed_points', 0)}")
    print(f"  凍結: {debtor.get('frozen', False)}")
    
    print(f"正常使用者: {normal_user.get('name')} (Telegram ID: {normal_user.get('telegram_id')})")
    print(f"  點數: {normal_user.get('points', 0)}")
    print(f"  欠款: {normal_user.get('owed_points', 0)}")
    
    # 測試 1: 有欠款的使用者發起 PvP 挑戰（應該失敗）
    print(f"\n1️⃣ 測試有欠款使用者發起 PvP 挑戰...")
    result1 = await user_service.create_pvp_challenge(
        from_user=debtor.get('telegram_id'),
        amount=50,
        chat_id="test_chat"
    )
    print(f"結果: {result1.success}")
    print(f"訊息: {result1.message}")
    
    # 測試 2: 正常使用者發起 PvP 挑戰（應該成功）
    print(f"\n2️⃣ 測試正常使用者發起 PvP 挑戰...")
    result2 = await user_service.create_pvp_challenge(
        from_user=normal_user.get('telegram_id'),
        amount=50,
        chat_id="test_chat"
    )
    print(f"結果: {result2.success}")
    print(f"訊息: {result2.message}")
    
    # 如果挑戰創建成功，測試有欠款使用者接受挑戰
    if result2.success:
        # 先設置發起者的選擇
        challenge_id = result2.challenge_id if hasattr(result2, 'challenge_id') else None
        
        if challenge_id:
            print(f"\n3️⃣ 設置發起者選擇...")
            choice_result = await user_service.set_pvp_creator_choice(
                from_user=normal_user.get('telegram_id'),
                challenge_id=challenge_id,
                choice="rock"
            )
            print(f"設置選擇結果: {choice_result.success}")
            
            if choice_result.success:
                print(f"\n4️⃣ 測試有欠款使用者接受 PvP 挑戰...")
                accept_result = await user_service.accept_pvp_challenge(
                    from_user=debtor.get('telegram_id'),
                    challenge_id=challenge_id,
                    choice="paper"
                )
                print(f"接受挑戰結果: {accept_result.success}")
                print(f"訊息: {accept_result.message}")
            else:
                print(f"設置選擇失敗: {choice_result.message}")
        else:
            print("⚠️ 無法獲取挑戰 ID")
    
    print("\n✅ PvP 債務檢查測試完成！")

if __name__ == "__main__":
    asyncio.run(test_pvp_debt_check())