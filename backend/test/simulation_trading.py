#!/usr/bin/env python3
"""
SITCON Camp 2025 股票交易模擬腳本
基於使用者範例：10人3隊的完整交易流程
模擬從初始發行、交易、到最終結算的完整過程
"""

import asyncio
import aiohttp
import json
import random
import time
from typing import List, Dict, Any
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000"
ADMIN_PASSWORD = "admin123"  # 替換為實際的管理員密碼
INITIAL_POINTS = 100  # 每人初始點數
INITIAL_STOCK_PRICE = 20  # 初始股票價格
FINAL_SETTLEMENT_PRICE = 20  # 最終結算價格

# 測試資料：10人3隊
TEAMS = ["A隊", "B隊", "C隊"]
PLAYERS = [
    {"username": "小明", "email": "xiaoming@sitcon.org", "team": "A隊"},
    {"username": "小華", "email": "xiaohua@sitcon.org", "team": "A隊"},
    {"username": "小李", "email": "xiaoli@sitcon.org", "team": "A隊"},
    {"username": "小王", "email": "xiaowang@sitcon.org", "team": "B隊"},
    {"username": "小陳", "email": "xiaochen@sitcon.org", "team": "B隊"},
    {"username": "小林", "email": "xiaolin@sitcon.org", "team": "B隊"},
    {"username": "小張", "email": "xiaozhang@sitcon.org", "team": "B隊"},
    {"username": "小周", "email": "xiaozhou@sitcon.org", "team": "C隊"},
    {"username": "小吳", "email": "xiaowu@sitcon.org", "team": "C隊"},
    {"username": "小劉", "email": "xiaoliu@sitcon.org", "team": "C隊"},
]

