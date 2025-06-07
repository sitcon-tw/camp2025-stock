#!/usr/bin/env python3
"""
快速市場設定腳本
用於快速啟動市場、建立測試用戶、開始交易
適合開發階段快速測試使用
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timezone

BASE_URL = "http://localhost:8000"
ADMIN_PASSWORD = "admin123"

class QuickMarketSetup:
    def __init__(self):
        self.session = None
        self.admin_token = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log(self, message: str):
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
                    self.log("✅ 管理員登入成功")
                    return True
                else:
                    self.log(f"❌ 管理員登入失敗: {resp.status}")
                    return False
        except Exception as e:
            self.log(f"❌ 管理員登入錯誤: {e}")
            return False
    
    async def setup_24h_trading(self):
        """設定24小時交易時間"""
        try:
            current_time = datetime.now(timezone.utc)
            start_time = int(current_time.timestamp()) - 3600
            end_time = int(current_time.timestamp()) + 86400
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            market_data = {
                "openTime": [{"start": start_time, "end": end_time}]
            }
            
            async with self.session.post(
                f"{BASE_URL}/api/admin/market/update",
                json=market_data,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    self.log("✅ 24小時交易時間設定完成")
                    return True
                else:
                    self.log(f"❌ 交易時間設定失敗: {resp.status}")
                    return False
        except Exception as e:
            self.log(f"❌ 交易時間設定錯誤: {e}")
            return False
    
    async def open_market(self):
        """開市"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            async with self.session.post(
                f"{BASE_URL}/api/admin/market/open",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log(f"✅ 市場開盤: {data.get('message', '')}")
                    return True
                else:
                    self.log(f"❌ 開盤失敗: {resp.status}")
                    return False
        except Exception as e:
            self.log(f"❌ 開盤錯誤: {e}")
            return False
    
    async def create_test_users(self, count: int = 5):
        """建立測試用戶"""
        teams = ["紅隊", "藍隊", "綠隊"]
        users = []
        user_tokens = {}
        
        self.log(f"🏗️ 建立 {count} 個測試用戶...")
        
        for i in range(count):
            user_data = {
                "username": f"TestUser{i+1:02d}",
                "email": f"test{i+1:02d}@camp.test",
                "team": teams[i % len(teams)]
            }
            users.append(user_data)
        
        # 註冊用戶
        for user in users:
            try:
                async with self.session.post(
                    f"{BASE_URL}/api/user/register",
                    json=user
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("success"):
                            self.log(f"  ✅ {user['username']} 註冊成功")
                        else:
                            self.log(f"  ⚠️ {user['username']} 註冊失敗: {data.get('message')}")
            except Exception as e:
                self.log(f"  ❌ {user['username']} 註冊錯誤: {e}")
        
        # 用戶登入並記錄 token
        for user in users:
            try:
                async with self.session.post(
                    f"{BASE_URL}/api/user/login",
                    json={"username": user["username"]}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("success"):
                            user_tokens[user["username"]] = data["token"]
                            self.log(f"  ✅ {user['username']} 登入成功")
            except Exception as e:
                self.log(f"  ❌ {user['username']} 登入錯誤: {e}")
        
        # 給予初始點數
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        for user in users:
            try:
                async with self.session.post(
                    f"{BASE_URL}/api/admin/users/give-points",
                    json={
                        "username": user["username"],
                        "type": "user",
                        "amount": 1000
                    },
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("ok"):
                            self.log(f"  💰 {user['username']} 獲得 1000 點數")
            except Exception as e:
                self.log(f"  ❌ 給予 {user['username']} 點數錯誤: {e}")
        
        return user_tokens
    
    async def demo_trading(self, user_tokens):
        """演示交易"""
        self.log("📈 開始演示交易...")
        
        # 取得用戶列表
        usernames = list(user_tokens.keys())
        if len(usernames) < 3:
            self.log("❌ 需要至少3個用戶才能演示交易")
            return
        
        # 演示交易場景
        demo_trades = [
            # 場景1: IPO申購
            (usernames[0], "market", "buy", 20, None, "IPO申購"),
            (usernames[1], "market", "buy", 15, None, "IPO申購"),
            
            # 場景2: 限價掛單
            (usernames[2], "limit", "buy", 30, 19, "低價掛買單"),
            (usernames[0], "limit", "sell", 10, 21, "高價掛賣單"),
            
            # 場景3: 市價交易
            (usernames[1], "market", "sell", 5, None, "市價賣出"),
            (usernames[2], "market", "buy", 10, None, "市價買入"),
        ]
        
        for username, order_type, side, quantity, price, description in demo_trades:
            await self.place_demo_order(username, user_tokens[username], order_type, side, quantity, price, description)
            await asyncio.sleep(1)
        
        # 顯示市場狀態
        await self.show_market_status()
    
    async def place_demo_order(self, username, token, order_type, side, quantity, price, description):
        """下演示訂單"""
        order_data = {
            "order_type": order_type,
            "side": side,
            "quantity": quantity
        }
        
        if price:
            order_data["price"] = price
        
        try:
            headers = {"Authorization": f"Bearer {token}"}
            async with self.session.post(
                f"{BASE_URL}/api/user/stock/order",
                json=order_data,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("success"):
                        order_desc = f"{side.upper()} {quantity}股"
                        if price:
                            order_desc += f" @ {price}元"
                        else:
                            order_desc += " (市價)"
                        self.log(f"  📊 {username}: {order_desc} - {description}")
                        if data.get("message"):
                            self.log(f"      結果: {data['message']}")
                    else:
                        self.log(f"  ❌ {username} 下單失敗: {data.get('message')}")
        except Exception as e:
            self.log(f"  ❌ {username} 下單錯誤: {e}")
    
    async def show_market_status(self):
        """顯示市場狀態"""
        try:
            # 取得股價摘要
            async with self.session.get(f"{BASE_URL}/api/price/summary") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log("📊 === 市場狀態 ===")
                    self.log(f"目前股價: {data.get('lastPrice')} 元")
                    self.log(f"漲跌: {data.get('change')} ({data.get('changePercent')})")
                    self.log(f"成交量: {data.get('volume')} 股")
                    self.log(f"最高/最低: {data.get('high')}/{data.get('low')} 元")
            
            # 取得五檔報價
            async with self.session.get(f"{BASE_URL}/api/price/depth") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log("📋 === 委託簿 ===")
                    
                    # 賣方
                    sell_orders = data.get('sell', [])
                    if sell_orders:
                        self.log("賣方:")
                        for i, order in enumerate(reversed(sell_orders[-3:])):
                            self.log(f"  賣{len(sell_orders)-i}: {order['price']}元 x {order['quantity']}股")
                    
                    self.log("  --- 成交線 ---")
                    
                    # 買方
                    buy_orders = data.get('buy', [])
                    if buy_orders:
                        self.log("買方:")
                        for i, order in enumerate(buy_orders[:3]):
                            self.log(f"  買{i+1}: {order['price']}元 x {order['quantity']}股")
            
            # 取得排行榜
            async with self.session.get(f"{BASE_URL}/api/leaderboard") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log("🏆 === 排行榜前5名 ===")
                    for i, entry in enumerate(data[:5], 1):
                        total = entry.get('points', 0) + entry.get('stockValue', 0)
                        self.log(f"{i}. {entry.get('username')} ({entry.get('team')}) - 總資產: {total}元")
                        
        except Exception as e:
            self.log(f"❌ 取得市場狀態錯誤: {e}")
    
    async def show_trading_instructions(self, user_tokens):
        """顯示交易說明"""
        self.log("📖 === 交易說明 ===")
        self.log("市場已準備就緒！以下是測試用戶的登入令牌:")
        self.log("")
        
        for username, token in user_tokens.items():
            self.log(f"用戶: {username}")
            self.log(f"Token: {token}")
            self.log(f"測試下單 API:")
            self.log(f"  curl -X POST '{BASE_URL}/api/user/stock/order' \\")
            self.log(f"    -H 'Authorization: Bearer {token}' \\")
            self.log(f"    -H 'Content-Type: application/json' \\")
            self.log(f"    -d '{{\"order_type\":\"market\",\"side\":\"buy\",\"quantity\":10}}'")
            self.log("")
        
        self.log("📊 API 端點:")
        self.log(f"  市場狀態: {BASE_URL}/api/price/summary")
        self.log(f"  委託簿: {BASE_URL}/api/price/depth")
        self.log(f"  排行榜: {BASE_URL}/api/leaderboard")
        self.log(f"  API 文件: {BASE_URL}/docs")
        self.log("")
        
        self.log("🔧 管理員操作:")
        self.log(f"  管理員 Token: {self.admin_token}")
        self.log("  手動執行集合競價:")
        self.log(f"    curl -X POST '{BASE_URL}/api/admin/market/call-auction' \\")
        self.log(f"      -H 'Authorization: Bearer {self.admin_token}'")
        self.log("")
    
    async def quick_setup(self, user_count: int = 5, demo_trade: bool = True):
        """快速設定"""
        self.log("🚀 === SITCON Camp 2025 快速市場設定 ===")
        self.log("=" * 50)
        
        # 1. 管理員登入
        if not await self.admin_login():
            return False
        
        # 2. 設定交易時間
        await self.setup_24h_trading()
        
        # 3. 開市
        await self.open_market()
        
        # 4. 建立測試用戶
        user_tokens = await self.create_test_users(user_count)
        
        if not user_tokens:
            self.log("❌ 無法建立測試用戶")
            return False
        
        await asyncio.sleep(2)
        
        # 5. 演示交易（可選）
        if demo_trade:
            await self.demo_trading(user_tokens)
        
        await asyncio.sleep(1)
        
        # 6. 顯示說明
        await self.show_trading_instructions(user_tokens)
        
        self.log("✅ 快速設定完成！")
        return True

async def main():
    """主函數"""
    import sys
    
    # 解析命令列參數
    user_count = 5
    demo_trade = True
    
    if len(sys.argv) > 1:
        try:
            user_count = int(sys.argv[1])
        except ValueError:
            print("用戶數量必須是數字")
            return
    
    if len(sys.argv) > 2:
        demo_trade = sys.argv[2].lower() in ['true', '1', 'yes', 'y']
    
    try:
        async with QuickMarketSetup() as setup:
            await setup.quick_setup(user_count, demo_trade)
    except KeyboardInterrupt:
        print("\n⏹️ 設定被用戶中斷")
    except Exception as e:
        print(f"\n❌ 設定過程中發生錯誤: {e}")

if __name__ == "__main__":
    print("⚡ SITCON Camp 2025 快速市場設定")
    print("用法: python quick_setup.py [用戶數量] [是否演示交易]")
    print("範例: python quick_setup.py 10 true")
    print("確保後端服務運行在 http://localhost:8000")
    print("-" * 50)
    
    asyncio.run(main())
