#!/usr/bin/env python3
"""
股票價格變化產生器
直接向資料庫插入不同價格的交易記錄來模擬真實市場波動
"""

import asyncio
import random
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import uuid

class PriceVariationGenerator:
    def __init__(self):
        self.client = None
        self.db = None
        
    async def connect_to_database(self):
        """連線到 MongoDB"""
        try:
            self.client = AsyncIOMotorClient("mongodb://localhost:27017")
            self.db = self.client["sitcon_camp_2025"]
            print("✅ 成功連線到資料庫")
            return True
        except Exception as e:
            print(f"❌ 資料庫連線失敗: {e}")
            return False
    
    async def close_database(self):
        """關閉資料庫連線"""
        if self.client:
            self.client.close()
    
    async def generate_realistic_price_series(self, base_price: float = 20.0, count: int = 50) -> list:
        """產生真實的價格序列"""
        prices = [base_price]
        current_price = base_price
        
        for i in range(count - 1):
            # 隨機漂移：70% 小幅波動，20% 中幅波動，10% 大幅波動
            rand = random.random()
            if rand < 0.7:
                # 小幅波動 ±1%
                change_percent = random.uniform(-0.01, 0.01)
            elif rand < 0.9:
                # 中幅波動 ±3%
                change_percent = random.uniform(-0.03, 0.03)
            else:
                # 大幅波動 ±5%
                change_percent = random.uniform(-0.05, 0.05)
            
            # 增加趨勢性：讓價格有一定的連續性
            if i > 0:
                previous_change = (prices[-1] - prices[-2]) / prices[-2] if len(prices) >= 2 else 0
                # 60% 機率延續前一次的趨勢方向
                if random.random() < 0.6 and abs(previous_change) > 0.001:
                    change_percent = abs(change_percent) * (1 if previous_change > 0 else -1) * 0.5
            
            current_price = current_price * (1 + change_percent)
            # 確保價格不會低於 10 或高於 30
            current_price = max(10.0, min(30.0, current_price))
            current_price = round(current_price, 2)
            prices.append(current_price)
        
        return prices
    
    async def get_existing_users(self) -> list:
        """獲取現有使用者列表"""
        cursor = self.db.users.find({}, {"username": 1})
        users = []
        async for user in cursor:
            users.append(user["username"])
        return users
    
    async def create_realistic_trades(self, count: int = 50):
        """建立具有真實價格變化的交易記錄"""
        print(f"📈 產生 {count} 筆具有價格變化的交易記錄...")
        
        # 獲取使用者列表
        users = await self.get_existing_users()
        if not users:
            print("❌ 沒有找到使用者，請先運行 generate_trading_data.py")
            return
        
        print(f"📋 找到 {len(users)} 個使用者")
        
        # 產生價格序列
        prices = await self.generate_realistic_price_series(20.0, count)
        print(f"💰 價格範圍: ${min(prices):.2f} - ${max(prices):.2f}")
        
        # 產生時間序列（過去24小時）
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(hours=24)
        time_intervals = []
        for i in range(count):
            trade_time = start_time + timedelta(hours=24 * i / count)
            time_intervals.append(trade_time)
        
        trades_created = 0
        
        for i in range(count):
            # 隨機選擇使用者
            username = random.choice(users)
            price = prices[i]
            quantity = random.randint(1, 10)
            side = random.choice(["buy", "sell"])
            trade_time = time_intervals[i]
            
            # 建立交易記錄
            trade_record = {
                "_id": str(uuid.uuid4()),
                "username": username,
                "order_type": "market",
                "side": side,
                "quantity": quantity,
                "price": price,
                "stock_amount": quantity if side == "buy" else -quantity,
                "points_amount": -price * quantity if side == "buy" else price * quantity,
                "status": "completed",
                "created_at": trade_time,
                "completed_at": trade_time
            }
            
            try:
                # 插入交易記錄
                await self.db.stock_orders.insert_one(trade_record)
                
                # 同時更新使用者的股票和點數
                user_update = {}
                if side == "buy":
                    user_update = {
                        "$inc": {
                            "stock_amount": quantity,
                            "points": -price * quantity
                        }
                    }
                else:
                    user_update = {
                        "$inc": {
                            "stock_amount": -quantity,
                            "points": price * quantity
                        }
                    }
                
                await self.db.users.update_one(
                    {"username": username},
                    user_update
                )
                
                trades_created += 1
                action = "買入" if side == "buy" else "賣出"
                print(f"✅ [{i+1:2d}] {username}: {action} {quantity}股 @${price:.2f}")
                
            except Exception as e:
                print(f"❌ [{i+1:2d}] 建立交易失敗: {e}")
        
        print(f"\n🎉 成功建立 {trades_created}/{count} 筆價格變化交易")
        
        # 顯示價格摘要
        print(f"\n📊 價格變化摘要:")
        print(f"   起始價格: ${prices[0]:.2f}")
        print(f"   最終價格: ${prices[-1]:.2f}")
        print(f"   漲跌: ${prices[-1] - prices[0]:+.2f} ({(prices[-1] - prices[0]) / prices[0] * 100:+.1f}%)")
        print(f"   最高價: ${max(prices):.2f}")
        print(f"   最低價: ${min(prices):.2f}")

async def main():
    """主函數"""
    print("📈 股票價格變化產生器啟動")
    print("=" * 50)
    
    generator = PriceVariationGenerator()
    
    # 連線資料庫
    if not await generator.connect_to_database():
        return
    
    try:
        # 產生價格變化交易
        await generator.create_realistic_trades(50)
        
        print("\n" + "=" * 50)
        print("✨ 價格變化產生完成！")
        print("🔄 請重新載入前端頁面查看價格變化")
        
    finally:
        await generator.close_database()

if __name__ == "__main__":
    asyncio.run(main())