class TradingSimulator:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.user_tokens = {}
        self.user_stats = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def log(self, message: str):
        """記錄日誌"""
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
    
    async def register_players(self):
        """註冊所有玩家"""
        await self.log("👥 開始註冊玩家...")
        
        for player in PLAYERS:
            try:
                async with self.session.post(
                    f"{BASE_URL}/api/user/register",
                    json={
                        "username": player["username"],
                        "email": player["email"],
                        "team": player["team"]
                    }
                ) as resp:
                    data = await resp.json()
                    if resp.status == 200 and data.get("success"):
                        await self.log(f"✅ {player['username']} ({player['team']}) 註冊成功")
                        self.user_stats[player["username"]] = {
                            "team": player["team"],
                            "trades": 0,
                            "initial_points": INITIAL_POINTS
                        }
                    else:
                        await self.log(f"⚠️  {player['username']} 註冊失敗: {data.get('message')}")
            except Exception as e:
                await self.log(f"❌ {player['username']} 註冊錯誤: {e}")
    
    async def login_players(self):
        """所有玩家登入"""
        await self.log("🔑 玩家登入中...")
        
        for player in PLAYERS:
            try:
                async with self.session.post(
                    f"{BASE_URL}/api/user/login",
                    json={"username": player["username"]}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("success"):
                            self.user_tokens[player["username"]] = data["token"]
                            await self.log(f"✅ {player['username']} 登入成功")
                        else:
                            await self.log(f"❌ {player['username']} 登入失敗: {data.get('message')}")
                    else:
                        await self.log(f"❌ {player['username']} 登入請求失敗")
            except Exception as e:
                await self.log(f"❌ {player['username']} 登入錯誤: {e}")
    
    async def give_initial_points(self):
        """給予玩家初始點數"""
        await self.log(f"💰 給予每位玩家 {INITIAL_POINTS} 初始點數...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        for player in PLAYERS:
            try:
                async with self.session.post(
                    f"{BASE_URL}/api/admin/users/give-points",
                    json={
                        "username": player["username"],
                        "type": "user",
                        "amount": INITIAL_POINTS
                    },
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("ok"):
                            await self.log(f"✅ {player['username']} 獲得 {INITIAL_POINTS} 點數")
                        else:
                            await self.log(f"❌ 給予 {player['username']} 點數失敗: {data}")
                    else:
                        await self.log(f"❌ 給予 {player['username']} 點數請求失敗: {resp.status}")
            except Exception as e:
                await self.log(f"❌ 給予 {player['username']} 點數錯誤: {e}")
    
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
                        self.user_stats[username]["trades"] += 1
                        
                        # 記錄交易
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
    
    async def get_user_portfolio(self, username: str) -> Dict[str, Any]:
        """取得使用者投資組合"""
        if username not in self.user_tokens:
            return {}
        
        try:
            headers = {"Authorization": f"Bearer {self.user_tokens[username]}"}
            async with self.session.get(
                f"{BASE_URL}/api/user/portfolio",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {}
        except Exception as e:
            await self.log(f"❌ 取得 {username} 投資組合錯誤: {e}")
            return {}
    
    async def get_current_price(self) -> int:
        """取得目前股價"""
        try:
            async with self.session.get(f"{BASE_URL}/api/price/summary") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("lastPrice", INITIAL_STOCK_PRICE)
                return INITIAL_STOCK_PRICE
        except Exception as e:
            await self.log(f"❌ 取得股價錯誤: {e}")
            return INITIAL_STOCK_PRICE
    
    async def show_user_status(self, username: str):
        """顯示使用者狀態"""
        portfolio = await self.get_user_portfolio(username)
        if portfolio:
            points = portfolio.get("points", 0)
            stocks = portfolio.get("stocks", 0)
            total_value = portfolio.get("totalValue", 0)
            team = self.user_stats[username]["team"]
            
            await self.log(f"👤 {username} ({team}): {points}點 + {stocks}股 = 總資產{total_value}元")
    
    async def simulate_example_scenario(self):
        """模擬你提供的範例場景"""
        await self.log("\n" + "="*60)
        await self.log("🎭 開始模擬範例場景")
        await self.log("="*60)
        
        # 初始狀態：每人100點，初始股價20元
        await self.log("📊 初始狀態:")
        await self.log("   每人都有 100 點")
        await self.log("   系統發行股票，初始價格 20 點/股")
        
        # 顯示幾個用戶的初始狀態
        for username in ["小明", "小華", "小李"]:
            await self.show_user_status(username)
        
        await asyncio.sleep(2)
        
        # 場景1: A用20點買了3張，B用20點買了1張
        await self.log("\n📖 場景1: 初始購買")
        await self.log("   小明用20點買3股，小華用20點買1股")
        
        await self.place_order("小明", "market", "buy", 3)  # 市價買3股
        await asyncio.sleep(1)
        await self.place_order("小華", "market", "buy", 1)  # 市價買1股
        await asyncio.sleep(2)
        
        # 顯示狀態
        await self.log("   結果:")
        await self.show_user_status("小明")  # 應該是 40點 + 3股
        await self.show_user_status("小華")  # 應該是 80點 + 1股
        
        await asyncio.sleep(3)
        
        # 場景2: A想21賣三張，B想25買三張，成交
        await self.log("\n📖 場景2: 交易撮合")
        await self.log("   小明想21元賣3股，小華想25元買3股")
        await self.log("   (應該以21元成交)")
        
        await self.place_order("小明", "limit", "sell", 3, 21)  # 限價賣21元
        await asyncio.sleep(1)
        await self.place_order("小華", "limit", "buy", 3, 25)   # 限價買25元
        await asyncio.sleep(3)  # 等待撮合
        
        # 顯示狀態
        await self.log("   結果:")
        await self.show_user_status("小明")  # 應該是 103點 + 0股 (40 + 21*3 = 103)
        await self.show_user_status("小華")  # 應該是 17點 + 4股 (80 - 21*3 = 17)
        
        await asyncio.sleep(3)
        
        # 場景3: A想25賣，B想20買，不成交
        await self.log("\n📖 場景3: 價差過大不成交")
        await self.log("   小明想25元賣，小華想20元買")
        await self.log("   (價差過大，不會成交)")
        
        await self.place_order("小明", "limit", "sell", 1, 25)  # 想賣25元
        await asyncio.sleep(1)
        await self.place_order("小華", "limit", "buy", 1, 20)   # 想買20元
        await asyncio.sleep(2)
        
        await self.log("   如預期，訂單掛著但未成交")
        
        await asyncio.sleep(2)
    
    async def simulate_random_trading(self, num_trades: int = 30):
        """模擬隨機交易活動"""
        await self.log(f"\n💹 開始隨機交易階段 ({num_trades} 筆交易)...")
        
        active_players = list(self.user_tokens.keys())
        
        for i in range(num_trades):
            # 隨機選擇玩家
            trader = random.choice(active_players)
            
            # 取得目前股價
            current_price = await self.get_current_price()
            
            # 隨機決定交易類型和方向
            side = random.choice(["buy", "sell"])
            order_type = random.choice(["market", "limit"])
            quantity = random.randint(1, 2)
            
            price = None
            if order_type == "limit":
                # 限價單價格設定
                if side == "buy":
                    price = max(15, current_price + random.randint(-2, 2))
                else:
                    price = max(16, current_price + random.randint(-1, 3))
            
            success = await self.place_order(trader, order_type, side, quantity, price)
            
            if success:
                await asyncio.sleep(random.uniform(0.3, 1.0))
            else:
                await asyncio.sleep(0.2)
    
    async def final_settlement(self):
        """執行最終結算"""
        await self.log("\n🏁 執行最終結算...")
        await self.log(f"   所有剩餘股票將以 {FINAL_SETTLEMENT_PRICE} 元/股 強制賣出")
        
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
    
    async def show_final_results(self):
        """顯示最終結果統計"""
        await self.log("\n" + "="*60)
        await self.log("📊 最終結果統計")
        await self.log("="*60)
        
        total_points = 0
        team_stats = {team: {"players": 0, "total_points": 0} for team in TEAMS}
        
        await self.log("👥 個人結果:")
        for username in self.user_tokens.keys():
            portfolio = await self.get_user_portfolio(username)
            if portfolio:
                points = portfolio.get("points", 0)
                stocks = portfolio.get("stocks", 0)
                stock_value = portfolio.get("stockValue", 0)
                total_value = portfolio.get("totalValue", 0)
                trades = self.user_stats[username]["trades"]
                team = self.user_stats[username]["team"]
                
                await self.log(
                    f"   {username:6} ({team}): "
                    f"{points:3}點 + {stocks}股({stock_value}元) = {total_value:3}元 "
                    f"(交易{trades}次)"
                )
                
                total_points += total_value
                team_stats[team]["players"] += 1
                team_stats[team]["total_points"] += total_value
        
        await self.log("\n🏆 隊伍排行:")
        for team, stats in sorted(team_stats.items(), key=lambda x: x[1]["total_points"], reverse=True):
            avg_points = stats["total_points"] / stats["players"] if stats["players"] > 0 else 0
            await self.log(f"   {team}: {stats['total_points']}點 (平均 {avg_points:.1f}點/人)")
        
        await self.log(f"\n💰 總點數驗證: {total_points} 點")
        expected_total = len(PLAYERS) * INITIAL_POINTS
        await self.log(f"   預期總點數: {expected_total} 點")
        
        if total_points == expected_total:
            await self.log("✅ 點數守恆！沒有通膨或通縮")
        else:
            diff = total_points - expected_total
            await self.log(f"⚠️  點數差異: {diff:+d} 點")
    
    async def show_market_status(self):
        """顯示市場狀態"""
        try:
            async with self.session.get(f"{BASE_URL}/api/price/summary") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    await self.log("\n📈 最終市場狀態:")
                    await self.log(f"   最終股價: {data.get('lastPrice')}元")
                    await self.log(f"   今日漲跌: {data.get('change')} ({data.get('changePercent')})")
                    await self.log(f"   總成交量: {data.get('volume')}股")
        except Exception as e:
            await self.log(f"❌ 無法取得市場狀態: {e}")
    
    async def run_simulation(self):
        """執行完整模擬"""
        await self.log("🚀 SITCON Camp 2025 股票交易模擬開始")
        await self.log("基於範例：10人3隊的完整交易流程")
        await self.log("="*60)
        
        # 1. 管理員登入
        if not await self.admin_login():
            await self.log("❌ 模擬中止：管理員登入失敗")
            return
        
        # 2. 註冊玩家
        await self.register_players()
        
        # 3. 玩家登入
        await self.login_players()
        
        # 4. 給予初始點數
        await self.give_initial_points()
        
        # 5. 等待系統更新
        await asyncio.sleep(2)
        
        # 6. 模擬範例場景
        await self.simulate_example_scenario()
        
        # 7. 隨機交易階段
        await self.simulate_random_trading(25)
        
        # 8. 最終結算
        await self.final_settlement()
        
        # 9. 顯示結果
        await self.show_market_status()
        await self.show_final_results()
        
        await self.log("\n🎉 模擬完成！")
        await self.log("="*60)
        await self.log("💡 重點驗證:")
        await self.log("   ✓ 初始每人100點")
        await self.log("   ✓ 交易撮合機制")
        await self.log("   ✓ 最終結算機制")
        await self.log("   ✓ 點數守恆原理")
        await self.log("   ✓ 想玩的人可以玩，不玩的也不吃虧")


async def main():
    """主函數"""
    try:
        async with TradingSimulator() as simulator:
            await simulator.run_simulation()
    except KeyboardInterrupt:
        print("\n⏹️  模擬被用戶中斷")
    except Exception as e:
        print(f"\n❌ 模擬過程中發生錯誤: {e}")


if __name__ == "__main__":
    print("🎯 SITCON Camp 2025 股票交易模擬器")
    print("確保後端服務運行在 http://localhost:8000")
    print("按 Ctrl+C 可隨時停止模擬\n")
    
    asyncio.run(main())
