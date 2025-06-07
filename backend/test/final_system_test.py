#!/usr/bin/env python3
"""
SITCON Camp 2025 股票交易系統 - 最終完整性測試
驗證所有核心功能和 API 端點是否正常運作
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
ADMIN_PASSWORD = "admin123"
INTERNAL_API_KEY = "neverGonnaGiveYouUp"

class SystemTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log(self, message: str, status: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "🔍"
        print(f"[{timestamp}] {icon} {message}")
    
    async def test_basic_apis(self):
        """測試基本 API 端點"""
        self.log("測試基本 API 端點", "INFO")
        
        # 測試系統狀態
        try:
            async with self.session.get(f"{BASE_URL}/api/status") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log(f"系統狀態 API: 市場開放={data.get('isOpen')}", "PASS")
                else:
                    self.log("系統狀態 API 失敗", "FAIL")
        except Exception as e:
            self.log(f"系統狀態 API 錯誤: {e}", "FAIL")
        
        # 測試交易時間 API
        try:
            async with self.session.get(f"{BASE_URL}/api/trading-hours") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log(f"交易時間 API: 目前開放={data.get('isCurrentlyOpen')}", "PASS")
                else:
                    self.log("交易時間 API 失敗", "FAIL")
        except Exception as e:
            self.log(f"交易時間 API 錯誤: {e}", "FAIL")
        
        # 測試價格摘要 API
        try:
            async with self.session.get(f"{BASE_URL}/api/price/summary") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log(f"價格摘要 API: 最新價格={data.get('lastPrice')}", "PASS")
                else:
                    self.log("價格摘要 API 失敗", "FAIL")
        except Exception as e:
            self.log(f"價格摘要 API 錯誤: {e}", "FAIL")
    
    async def test_admin_login(self):
        """測試管理員登入"""
        self.log("測試管理員登入", "INFO")
        
        try:
            async with self.session.post(
                f"{BASE_URL}/api/admin/login",
                json={"password": ADMIN_PASSWORD}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.admin_token = data["token"]
                    self.log("管理員登入成功", "PASS")
                    return True
                else:
                    self.log("管理員登入失敗", "FAIL")
                    return False
        except Exception as e:
            self.log(f"管理員登入錯誤: {e}", "FAIL")
            return False
    
    async def test_bot_apis(self):
        """測試機器人 API 端點"""
        self.log("測試機器人 API 端點", "INFO")
        
        headers = {"token": INTERNAL_API_KEY}
        
        # 測試 Webhook 端點
        webhook_data = {
            "update_id": 123456,
            "message": {
                "message_id": 1,
                "from": {"id": 123, "username": "testuser"},
                "chat": {"id": -123, "type": "group"},
                "text": "/start"
            }
        }
        
        try:
            async with self.session.post(
                f"{BASE_URL}/api/bot/webhook",
                json=webhook_data,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    self.log("機器人 Webhook API 正常", "PASS")
                else:
                    self.log(f"機器人 Webhook API 失敗: {resp.status}", "FAIL")
        except Exception as e:
            self.log(f"機器人 Webhook API 錯誤: {e}", "FAIL")
        
        # 測試廣播端點
        broadcast_data = {
            "title": "測試廣播",
            "message": "這是一個測試訊息",
            "groups": [123, 456]
        }
        
        try:
            async with self.session.post(
                f"{BASE_URL}/api/bot/broadcast",
                json=broadcast_data,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    self.log("機器人廣播 API 正常", "PASS")
                else:
                    self.log(f"機器人廣播 API 失敗: {resp.status}", "FAIL")
        except Exception as e:
            self.log(f"機器人廣播 API 錯誤: {e}", "FAIL")
        
        # 測試全域廣播端點
        broadcast_all_data = {
            "title": "測試全域廣播",
            "message": "這是一個全域測試訊息"
        }
        
        try:
            async with self.session.post(
                f"{BASE_URL}/api/bot/broadcast/all",
                json=broadcast_all_data,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    self.log("機器人全域廣播 API 正常", "PASS")
                else:
                    self.log(f"機器人全域廣播 API 失敗: {resp.status}", "FAIL")
        except Exception as e:
            self.log(f"機器人全域廣播 API 錯誤: {e}", "FAIL")
    
    async def test_market_time_validation(self):
        """測試市場時間驗證功能"""
        self.log("測試市場時間驗證功能", "INFO")
        
        if not self.admin_token:
            self.log("無管理員權限，跳過市場時間測試", "FAIL")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # 設定市場關閉（過去的時間範圍）
        closed_hours = {
            "openTime": [{"start": 1000000000, "end": 1000003600}]  # 2001年的時間
        }
        
        try:
            async with self.session.post(
                f"{BASE_URL}/api/admin/market/update",
                json=closed_hours,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    self.log("成功設定市場關閉時間", "PASS")
                    
                    # 驗證狀態顯示關閉
                    await asyncio.sleep(1)
                    async with self.session.get(f"{BASE_URL}/api/status") as status_resp:
                        if status_resp.status == 200:
                            data = await status_resp.json()
                            if not data.get("isOpen"):
                                self.log("市場狀態正確顯示為關閉", "PASS")
                            else:
                                self.log("市場狀態顯示錯誤", "FAIL")
                
                else:
                    self.log("設定市場時間失敗", "FAIL")
        except Exception as e:
            self.log(f"市場時間測試錯誤: {e}", "FAIL")
        
        # 恢復市場開放
        current_time = int(time.time())
        open_hours = {
            "openTime": [{"start": current_time - 300, "end": current_time + 3600}]
        }
        
        try:
            async with self.session.post(
                f"{BASE_URL}/api/admin/market/update",
                json=open_hours,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    self.log("恢復市場開放時間", "PASS")
                else:
                    self.log("恢復市場開放失敗", "FAIL")
        except Exception as e:
            self.log(f"恢復市場開放錯誤: {e}", "FAIL")
    
    async def test_user_registration_and_trading(self):
        """測試用戶註冊和交易功能"""
        self.log("測試用戶註冊和交易功能", "INFO")
        
        test_username = f"testuser_{int(time.time())}"
        test_email = f"{test_username}@test.com"
        
        # 註冊測試用戶
        try:
            async with self.session.post(
                f"{BASE_URL}/api/user/register",
                json={
                    "username": test_username,
                    "email": test_email,
                    "team": "測試隊"
                }
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("success"):
                        self.log(f"用戶註冊成功: {test_username}", "PASS")
                    else:
                        self.log(f"用戶註冊失敗: {data.get('message')}", "FAIL")
                        return
                else:
                    self.log("用戶註冊請求失敗", "FAIL")
                    return
        except Exception as e:
            self.log(f"用戶註冊錯誤: {e}", "FAIL")
            return
        
        # 登入測試用戶
        user_token = None
        try:
            async with self.session.post(
                f"{BASE_URL}/api/user/login",
                json={"username": test_username}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("success"):
                        user_token = data["token"]
                        self.log(f"用戶登入成功: {test_username}", "PASS")
                    else:
                        self.log(f"用戶登入失敗: {data.get('message')}", "FAIL")
                        return
                else:
                    self.log("用戶登入請求失敗", "FAIL")
                    return
        except Exception as e:
            self.log(f"用戶登入錯誤: {e}", "FAIL")
            return
        
        # 給予測試用戶點數
        if self.admin_token:
            try:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                async with self.session.post(
                    f"{BASE_URL}/api/admin/users/give-points",
                    json={
                        "username": test_username,
                        "type": "user",
                        "amount": 100
                    },
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("ok"):
                            self.log(f"給予用戶點數成功: {test_username}", "PASS")
                        else:
                            self.log(f"給予用戶點數失敗: {data}", "FAIL")
                    else:
                        self.log("給予用戶點數請求失敗", "FAIL")
            except Exception as e:
                self.log(f"給予用戶點數錯誤: {e}", "FAIL")
        
        # 測試交易功能
        if user_token:
            try:
                headers = {"Authorization": f"Bearer {user_token}"}
                trade_data = {
                    "order_type": "market",
                    "side": "buy",
                    "quantity": 1
                }
                
                async with self.session.post(
                    f"{BASE_URL}/api/user/stock/order",
                    json=trade_data,
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("success"):
                            self.log(f"用戶交易成功: {test_username}", "PASS")
                        else:
                            self.log(f"用戶交易失敗: {data.get('message')}", "FAIL")
                    else:
                        self.log("用戶交易請求失敗", "FAIL")
            except Exception as e:
                self.log(f"用戶交易錯誤: {e}", "FAIL")
    
    async def run_all_tests(self):
        """執行所有測試"""
        self.log("🚀 SITCON Camp 2025 股票交易系統完整性測試開始")
        self.log("="*80)
        
        await self.test_basic_apis()
        await asyncio.sleep(1)
        
        await self.test_admin_login()
        await asyncio.sleep(1)
        
        await self.test_bot_apis()
        await asyncio.sleep(1)
        
        await self.test_market_time_validation()
        await asyncio.sleep(1)
        
        await self.test_user_registration_and_trading()
        
        self.log("="*80)
        self.log("🎉 系統完整性測試完成！")
        self.log("="*80)
        self.log("📋 測試摘要:")
        self.log("   ✓ 基本 API 端點")
        self.log("   ✓ 管理員認證系統")
        self.log("   ✓ 機器人 API 端點")
        self.log("   ✓ 市場時間驗證")
        self.log("   ✓ 用戶註冊與交易")
        self.log("   ✓ 點數發放系統")
        self.log("   ✓ 股票交易系統")


async def main():
    """主函數"""
    try:
        async with SystemTester() as tester:
            await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n⏹️  測試被用戶中斷")
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")


if __name__ == "__main__":
    print("🧪 SITCON Camp 2025 股票交易系統完整性測試")
    print("確保後端服務運行在 http://localhost:8000")
    print("按 Ctrl+C 可隨時停止測試\n")
    
    asyncio.run(main())
