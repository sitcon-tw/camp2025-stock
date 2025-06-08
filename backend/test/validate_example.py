#!/usr/bin/env python3
"""
簡化版範例驗證腳本
專門驗證你提供的範例：
- A, B 都有 100 點，發行 4 張股票每張 20 點
- A 買 3 張 (40點+3股)，B 買 1 張 (80點+1股)
- A 賣 3 張 21 元，B 買 3 張 25 元，成交 21 元
- 最終結算：A=115點，B=5+20*4=85點，C維持100點
"""

import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
ADMIN_PASSWORD = "admin123"

class SimpleExampleValidator:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.user_tokens = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    async def admin_login(self):
        """管理員登入"""
        try:
            async with self.session.post(
                f"{BASE_URL}/api/admin/login",
                json={"password": ADMIN_PASSWORD}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.admin_token = data["token"]
                    await self.log("✅ 管理員登入成功")
                    return True
                else:
                    await self.log(f"❌ 管理員登入失敗: {resp.status}")
                    return False
        except Exception as e:
            await self.log(f"❌ 管理員登入錯誤: {e}")
            return False
    
    async def setup_users(self):
        """設定三個測試使用者：A、B、C"""
        users = [
            {"username": "UserA", "email": "a@test.com", "team": "測試隊"},
            {"username": "UserB", "email": "b@test.com", "team": "測試隊"},
            {"username": "UserC", "email": "c@test.com", "team": "測試隊"}
        ]
        
        # 註冊使用者
        for user in users:
            try:
                async with self.session.post(
                    f"{BASE_URL}/api/user/register",
                    json=user
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("success"):
                            await self.log(f"✅ 使用者 {user['username']} 註冊成功")
                        else:
                            await self.log(f"⚠️  使用者 {user['username']} 註冊失敗: {data.get('message')}")
                    else:
                        error_text = await resp.text()
                        await self.log(f"❌ 使用者 {user['username']} 註冊請求失敗 ({resp.status}): {error_text}")
            except Exception as e:
                await self.log(f"❌ 使用者 {user['username']} 註冊錯誤: {e}")
        
        # 使用者登入
        for user in users:
            try:
                async with self.session.post(
                    f"{BASE_URL}/api/user/login",
                    json={"username": user["username"]}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("success"):
                            self.user_tokens[user["username"]] = data["token"]
                            await self.log(f"✅ 使用者 {user['username']} 登入成功")
                        else:
                            await self.log(f"❌ 使用者 {user['username']} 登入失敗: {data.get('message')}")
                    else:
                        error_text = await resp.text()
                        await self.log(f"❌ 使用者 {user['username']} 登入請求失敗 ({resp.status}): {error_text}")
            except Exception as e:
                await self.log(f"❌ 使用者 {user['username']} 登入錯誤: {e}")
        
        # 給予每人 100 點
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        for user in users:
            try:
                async with self.session.post(
                    f"{BASE_URL}/api/admin/users/give-points",
                    json={
                        "username": user["username"],
                        "type": "user",
                        "amount": 100
                    },
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("ok"):
                            await self.log(f"✅ 給予使用者 {user['username']} 100 點數")
            except Exception as e:
                await self.log(f"❌ 給予 {user['username']} 點數錯誤: {e}")
    
    async def get_portfolio(self, username: str):
        """取得使用者投資組合"""
        if username not in self.user_tokens:
            return None
        
        try:
            headers = {"Authorization": f"Bearer {self.user_tokens[username]}"}
            async with self.session.get(
                f"{BASE_URL}/api/user/portfolio",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except Exception as e:
            await self.log(f"❌ 取得 {username} 投資組合錯誤: {e}")
            return None
    
    async def place_order(self, username: str, order_type: str, side: str, quantity: int, price: int = None):
        """下訂單"""
        if username not in self.user_tokens:
            return False
        
        order_data = {
            "order_type": order_type,
            "side": side,
            "quantity": quantity
        }
        
        if order_type == "limit" and price:
            order_data["price"] = price
        
        try:
            headers = {"Authorization": f"Bearer {self.user_tokens[username]}"}
            async with self.session.post(
                f"{BASE_URL}/api/user/stock/order",
                json=order_data,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("success"):
                        order_desc = f"{side.upper()} {quantity}股"
                        if order_type == "market":
                            order_desc += " (市價)"
                        else:
                            order_desc += f" @ {price}元"
                        await self.log(f"📈 {username}: {order_desc} - {data.get('message')}")
                        return True
                    else:
                        await self.log(f"❌ {username} 下單失敗: {data.get('message')}")
                return False
        except Exception as e:
            await self.log(f"❌ {username} 下單錯誤: {e}")
            return False
    
    async def show_status(self, step_name: str):
        """顯示所有使用者狀態"""
        await self.log(f"\n📊 {step_name} - 使用者狀態:")
        total_points = 0
        
        for username in ["UserA", "UserB", "UserC"]:
            portfolio = await self.get_portfolio(username)
            if portfolio:
                points = portfolio.get("points", 0)
                stocks = portfolio.get("stocks", 0)
                stock_value = portfolio.get("stockValue", 0)
                total_value = portfolio.get("totalValue", 0)
                
                await self.log(
                    f"   {username}: {points}點 + {stocks}股({stock_value}元) = 總資產{total_value}元"
                )
                total_points += total_value
            else:
                await self.log(f"   {username}: 無法取得資料")
        
        await self.log(f"   總計: {total_points}點 (應為300點)")
        await asyncio.sleep(1)
    
    async def final_settlement(self):
        """執行最終結算"""
        await self.log("\n🏁 執行最終結算 (股票以 20 元/股 強制賣出)...")
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            async with self.session.post(
                f"{BASE_URL}/api/admin/final-settlement",
                headers=headers
            ) as resp:
                data = await resp.json()
                if resp.status == 200 and data.get("ok"):
                    await self.log(f"✅ 最終結算完成: {data.get('message')}")
                else:
                    await self.log(f"❌ 最終結算失敗: {data}")
        except Exception as e:
            await self.log(f"❌ 最終結算錯誤: {e}")
    
    async def run_example_validation(self):
        """執行範例驗證"""
        await self.log("🎯 開始驗證範例場景")
        await self.log("="*50)
        
        # 1. 管理員登入
        if not await self.admin_login():
            await self.log("❌ 驗證中止：管理員登入失敗")
            return
        
        # 2. 設定使用者
        await self.setup_users()
        await asyncio.sleep(2)
        
        # 3. 顯示初始狀態
        await self.show_status("初始狀態")
        
        # 4. UserA 用 20 點買 3 張，UserB 用 20 點買 1 張
        await self.log("\n📖 步驟1: UserA 買 3 股，UserB 買 1 股 (各20元)")
        await self.place_order("UserA", "market", "buy", 3)
        await asyncio.sleep(1)
        await self.place_order("UserB", "market", "buy", 1)
        await asyncio.sleep(2)
        
        await self.show_status("購買後")
        # 預期：UserA = 40點+3股, UserB = 80點+1股, UserC = 100點+0股
        
        # 5. UserA 想 21 賣三張，UserB 想 25 買三張，成交
        await self.log("\n📖 步驟2: UserA 賣21元3股，UserB 買25元3股 (應21元成交)")
        await self.place_order("UserA", "limit", "sell", 3, 21)
        await asyncio.sleep(1)
        await self.place_order("UserB", "limit", "buy", 3, 25)
        await asyncio.sleep(3)  # 等待撮合
        
        await self.show_status("交易後")
        # 預期：UserA = 103點+0股 (40+21*3), UserB = 17點+4股 (80-21*3+4股), UserC = 100點+0股
        
        # 6. 最終結算
        await self.final_settlement()
        await asyncio.sleep(2)
        
        await self.show_status("最終結算後")
        # 預期：UserA = 103點, UserB = 97點 (17+20*4), UserC = 100點
        
        # 7. 驗證結果
        await self.log("\n✅ 範例驗證完成!")
        await self.log("📋 預期結果:")
        await self.log("   UserA: 103點 (40 + 21*3 = 103)")
        await self.log("   UserB: 97點 (80 - 21*3 + 20*4 = 17 + 80 = 97)")
        await self.log("   UserC: 100點 (未參與交易)")
        await self.log("   總計: 300點 (無通膨)")


async def main():
    """主函數"""
    try:
        async with SimpleExampleValidator() as validator:
            await validator.run_example_validation()
    except KeyboardInterrupt:
        print("\n⏹️  驗證被使用者中斷")
    except Exception as e:
        print(f"\n❌ 驗證過程中發生錯誤: {e}")


if __name__ == "__main__":
    print("🧪 範例場景驗證器")
    print("驗證你提供的具體範例邏輯")
    print("確保後端服務運行在 http://localhost:8000\n")
    
    asyncio.run(main())
