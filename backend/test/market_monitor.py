#!/usr/bin/env python3
"""
即時市場監控腳本
持續監控股票市場狀態，包含價格變動、委託簿、成交記錄等
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
from typing import Dict, List

BASE_URL = "http://localhost:8000"

class MarketMonitor:
    def __init__(self):
        self.session = None
        self.previous_price = None
        self.monitoring = True
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def clear_screen(self):
        """清除螢幕"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def format_price_change(self, current_price: int, previous_price: int = None) -> str:
        """格式化價格變動顯示"""
        if previous_price is None:
            return f"{current_price} 元"
        
        if current_price > previous_price:
            return f"🔺 {current_price} 元 (+{current_price - previous_price})"
        elif current_price < previous_price:
            return f"🔻 {current_price} 元 ({current_price - previous_price})"
        else:
            return f"➡️ {current_price} 元 (無變動)"
    
    async def get_market_data(self) -> Dict:
        """取得市場資料"""
        try:
            async with self.session.get(f"{BASE_URL}/api/price/summary") as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            pass
        return {}
    
    async def get_depth_data(self) -> Dict:
        """取得委託簿資料"""
        try:
            async with self.session.get(f"{BASE_URL}/api/price/depth") as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            pass
        return {}
    
    async def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """取得最近成交記錄"""
        try:
            async with self.session.get(f"{BASE_URL}/api/price/trades?limit={limit}") as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            pass
        return []
    
    async def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """取得排行榜"""
        try:
            async with self.session.get(f"{BASE_URL}/api/leaderboard") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data[:limit]
        except Exception:
            pass
        return []
    
    async def get_market_status(self) -> Dict:
        """取得市場開放狀態"""
        try:
            async with self.session.get(f"{BASE_URL}/api/status") as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            pass
        return {}
    
    def display_header(self):
        """顯示標題"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("=" * 80)
        print(f"📊 SITCON Camp 2025 股票市場即時監控 - {now}")
        print("=" * 80)
    
    def display_market_summary(self, market_data: Dict):
        """顯示市場摘要"""
        if not market_data:
            print("❌ 無法取得市場資料")
            return
        
        current_price = market_data.get('lastPrice', 0)
        change = market_data.get('change', '+0')
        change_percent = market_data.get('changePercent', '+0.0%')
        volume = market_data.get('volume', 0)
        high = market_data.get('high', 0)
        low = market_data.get('low', 0)
        
        print(f"💰 目前股價: {self.format_price_change(current_price, self.previous_price)}")
        print(f"📈 漲跌幅度: {change} ({change_percent})")
        print(f"📊 成交量: {volume:,} 股")
        print(f"🔼 最高價: {high} 元")
        print(f"🔽 最低價: {low} 元")
        
        self.previous_price = current_price
    
    def display_order_book(self, depth_data: Dict):
        """顯示委託簿"""
        if not depth_data:
            print("❌ 無法取得委託簿資料")
            return
        
        print("\n📋 === 五檔委託簿 ===")
        
        # 賣方掛單
        sell_orders = depth_data.get('sell', [])
        if sell_orders:
            print("🔴 賣方:")
            for i, order in enumerate(reversed(sell_orders[-5:])):
                level = len(sell_orders) - i
                print(f"  賣{level}: {order['price']:>4} 元 x {order['quantity']:>6,} 股")
        else:
            print("🔴 賣方: 無掛單")
        
        print("     ─────────────────")
        
        # 買方掛單
        buy_orders = depth_data.get('buy', [])
        if buy_orders:
            print("🟢 買方:")
            for i, order in enumerate(buy_orders[:5]):
                print(f"  買{i+1}: {order['price']:>4} 元 x {order['quantity']:>6,} 股")
        else:
            print("🟢 買方: 無掛單")
    
    def display_recent_trades(self, trades: List[Dict]):
        """顯示最近成交"""
        if not trades:
            print("\n❌ 無法取得成交記錄")
            return
        
        print(f"\n🎯 === 最近 {len(trades)} 筆成交 ===")
        print(f"{'時間':>8} {'價格':>6} {'數量':>8}")
        print("-" * 30)
        
        for trade in trades[:10]:
            trade_time = trade.get('timestamp', '')
            if trade_time:
                # 只顯示時間部分
                time_part = trade_time.split('T')[1][:8] if 'T' in trade_time else trade_time[:8]
            else:
                time_part = 'N/A'
            
            price = trade.get('price', 0)
            quantity = trade.get('quantity', 0)
            
            print(f"{time_part:>8} {price:>4} 元 {quantity:>6,} 股")
    
    def display_leaderboard(self, leaderboard: List[Dict]):
        """顯示排行榜"""
        if not leaderboard:
            print("\n❌ 無法取得排行榜")
            return
        
        print(f"\n🏆 === 排行榜前 {len(leaderboard)} 名 ===")
        print(f"{'排名':<4} {'用戶':<12} {'隊伍':<8} {'總資產':<8}")
        print("-" * 40)
        
        for i, entry in enumerate(leaderboard, 1):
            username = entry.get('username', 'N/A')[:12]
            team = entry.get('team', 'N/A')[:8]
            points = entry.get('points', 0)
            stock_value = entry.get('stockValue', 0)
            total = points + stock_value
            
            print(f"{i:<4} {username:<12} {team:<8} {total:>6,} 元")
    
    def display_market_status(self, status_data: Dict):
        """顯示市場狀態"""
        if not status_data:
            return
        
        is_open = status_data.get('isOpen', False)
        current_time = status_data.get('currentTime', '')
        
        status_icon = "🟢 開盤中" if is_open else "🔴 休市中"
        print(f"\n📅 市場狀態: {status_icon}")
        
        if current_time:
            time_part = current_time.split('T')[1][:8] if 'T' in current_time else current_time
            print(f"⏰ 系統時間: {time_part}")
    
    def display_controls(self):
        """顯示控制說明"""
        print("\n" + "=" * 80)
        print("⌨️  控制說明: Ctrl+C 退出監控")
        print("🔄 自動更新: 每5秒重新整理")
        print("=" * 80)
    
    async def monitor_loop(self, refresh_interval: int = 5):
        """監控循環"""
        try:
            while self.monitoring:
                # 清除螢幕
                self.clear_screen()
                
                # 顯示標題
                self.display_header()
                
                # 並行取得所有資料
                market_data, depth_data, trades, leaderboard, status_data = await asyncio.gather(
                    self.get_market_data(),
                    self.get_depth_data(),
                    self.get_recent_trades(10),
                    self.get_leaderboard(10),
                    self.get_market_status(),
                    return_exceptions=True
                )
                
                # 處理可能的異常
                market_data = market_data if isinstance(market_data, dict) else {}
                depth_data = depth_data if isinstance(depth_data, dict) else {}
                trades = trades if isinstance(trades, list) else []
                leaderboard = leaderboard if isinstance(leaderboard, list) else []
                status_data = status_data if isinstance(status_data, dict) else {}
                
                # 顯示各區塊資料
                self.display_market_status(status_data)
                self.display_market_summary(market_data)
                self.display_order_book(depth_data)
                self.display_recent_trades(trades)
                self.display_leaderboard(leaderboard)
                self.display_controls()
                
                # 等待下次更新
                await asyncio.sleep(refresh_interval)
                
        except KeyboardInterrupt:
            self.monitoring = False
            print("\n👋 監控已停止")
        except Exception as e:
            print(f"\n❌ 監控錯誤: {e}")

async def main():
    """主函數"""
    import sys
    
    refresh_interval = 5
    if len(sys.argv) > 1:
        try:
            refresh_interval = int(sys.argv[1])
            if refresh_interval < 1:
                refresh_interval = 1
        except ValueError:
            print("更新間隔必須是正整數（秒）")
            return
    
    print("🚀 啟動市場監控...")
    print(f"🔄 更新間隔: {refresh_interval} 秒")
    print("⏳ 正在連接到市場...")
    
    try:
        async with MarketMonitor() as monitor:
            await monitor.monitor_loop(refresh_interval)
    except KeyboardInterrupt:
        print("\n⏹️ 監控被用戶中斷")
    except Exception as e:
        print(f"\n❌ 監控過程中發生錯誤: {e}")

if __name__ == "__main__":
    print("📺 SITCON Camp 2025 市場監控器")
    print("用法: python market_monitor.py [更新間隔秒數]")
    print("範例: python market_monitor.py 3")
    print("確保後端服務運行在 http://localhost:8000")
    print("-" * 50)
    
    asyncio.run(main())
