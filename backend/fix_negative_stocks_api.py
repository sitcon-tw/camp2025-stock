#!/usr/bin/env python3
"""
通過API調用修復負股票的腳本
"""

import asyncio
import aiohttp
import os
import json

# API基礎URL
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

async def fix_negative_stocks():
    """調用API修復負股票"""
    async with aiohttp.ClientSession() as session:
        try:
            # 1. 管理員登入
            print("🔐 管理員登入中...")
            login_data = {"password": ADMIN_PASSWORD}
            async with session.post(f"{BASE_URL}/admin/login", json=login_data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"❌ 登入失敗: {response.status} - {error_text}")
                    return
                
                login_result = await response.json()
                if not login_result.get("success"):
                    print(f"❌ 登入失敗: {login_result.get('message')}")
                    return
                
                token = login_result.get("token")
                print("✅ 管理員登入成功")
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # 2. 修復無效訂單
            print("\n🔧 開始修復無效訂單...")
            async with session.post(f"{BASE_URL}/admin/fix-invalid-orders", headers=headers) as response:
                result = await response.json()
                
                if response.status == 200:
                    print("✅ 無效訂單修復完成!")
                    print(f"📊 修復結果:")
                    print(f"   - 修復訂單數: {result.get('fixed_count', 0)}")
                    print(f"   - 狀態: {result.get('message', 'N/A')}")
                    
                    # 顯示無效訂單詳情
                    invalid_orders = result.get('invalid_orders', [])
                    if invalid_orders:
                        print(f"📋 修復的無效訂單 ({len(invalid_orders)} 個):")
                        for order in invalid_orders[:5]:  # 只顯示前5個
                            print(f"   - {order['username']}: Order {order['order_id'][:8]}... quantity={order['quantity']}")
                        if len(invalid_orders) > 5:
                            print(f"   ... 還有 {len(invalid_orders) - 5} 個")
                else:
                    print(f"❌ 無效訂單修復失敗: {response.status}")
                    print(f"   錯誤訊息: {result.get('detail', 'Unknown error')}")
            
            # 3. 修復負股票
            print("\n🔧 開始修復負股票...")
            params = {"cancel_pending_orders": True}
            
            async with session.post(f"{BASE_URL}/admin/fix-negative-stocks", 
                                  headers=headers, params=params) as response:
                result = await response.json()
                
                if response.status == 200:
                    print("✅ 負股票修復完成!")
                    print(f"📊 修復結果:")
                    print(f"   - 修復記錄數: {result.get('fixed_count', 0)}")
                    print(f"   - 取消訂單數: {result.get('cancelled_orders', 0)}")
                    print(f"   - 狀態: {result.get('message', 'N/A')}")
                    
                    # 顯示受影響的用戶
                    negative_users = result.get('negative_users', [])
                    if negative_users:
                        print(f"📋 受影響的用戶 ({len(negative_users)} 人):")
                        for user in negative_users:
                            print(f"   - {user['username']} (ID: {user['user_id']}): {user['negative_amount']} 股")
                else:
                    print(f"❌ 負股票修復失敗: {response.status}")
                    print(f"   錯誤訊息: {result.get('detail', 'Unknown error')}")
                
        except aiohttp.ClientError as e:
            print(f"❌ 網絡錯誤: {e}")
        except Exception as e:
            print(f"❌ 未知錯誤: {e}")

if __name__ == "__main__":
    print("🚀 負股票修復工具")
    print(f"📡 API地址: {BASE_URL}")
    print("-" * 50)
    
    asyncio.run(fix_negative_stocks())