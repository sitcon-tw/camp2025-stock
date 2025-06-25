#!/usr/bin/env python3
"""
SITCON Camp 2025 股票交易系統測試腳本
註冊10個玩家，分3個隊伍，執行100筆交易測試
"""

import asyncio
import aiohttp
import json
import random
import time
from typing import List, Dict, Any
from datetime import datetime

# 設定
BASE_URL = "http://localhost:8000"
ADMIN_PASSWORD = "admin123"  # 替換為實際的管理員密碼

# 測試資料
TEAMS = ["紅隊", "藍隊", "綠隊"]
PLAYERS = [
    {"username": f"player_{i+1:02d}", "email": f"player{i+1:02d}@sitcon.org", "team": TEAMS[i % 3]}
    for i in range(10)
]

class TradingTestRunner:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.user_tokens = {}
        self.user_stats = {}
        self.trade_count = 0
        
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
        await self.log("🎮 開始註冊玩家...")
        
        for player in PLAYERS:
            try:
                async with self.session.post(
                    f"{BASE_URL}/api/user/register",
                    json=player
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("success"):
                            await self.log(f"✅ 註冊成功: {player['username']} ({player['team']})")
                            
                            # 初始化玩家統計
                            self.user_stats[player['username']] = {
                                "team": player['team'],
                                "points": 100,
                                "stocks": 0,
                                "trades": 0
                            }
                        else:
                            await self.log(f"❌ 註冊失敗: {player['username']} - {data.get('message')}")
                    else:
                        await self.log(f"❌ 註冊請求失敗: {player['username']} - {resp.status}")
            except Exception as e:
                await self.log(f"❌ 註冊錯誤: {player['username']} - {e}")
        
        await asyncio.sleep(1)  # 等待註冊完成
    
    async def login_players(self):
        """所有玩家登入"""
        await self.log("🔑 開始玩家登入...")
        
        for player in PLAYERS:
            try:
                async with self.session.post(
                    f"{BASE_URL}/api/user/login",
                    json={"username": player['username']}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("success"):
                            token = data["token"]
                            self.user_tokens[player['username']] = token
                            await self.log(f"✅ 登入成功: {player['username']}，token={token}")
                        else:
                            await self.log(f"❌ 登入失敗: {player['username']} - {data.get('message')}")
                    else:
                        await self.log(f"❌ 登入請求失敗: {player['username']} - {resp.status}")
            except Exception as e:
                await self.log(f"❌ 登入錯誤: {player['username']} - {e}")
        
        await asyncio.sleep(1)
    
    async def get_current_price(self) -> int:
        """取得目前股價"""
        try:
            async with self.session.get(f"{BASE_URL}/api/price/current") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("price", 20)
                return 20
        except:
            return 20
    
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
                        self.trade_count += 1
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
        except:
            return {}
    
    async def simulate_scenario_trading(self):
        """模擬您範例中的具體交易場景"""
        await self.log("🎭 開始模擬範例交易場景...")
        
        # 場景 1: A 買 3 張，B 買 1 張 (各20元)
        await self.log("📖 場景1: 初始購買")
        await self.place_order("player_01", "market", "buy", 3)  # A
        await asyncio.sleep(0.5)
        await self.place_order("player_02", "market", "buy", 1)  # B
        await asyncio.sleep(1)
        
        # 場景 2: A 想21元賣3張，B 想25元買3張 (應該21元成交)
        await self.log("📖 場景2: A 賣21元，B 買25元")
        await self.place_order("player_01", "limit", "sell", 3, 21)  # A 賣
        await asyncio.sleep(0.5)
        await self.place_order("player_02", "limit", "buy", 3, 25)   # B 買
        await asyncio.sleep(2)  # 等待撮合
        
        # 場景 3: A 想25元賣，B 想20元買 (不會成交，價差太大)
        await self.log("📖 場景3: A 賣25元，B 買20元 (應不成交)")
        await self.place_order("player_01", "limit", "sell", 1, 25)  # A 賣
        await asyncio.sleep(0.5)
        await self.place_order("player_02", "limit", "buy", 1, 20)   # B 買
        await asyncio.sleep(2)
        
        # 新增一些其他玩家的交易來創造市場活力
        await self.log("📖 場景4: 其他玩家加入交易")
        await self.place_order("player_03", "limit", "buy", 2, 22)   # C 買22元
        await asyncio.sleep(0.5)
        await self.place_order("player_04", "limit", "sell", 1, 23)  # D 賣23元
        await asyncio.sleep(0.5)
        await self.place_order("player_05", "market", "buy", 1)      # E 市價買
        await asyncio.sleep(2)
    
    async def simulate_active_trading(self, num_trades: int = 80):
        """模擬活躍交易階段"""
        await self.log(f"💹 開始活躍交易階段 ({num_trades} 筆交易)...")
        
        active_players = list(self.user_tokens.keys())
        
        for i in range(num_trades):
            if self.trade_count >= 100:
                break
                
            # 隨機選擇玩家
            trader = random.choice(active_players)
            
            # 取得目前股價
            current_price = await self.get_current_price()
            
            # 隨機決定交易類型和方向
            side = random.choice(["buy", "sell"])
            order_type = random.choice(["market", "limit"])
            quantity = random.randint(1, 3)
            
            price = None
            if order_type == "limit":
                # 限價單價格設定
                if side == "buy":
                    price = max(15, current_price + random.randint(-3, 3))
                else:
                    price = max(16, current_price + random.randint(-2, 4))
            
            success = await self.place_order(trader, order_type, side, quantity, price)
            
            if success:
                await asyncio.sleep(random.uniform(0.1, 0.5))
            else:
                await asyncio.sleep(0.1)

    async def simulate_transfers(self):
        """模擬玩家間點數轉帳"""
        await self.log("🔄 開始模擬點數轉帳...")
        usernames = list(self.user_tokens.keys())
        for _ in range(10):
            sender = random.choice(usernames)
            receiver = random.choice([u for u in usernames if u != sender])
            amount = random.randint(1, 10)
            
            try:
                headers = {"Authorization": f"Bearer {self.user_tokens[sender]}"}
                async with self.session.post(
                    f"{BASE_URL}/api/user/transfer",
                    json={"to_username": receiver, "amount": amount, "note": "測試轉帳"},
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("ok") or data.get("success"):
                            await self.log(f"💸 {sender} 轉帳 {amount} 點給 {receiver} 成功，回傳: {data.get('message')}")
                        else:
                            await self.log(f"❌ {sender} 轉帳失敗: {data.get('message')}")
                    else:
                        await self.log(f"❌ {sender} 轉帳請求失敗: {resp.status}")
            except Exception as e:
                await self.log(f"❌ {sender} 轉帳錯誤: {e}")
            await asyncio.sleep(0.3)
    
    async def simulate_final_settlement(self):
        """模擬最終結算（使用後端 API）"""
        await self.log("🏁 開始最終結算 (透過 API)...")

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
            await self.log(f"❌ 傳送最終結算請求失敗: {e}")
    
    async def show_final_results(self):
        """顯示最終結果"""
        await self.log("📊 最終結果統計:")
        await self.log("=" * 60)
        
        total_points = 0
        team_stats = {team: {"players": 0, "total_points": 0} for team in TEAMS}
        
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
                    f"👤 {username:10} ({team:2}): "
                    f"{points:3}點 + {stocks}股({stock_value}元) = {total_value}元 "
                    f"(交易{trades}次)"
                )
                
                total_points += total_value
                team_stats[team]["players"] += 1
                team_stats[team]["total_points"] += total_value
        
        await self.log("=" * 60)
        await self.log(f"💰 總點數: {total_points} (應為 1000)")
        await self.log(f"📈 總交易數: {self.trade_count}")
        
        await self.log("\n🏆 隊伍排行:")
        for team, stats in sorted(team_stats.items(), key=lambda x: x[1]["total_points"], reverse=True):
            avg_points = stats["total_points"] / stats["players"] if stats["players"] > 0 else 0
            await self.log(f"  {team}: {stats['total_points']}點 (平均 {avg_points:.1f}點/人)")
    
    async def show_market_status(self):
        """顯示市場狀態"""
        try:
            async with self.session.get(f"{BASE_URL}/api/price/summary") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    await self.log("📈 市場狀態:")
                    await self.log(f"  目前股價: {data.get('lastPrice')}元")
                    await self.log(f"  今日漲跌: {data.get('change')} ({data.get('changePercent')})")
                    await self.log(f"  成交量: {data.get('volume')}")
        except Exception as e:
            await self.log(f"❌ 無法取得市場狀態: {e}")
    
    async def run_full_test(self):
        """執行完整測試"""
        await self.log("🎯 開始 SITCON Camp 2025 股票交易測試")
        await self.log("=" * 60)
        
        # 1. 管理員登入
        if not await self.admin_login():
            await self.log("❌ 測試中止：管理員登入失敗")
            return
        
        # 2. 註冊玩家
        await self.register_players()
        
        # 3. 玩家登入
        await self.login_players()
        
        # 4. 顯示初始狀態
        await self.log(f"\n👥 成功註冊 {len(self.user_tokens)} 個玩家")
        for team in TEAMS:
            count = sum(1 for stats in self.user_stats.values() if stats["team"] == team)
            await self.log(f"  {team}: {count} 人")
        
        # 5. 模擬範例場景
        await self.simulate_scenario_trading()
        
        # 6. 活躍交易
        await self.simulate_active_trading(70)  # 減少到70筆，因為前面已有交易

        # 7. 模擬點數轉帳
        await self.simulate_transfers()

        # 8. 最終結算
        await self.simulate_final_settlement()
        
        # 9. 顯示結果
        await self.show_market_status()
        await self.show_final_results()
        
        await self.log("\n🎉 測試完成！")

async def main():
    """主函數"""
    try:
        async with TradingTestRunner() as runner:
            await runner.run_full_test()
    except KeyboardInterrupt:
        print("\n⏹️  測試被使用者中斷")
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    # 執行測試
    print("🚀 SITCON Camp 2025 股票交易系統測試腳本")
    print("確保後端服務運行在 http://localhost:8000")
    print("按 Ctrl+C 可隨時停止測試\n")
    
    asyncio.run(main())