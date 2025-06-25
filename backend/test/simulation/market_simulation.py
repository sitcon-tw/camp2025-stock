#!/usr/bin/env python3
"""
SITCON Camp 2025 股票市場完整模擬腳本
功能包含：
1. 系統初始化（重置資料、開市設定）
2. 使用者帳號啟用
3. 交易時間設定
4. 模擬多種交易場景
5. 即時市場狀況監控
"""

import asyncio
import aiohttp
import json
import random
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
import time

BASE_URL = "http://localhost:8000"
ADMIN_PASSWORD = "admin123"

class MarketSimulator:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.user_tokens = {}
        self.test_users = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        icons = {
            "INFO": "ℹ️",
            "SUCCESS": "✅", 
            "ERROR": "❌",
            "WARNING": "⚠️",
            "TRADE": "📈",
            "MARKET": "📊",
            "ADMIN": "🔧"
        }
        icon = icons.get(level, "📝")
        print(f"[{timestamp}] {icon} {message}")
    
    async def admin_login(self) -> bool:
        """管理員登入"""
        try:
            async with self.session.post(
                f"{BASE_URL}/api/admin/login",
                json={"password": ADMIN_PASSWORD}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.admin_token = data["token"]
                    self.log("管理員登入成功", "SUCCESS")
                    return True
                else:
                    self.log(f"管理員登入失敗: {resp.status}", "ERROR")
                    return False
        except Exception as e:
            self.log(f"管理員登入錯誤: {e}", "ERROR")
            return False
    
    async def reset_system(self) -> bool:
        """重置系統資料"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            async with self.session.post(
                f"{BASE_URL}/api/admin/reset/alldata",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log(f"系統重置成功: {data.get('message')}", "ADMIN")
                    return True
                else:
                    self.log(f"系統重置失敗: {resp.status}", "ERROR")
                    return False
        except Exception as e:
            self.log(f"系統重置錯誤: {e}", "ERROR")
            return False
    
    async def setup_market_hours(self) -> bool:
        """設定交易時間（24小時開放）"""
        try:
            # 設定24小時交易時間
            current_time = datetime.now(timezone.utc)
            start_time = int(current_time.timestamp()) - 3600  # 1小時前開始
            end_time = int(current_time.timestamp()) + 86400  # 24小時後結束
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            market_data = {
                "openTime": [
                    {
                        "start": start_time,
                        "end": end_time
                    }
                ]
            }
            
            async with self.session.post(
                f"{BASE_URL}/api/admin/market/update",
                json=market_data,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    self.log("交易時間設定成功（24小時開放）", "ADMIN")
                    return True
                else:
                    self.log(f"交易時間設定失敗: {resp.status}", "ERROR")
                    return False
        except Exception as e:
            self.log(f"交易時間設定錯誤: {e}", "ERROR")
            return False
    
    async def setup_trading_limits(self) -> bool:
        """設定漲跌幅限制"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            limit_data = {
                "limitPercent": 3000  # 30% 漲跌幅限制
            }
            
            async with self.session.post(
                f"{BASE_URL}/api/admin/market/set-limit",
                json=limit_data,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    self.log("漲跌幅限制設定成功（30%）", "ADMIN")
                    return True
                else:
                    self.log(f"漲跌幅限制設定失敗: {resp.status}", "ERROR")
                    return False
        except Exception as e:
            self.log(f"漲跌幅限制設定錯誤: {e}", "ERROR")
            return False
    
    async def open_market(self) -> bool:
        """手動開市"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            async with self.session.post(
                f"{BASE_URL}/api/admin/market/open",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log(f"市場開盤成功: {data.get('message')}", "MARKET")
                    return True
                else:
                    self.log(f"市場開盤失敗: {resp.status}", "ERROR")
                    return False
        except Exception as e:
            self.log(f"市場開盤錯誤: {e}", "ERROR")
            return False
    
    async def create_test_users(self, count: int = 10) -> bool:
        """建立測試使用者"""
        teams = ["紅隊", "藍隊", "綠隊", "黃隊", "紫隊"]
        
        self.test_users = []
        for i in range(count):
            user_data = {
                "username": f"Trader{i+1:02d}",
                "email": f"trader{i+1:02d}@camp.test",
                "team": teams[i % len(teams)]
            }
            self.test_users.append(user_data)
        
        # 註冊使用者
        success_count = 0
        for user in self.test_users:
            try:
                async with self.session.post(
                    f"{BASE_URL}/api/user/register",
                    json=user
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("success"):
                            success_count += 1
                        else:
                            self.log(f"使用者 {user['username']} 註冊失敗: {data.get('message')}", "WARNING")
                    else:
                        self.log(f"使用者 {user['username']} 註冊請求失敗: {resp.status}", "WARNING")
            except Exception as e:
                self.log(f"使用者 {user['username']} 註冊錯誤: {e}", "ERROR")
        
        # 使用者登入
        login_count = 0
        for user in self.test_users:
            try:
                async with self.session.post(
                    f"{BASE_URL}/api/user/login",
                    json={"username": user["username"]}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("success"):
                            self.user_tokens[user["username"]] = data["token"]
                            login_count += 1
                        else:
                            self.log(f"使用者 {user['username']} 登入失敗: {data.get('message')}", "WARNING")
            except Exception as e:
                self.log(f"使用者 {user['username']} 登入錯誤: {e}", "ERROR")
        
        self.log(f"測試使用者建立完成: {success_count}/{count} 註冊, {login_count}/{count} 登入", "SUCCESS")
        return login_count > 0
    
    async def give_initial_points(self, points_per_user: int = 1000) -> bool:
        """給予使用者初始點數"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        success_count = 0
        
        for user in self.test_users:
            try:
                async with self.session.post(
                    f"{BASE_URL}/api/admin/users/give-points",
                    json={
                        "username": user["username"],
                        "type": "user", 
                        "amount": points_per_user
                    },
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("ok"):
                            success_count += 1
            except Exception as e:
                self.log(f"給予 {user['username']} 點數錯誤: {e}", "ERROR")
        
        self.log(f"初始點數發放完成: {success_count}/{len(self.test_users)} 成功，每人 {points_per_user} 點", "ADMIN")
        return success_count > 0
    
    async def place_order(self, username: str, order_type: str, side: str, quantity: int, price: int = None) -> bool:
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
                        self.log(f"{username}: {order_desc} - {data.get('message')}", "TRADE")
                        return True
                    else:
                        self.log(f"{username} 下單失敗: {data.get('message')}", "WARNING")
                        return False
        except Exception as e:
            self.log(f"{username} 下單錯誤: {e}", "ERROR")
            return False
        
        return False
    
    async def get_market_status(self) -> Dict:
        """取得市場狀態"""
        try:
            async with self.session.get(f"{BASE_URL}/api/price/summary") as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception as e:
            self.log(f"取得市場狀態錯誤: {e}", "ERROR")
        return {}
    
    async def get_order_book(self) -> Dict:
        """取得委託簿"""
        try:
            async with self.session.get(f"{BASE_URL}/api/price/depth") as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception as e:
            self.log(f"取得委託簿錯誤: {e}", "ERROR")
        return {}
    
    async def show_market_overview(self):
        """顯示市場總覽"""
        market_status = await self.get_market_status()
        order_book = await self.get_order_book()
        
        if market_status:
            self.log("=== 市場狀態 ===", "MARKET")
            self.log(f"目前股價: {market_status.get('lastPrice', 'N/A')} 元", "MARKET")
            self.log(f"漲跌: {market_status.get('change', 'N/A')} ({market_status.get('changePercent', 'N/A')})", "MARKET")
            self.log(f"成交量: {market_status.get('volume', 'N/A')} 股", "MARKET")
            self.log(f"最高: {market_status.get('high', 'N/A')} / 最低: {market_status.get('low', 'N/A')}", "MARKET")
        
        if order_book:
            self.log("=== 五檔報價 ===", "MARKET")
            # 賣方
            sell_orders = order_book.get('sell', [])
            for i, order in enumerate(reversed(sell_orders[-5:])):
                self.log(f"賣{len(sell_orders)-i}: {order.get('price')} 元 ({order.get('quantity')} 股)", "MARKET")
            
            self.log("--- 成交價 ---", "MARKET")
            
            # 買方
            buy_orders = order_book.get('buy', [])
            for i, order in enumerate(buy_orders[:5]):
                self.log(f"買{i+1}: {order.get('price')} 元 ({order.get('quantity')} 股)", "MARKET")
    
    async def simulate_ipo_phase(self):
        """模擬 IPO 階段"""
        self.log("🚀 開始 IPO 階段模擬", "MARKET")
        
        # 一些使用者進行 IPO 申購（市價單）
        ipo_buyers = random.sample(self.test_users[:8], 5)  # 隨機選5個使用者
        
        for user in ipo_buyers:
            quantity = random.randint(10, 50)  # 10-50股
            await self.place_order(user["username"], "market", "buy", quantity)
            await asyncio.sleep(0.5)
        
        await asyncio.sleep(2)
        await self.show_market_overview()
    
    async def simulate_active_trading(self):
        """模擬活躍交易階段"""
        self.log("📈 開始活躍交易階段模擬", "MARKET")
        
        # 獲取目前股價作為基準
        market_status = await self.get_market_status()
        current_price = market_status.get('lastPrice', 20)
        
        trading_scenarios = [
            # 場景1: 搶短線交易
            {
                "name": "搶短線交易",
                "actions": [
                    ("Trader01", "limit", "buy", 20, current_price - 1),
                    ("Trader02", "limit", "sell", 15, current_price + 1),
                    ("Trader03", "market", "buy", 10),
                ]
            },
            # 場景2: 大單衝擊
            {
                "name": "大單衝擊",
                "actions": [
                    ("Trader04", "limit", "buy", 100, current_price + 2),
                    ("Trader05", "limit", "sell", 80, current_price - 2),
                ]
            },
            # 場景3: 階梯式掛單
            {
                "name": "階梯式掛單",
                "actions": [
                    ("Trader06", "limit", "buy", 30, current_price - 3),
                    ("Trader07", "limit", "buy", 25, current_price - 2),
                    ("Trader08", "limit", "buy", 20, current_price - 1),
                    ("Trader09", "limit", "sell", 25, current_price + 1),
                    ("Trader10", "limit", "sell", 30, current_price + 2),
                ]
            }
        ]
        
        for scenario in trading_scenarios:
            self.log(f"🎬 執行場景: {scenario['name']}", "TRADE")
            
            for username, order_type, side, quantity, *price_args in scenario["actions"]:
                price = price_args[0] if price_args else None
                await self.place_order(username, order_type, side, quantity, price)
                await asyncio.sleep(random.uniform(0.3, 1.0))
            
            await asyncio.sleep(2)
            await self.show_market_overview()
            self.log("-" * 50, "INFO")
    
    async def simulate_market_maker(self):
        """模擬造市商行為"""
        self.log("🏦 開始造市商模擬", "MARKET")
        
        market_status = await self.get_market_status()
        current_price = market_status.get('lastPrice', 20)
        
        # 造市商在買賣兩邊同時掛單
        market_maker_orders = [
            ("Trader01", "limit", "buy", 50, current_price - 2),
            ("Trader01", "limit", "sell", 50, current_price + 2),
            ("Trader02", "limit", "buy", 30, current_price - 1),
            ("Trader02", "limit", "sell", 30, current_price + 1),
        ]
        
        for username, order_type, side, quantity, price in market_maker_orders:
            await self.place_order(username, order_type, side, quantity, price)
            await asyncio.sleep(0.5)
        
        await asyncio.sleep(3)
        await self.show_market_overview()
    
    async def simulate_call_auction(self):
        """模擬集合競價"""
        self.log("⚖️ 執行集合競價撮合", "ADMIN")
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            async with self.session.post(
                f"{BASE_URL}/api/admin/market/call-auction",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log(f"集合競價完成: {data.get('message')}", "ADMIN")
                    if data.get('auctionPrice'):
                        self.log(f"成交價: {data.get('auctionPrice')} 元", "MARKET")
                    if data.get('matchedVolume'):
                        self.log(f"成交量: {data.get('matchedVolume')} 股", "MARKET")
                else:
                    self.log(f"集合競價失敗: {resp.status}", "ERROR")
        except Exception as e:
            self.log(f"集合競價錯誤: {e}", "ERROR")
        
        await asyncio.sleep(2)
        await self.show_market_overview()
    
    async def show_leaderboard(self):
        """顯示排行榜"""
        try:
            async with self.session.get(f"{BASE_URL}/api/leaderboard") as resp:
                if resp.status == 200:
                    leaderboard = await resp.json()
                    
                    self.log("🏆 === 排行榜 ===", "MARKET")
                    for i, entry in enumerate(leaderboard[:10], 1):
                        total_value = entry.get('points', 0) + entry.get('stockValue', 0)
                        self.log(
                            f"{i:2d}. {entry.get('username', 'N/A'):10s} "
                            f"({entry.get('team', 'N/A'):6s}) "
                            f"總資產: {total_value:4d} 元 "
                            f"(點數: {entry.get('points', 0):4d} + 股票: {entry.get('stockValue', 0):4d})",
                            "MARKET"
                        )
        except Exception as e:
            self.log(f"取得排行榜錯誤: {e}", "ERROR")
    
    async def run_full_simulation(self):
        """執行完整模擬"""
        self.log("🎪 === SITCON Camp 2025 股票市場完整模擬 ===", "INFO")
        self.log("=" * 60, "INFO")
        
        # 1. 系統初始化
        self.log("🔧 階段 1: 系統初始化", "ADMIN")
        if not await self.admin_login():
            return
        
        await self.reset_system()
        await self.setup_market_hours()
        await self.setup_trading_limits()
        await self.open_market()
        
        # 2. 使用者設定
        self.log("👥 階段 2: 使用者設定", "ADMIN") 
        await self.create_test_users(10)
        await self.give_initial_points(1000)
        
        await asyncio.sleep(2)
        
        # 3. IPO 階段
        self.log("💰 階段 3: IPO 申購", "MARKET")
        await self.simulate_ipo_phase()
        
        await asyncio.sleep(3)
        
        # 4. 活躍交易
        self.log("🔥 階段 4: 活躍交易", "MARKET")
        await self.simulate_active_trading()
        
        await asyncio.sleep(3)
        
        # 5. 造市商模擬
        self.log("🏦 階段 5: 造市商模擬", "MARKET")
        await self.simulate_market_maker()
        
        await asyncio.sleep(3)
        
        # 6. 集合競價
        self.log("⚖️ 階段 6: 集合競價", "ADMIN")
        await self.simulate_call_auction()
        
        await asyncio.sleep(3)
        
        # 7. 最終統計
        self.log("📊 階段 7: 最終統計", "MARKET")
        await self.show_market_overview()
        await self.show_leaderboard()
        
        self.log("🎉 === 模擬完成 ===", "SUCCESS")
        self.log(f"總共建立了 {len(self.test_users)} 個測試使用者", "INFO")
        self.log("可以在 http://localhost:8000/docs 查看 API 文件", "INFO")
        self.log("可以在 http://localhost:8000/api/leaderboard 查看即時排行榜", "INFO")

async def main():
    """主函數"""
    try:
        async with MarketSimulator() as simulator:
            await simulator.run_full_simulation()
    except KeyboardInterrupt:
        print("\n⏹️ 模擬被使用者中斷")
    except Exception as e:
        print(f"\n❌ 模擬過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 SITCON Camp 2025 股票市場模擬器")
    print("確保後端服務運行在 http://localhost:8000")
    print("管理員密碼: admin123")
    print("-" * 50)
    
    asyncio.run(main())
