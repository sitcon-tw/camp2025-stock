#!/usr/bin/env python3
"""
CAMP_DEBUG admin login
"""

import asyncio
import aiohttp
import json

BASE_URL = "http://localhost:8000"
CAMP_ADMIN_PASSWORD = "admin123"

async def test_login():
    print("建立 ClientSession...")
    
    timeout = aiohttp.ClientTimeout(total=10)  # 10秒超時
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            print(f"嘗試登入 URL: {BASE_URL}/api/admin/login")
            print(f"密碼: {CAMP_ADMIN_PASSWORD}")
            
            async with session.post(
                f"{BASE_URL}/api/admin/login",
                json={"password": CAMP_ADMIN_PASSWORD},
                headers={"Content-Type": "application/json"}
            ) as resp:
                print(f"狀態碼: {resp.status}")
                print(f"Headers: {dict(resp.headers)}")
                
                if resp.status == 200:
                    data = await resp.json()
                    print(f"回應資料: {data}")
                    token = data.get("token")
                    if token:
                        print("✅ 登入成功!")
                        print(f"Token: {token}")
                        return True
                    else:
                        print("❌ 沒有 token")
                        return False
                else:
                    response_text = await resp.text()
                    print(f"❌ 登入失敗，回應: {response_text}")
                    return False
                    
        except asyncio.TimeoutError:
            print("❌ 連線超時")
            return False
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("開始測試...")
    asyncio.run(test_login())
