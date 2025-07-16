#!/usr/bin/env python3
"""
測試改進的自動償還欠款機制（包含現有點數）
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

async def test_improved_repay():
    """測試改進的自動償還欠款機制"""
    print("🧪 測試改進的自動償還欠款機制（含現有點數）...")
    
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
        current_points = user.get('points', 0)
        current_owed = user.get('owed_points', 0)
        
        print(f"姓名: {user.get('name')}")
        print(f"現有點數: {current_points}")
        print(f"欠款金額: {current_owed}")
        print(f"凍結狀態: {user.get('frozen', False)}")
        print(f"實際可用: {current_points - current_owed}")
        
        # 測試給予 10 點
        give_amount = 10
        print(f"\n💰 測試給予 {give_amount} 點...")
        print(f"預期邏輯:")
        print(f"  可用於償還: {current_points} (現有) + {give_amount} (新給) = {current_points + give_amount}")
        print(f"  實際償還: min({current_points + give_amount}, {current_owed}) = {min(current_points + give_amount, current_owed)}")
        print(f"  剩餘點數: {max(0, current_points + give_amount - current_owed)}")
        print(f"  剩餘欠款: {max(0, current_owed - (current_points + give_amount))}")
        
        request = GivePointsRequest(
            type="user",
            username=user.get('name'),
            amount=give_amount
        )
        
        result = await admin_service.give_points(request)
        print(f"\n✅ 給予點數結果: {result}")
        
        # 檢查更新後的狀態
        print("\n📊 更新後的使用者狀態:")
        user_after = await db[Collections.USERS].find_one({'_id': user_oid})
        new_points = user_after.get('points', 0)
        new_owed = user_after.get('owed_points', 0)
        
        print(f"姓名: {user_after.get('name')}")
        print(f"點數: {new_points}")
        print(f"欠款: {new_owed}")
        print(f"凍結: {user_after.get('frozen', False)}")
        print(f"實際可用: {new_points - new_owed}")
        
        # 計算變化
        points_change = new_points - current_points
        debt_change = current_owed - new_owed
        
        print(f"\n📈 變化摘要:")
        print(f"點數變化: {current_points} → {new_points} ({points_change:+})")
        print(f"欠款變化: {current_owed} → {new_owed} (-{debt_change})")
        print(f"用於償還: {debt_change} 點")
        print(f"來源組成: {current_points} (原有) + {give_amount} (新給) = {current_points + give_amount}")
        
        # 驗證邏輯
        expected_repay = min(current_points + give_amount, current_owed)
        expected_remaining = max(0, current_points + give_amount - current_owed)
        
        if debt_change == expected_repay and new_points == expected_remaining:
            print("✅ 改進的自動償還邏輯完全正確！")
            print(f"✅ 現有點數 {current_points} 已正確用於償還")
        else:
            print("❌ 邏輯有問題！")
            print(f"預期償還: {expected_repay}, 實際償還: {debt_change}")
            print(f"預期剩餘: {expected_remaining}, 實際剩餘: {new_points}")
            
        print("\n✅ 測試完成！")
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_improved_repay())