#!/usr/bin/env python3
"""
股票交易資料生成器
創建100筆交易資料來測試API和填充資料庫
"""

import requests
import json
import random
import time
from datetime import datetime
from typing import List, Dict

BASE_URL = "http://localhost:8000"

class TradingDataGenerator:
    def __init__(self):
        self.base_url = BASE_URL
        self.users = []
        self.tokens = {}
        
    def create_users(self, count: int = 10) -> bool:
        """創建測試用戶"""
        print(f"📝 創建 {count} 個測試用戶...")
        
        teams = ["火箭隊", "閃電隊", "雷神隊", "極速隊", "無敵隊"]
        
        for i in range(count):
            username = f"trader_{i+1:03d}"
            user_data = {
                "username": username,
                "email": f"trader{i+1}@example.com",
                "team": random.choice(teams)
            }
            
            try:
                # 註冊用戶
                response = requests.post(
                    f"{self.base_url}/api/user/register",
                    json=user_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result["success"]:
                        print(f"✅ 用戶 {username} 註冊成功")
                        self.users.append(username)
                    else:
                        if "已存在" in result['message']:
                            print(f"⚠️  用戶 {username} 已存在，跳過")
                            self.users.append(username)
                        else:
                            print(f"❌ 用戶 {username} 註冊失敗: {result['message']}")
                else:
                    print(f"❌ 用戶 {username} 註冊請求失敗: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ 創建用戶 {username} 異常: {e}")
                
            # 稍微延遲避免過於頻繁的請求
            time.sleep(0.1)
        
        return len(self.users) > 0
    
    def login_users(self) -> bool:
        """為所有用戶登入並獲取token"""
        print(f"🔐 為 {len(self.users)} 個用戶進行登入...")
        
        success_count = 0
        for username in self.users:
            try:
                login_data = {"username": username}
                response = requests.post(
                    f"{self.base_url}/api/user/login",
                    json=login_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result["success"]:
                        self.tokens[username] = result["token"]
                        success_count += 1
                        print(f"✅ 用戶 {username} 登入成功")
                    else:
                        print(f"❌ 用戶 {username} 登入失敗: {result['message']}")
                else:
                    print(f"❌ 用戶 {username} 登入請求失敗: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ 用戶 {username} 登入異常: {e}")
                
            time.sleep(0.1)
        
        print(f"✅ 成功登入 {success_count}/{len(self.users)} 個用戶")
        return success_count > 0
    
    def get_current_price(self) -> float:
        """獲取當前股價"""
        try:
            response = requests.get(f"{self.base_url}/api/price/summary")
            if response.status_code == 200:
                data = response.json()
                return data.get("lastPrice", 20.0)
        except:
            pass
        return 20.0
    
    def generate_realistic_price(self, base_price: float) -> float:
        """生成合理的交易價格"""
        # 在基準價格的 ±5% 範圍內生成價格
        variation = random.uniform(-0.05, 0.05)
        price = base_price * (1 + variation)
        return round(price, 2)
    
    def create_trades(self, count: int = 100) -> int:
        """創建指定數量的交易"""
        print(f"📈 開始創建 {count} 筆交易...")
        
        if not self.tokens:
            print("❌ 沒有可用的用戶token，無法進行交易")
            return 0
        
        successful_trades = 0
        current_price = self.get_current_price()
        print(f"💰 當前股價: ${current_price}")
        
        # 交易類型配比：70%市價單，30%限價單
        order_types = ["market"] * 70 + ["limit"] * 30
        # 買賣方向配比：60%買入，40%賣出
        sides = ["buy"] * 60 + ["sell"] * 40
        
        for i in range(count):
            # 隨機選擇用戶
            username = random.choice(list(self.tokens.keys()))
            token = self.tokens[username]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 隨機選擇交易參數
            order_type = random.choice(order_types)
            side = random.choice(sides)
            quantity = random.randint(1, 10)  # 1-10股
            
            # 構建訂單
            order_data = {
                "order_type": order_type,
                "side": side,
                "quantity": quantity
            }
            
            # 如果是限價單，設定價格
            if order_type == "limit":
                if side == "buy":
                    # 買單價格稍低於當前價
                    price = self.generate_realistic_price(current_price * 0.98)
                else:
                    # 賣單價格稍高於當前價
                    price = self.generate_realistic_price(current_price * 1.02)
                order_data["price"] = price
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/user/stock/order",
                    json=order_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result["success"]:
                        successful_trades += 1
                        order_info = f"{side} {quantity}股"
                        if order_type == "limit":
                            order_info += f" @${order_data['price']}"
                        
                        print(f"✅ [{i+1:3d}] {username}: {order_info} - {result['message']}")
                        
                        # 如果有成交價格，更新當前價格參考
                        if result.get("executed_price"):
                            current_price = result["executed_price"]
                    else:
                        print(f"⚠️  [{i+1:3d}] {username}: 交易失敗 - {result['message']}")
                else:
                    print(f"❌ [{i+1:3d}] {username}: 請求失敗 - {response.status_code}")
                    
            except Exception as e:
                print(f"❌ [{i+1:3d}] {username}: 交易異常 - {e}")
            
            # 隨機延遲，模擬真實交易節奏
            time.sleep(random.uniform(0.1, 0.5))
        
        return successful_trades
    
    def show_market_summary(self):
        """顯示市場摘要"""
        print("\n📊 市場摘要:")
        
        try:
            # 獲取價格摘要
            response = requests.get(f"{self.base_url}/api/price/summary")
            if response.status_code == 200:
                summary = response.json()
                print(f"   💰 當前價格: ${summary['lastPrice']}")
                print(f"   📈 漲跌幅: {summary['changePercent']}")
                print(f"   📊 成交量: {summary['volume']}")
                print(f"   🔼 最高價: ${summary['high']}")
                print(f"   🔽 最低價: ${summary['low']}")
        except:
            print("   ❌ 無法獲取價格摘要")
        
        try:
            # 獲取最近交易
            response = requests.get(f"{self.base_url}/api/price/trades?limit=10")
            if response.status_code == 200:
                trades = response.json()
                print(f"   📝 最近交易: {len(trades)} 筆")
                for i, trade in enumerate(trades[:5]):
                    timestamp = datetime.fromisoformat(trade['timestamp'].replace('Z', '+00:00'))
                    time_str = timestamp.strftime('%H:%M:%S')
                    print(f"      {i+1}. {time_str} - ${trade['price']} x{trade['quantity']}")
        except:
            print("   ❌ 無法獲取交易記錄")
        
        try:
            # 獲取五檔報價
            response = requests.get(f"{self.base_url}/api/price/depth")
            if response.status_code == 200:
                depth = response.json()
                print(f"   📋 買盤: {len(depth['buy'])} 檔")
                print(f"   📋 賣盤: {len(depth['sell'])} 檔")
        except:
            print("   ❌ 無法獲取五檔報價")
    
    def give_initial_points(self) -> bool:
        """給所有用戶初始點數"""
        print("💰 給用戶添加初始點數...")
        
        # 先嘗試獲取管理員 token
        admin_token = self.get_admin_token()
        if not admin_token:
            print("❌ 無法獲取管理員權限，跳過添加點數")
            return False
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        success_count = 0
        
        for username in self.users:
            try:
                give_points_data = {
                    "target_type": "user",
                    "target": username,
                    "points": 5000,  # 給每個用戶 5000 點數
                    "note": "交易測試初始資金"
                }
                
                response = requests.post(
                    f"{self.base_url}/api/admin/users/give-points",
                    json=give_points_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result["success"]:
                        success_count += 1
                        print(f"✅ 用戶 {username} 獲得 5000 點數")
                    else:
                        print(f"❌ 給用戶 {username} 添加點數失敗: {result['message']}")
                else:
                    print(f"❌ 給用戶 {username} 添加點數請求失敗: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ 給用戶 {username} 添加點數異常: {e}")
                
            time.sleep(0.1)
        
        print(f"✅ 成功給 {success_count}/{len(self.users)} 個用戶添加點數")
        return success_count > 0
    
    def get_admin_token(self) -> str:
        """獲取管理員 token"""
        try:
            login_data = {"password": "admin123"}  # 使用預設管理員密碼
            response = requests.post(
                f"{self.base_url}/api/admin/login",
                json=login_data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    return result["token"]
        except Exception as e:
            print(f"管理員登入失敗: {e}")
        
        return None

def main():
    """主函數"""
    print("🚀 股票交易資料生成器啟動")
    print("=" * 50)
    
    generator = TradingDataGenerator()
    
    # 1. 創建用戶
    if not generator.create_users(10):
        print("❌ 創建用戶失敗，退出程序")
        return
    
    print("\n" + "=" * 50)
    
    # 2. 用戶登入
    if not generator.login_users():
        print("❌ 用戶登入失敗，退出程序")
        return
    
    print("\n" + "=" * 50)
    
    # 3. 生成交易
    success_count = generator.create_trades(100)
    
    print("\n" + "=" * 50)
    print(f"🎉 交易生成完成!")
    print(f"   ✅ 成功創建: {success_count}/100 筆交易")
    
    # 4. 顯示市場摘要
    generator.show_market_summary()
    
    print("\n" + "=" * 50)
    print("✨ 資料生成完成，你可以在前端頁面查看結果！")

if __name__ == "__main__":
    main()
