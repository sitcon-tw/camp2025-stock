#!/usr/bin/env python3
"""
測試自我轉帳防護功能
"""

import asyncio
import aiohttp
import json
import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, '/Users/doeshing/Documents/Github/camp2025-stock/backend')

BASE_URL = "http://localhost:8000"

async def test_self_transfer_protection():
    """測試自我轉帳防護功能"""
    
    async with aiohttp.ClientSession() as session:
        print("🧪 開始測試自我轉帳防護功能...")
        
        # 設定測試用的 Bot token (這需要從環境變數或配置中獲取)
        bot_token = os.getenv("BOT_TOKEN", "test_token")
        headers = {"X-Bot-Token": bot_token}
        
        # 使用已知的測試使用者 telegram_id
        test_telegram_id = "123456789"  # 替換為實際的測試使用者 ID
        
        # 測試 1: 相同 telegram_id 的自我轉帳
        print(f"\n📝 測試 1: 使用相同 telegram_id 自我轉帳")
        transfer_data = {
            "from_user": test_telegram_id,
            "to_username": test_telegram_id,  # 相同的 telegram_id
            "amount": 10,
            "note": "測試自我轉帳"
        }
        
        async with session.post(
            f"{BASE_URL}/api/bot/transfer",
            json=transfer_data,
            headers=headers
        ) as response:
            result = await response.json()
            print(f"回應: {result}")
            
            if not result.get("success") and "無法轉帳給自己" in result.get("message", ""):
                print("✅ 測試 1 通過：正確阻止相同 telegram_id 的自我轉帳")
            else:
                print("❌ 測試 1 失敗：未能阻止相同 telegram_id 的自我轉帳")
        
        # 測試 2: 獲取使用者資料以便進行更多測試
        print(f"\n📝 測試 2: 獲取使用者資料")
        profile_data = {"from_user": test_telegram_id}
        
        async with session.post(
            f"{BASE_URL}/api/bot/profile",
            json=profile_data,
            headers=headers
        ) as response:
            if response.status == 200:
                user_profile = await response.json()
                print(f"使用者資料: {user_profile}")
                
                # 如果使用者有 name，測試使用 name 自我轉帳
                if user_profile.get("name"):
                    print(f"\n📝 測試 3: 使用 name 自我轉帳")
                    transfer_data_name = {
                        "from_user": test_telegram_id,
                        "to_username": user_profile["name"],  # 使用 name
                        "amount": 10,
                        "note": "測試使用名字自我轉帳"
                    }
                    
                    async with session.post(
                        f"{BASE_URL}/api/bot/transfer",
                        json=transfer_data_name,
                        headers=headers
                    ) as response:
                        result = await response.json()
                        print(f"回應: {result}")
                        
                        if not result.get("success") and "無法轉帳給自己" in result.get("message", ""):
                            print("✅ 測試 3 通過：正確阻止使用 name 的自我轉帳")
                        else:
                            print("❌ 測試 3 失敗：未能阻止使用 name 的自我轉帳")
            else:
                print(f"❌ 無法獲取使用者資料，狀態碼: {response.status}")
                error_detail = await response.text()
                print(f"錯誤詳情: {error_detail}")

if __name__ == "__main__":
    asyncio.run(test_self_transfer_protection())