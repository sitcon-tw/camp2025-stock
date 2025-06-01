#!/usr/bin/env python3
"""
股票交易資料產生器
創建多個使用者並產生 100 筆交易資料
"""

import requests
import json
import sys
import random
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

# 模擬使用者資料
MOCK_USERS = [
    {"username": "trader_alice", "email": "alice@example.com", "team": "Team Alpha"},
    {"username": "trader_bob", "email": "bob@example.com", "team": "Team Beta"},
    {"username": "trader_charlie", "email": "charlie@example.com", "team": "Team Gamma"},
    {"username": "trader_diana", "email": "diana@example.com", "team": "Team Delta"},
    {"username": "trader_eve", "email": "eve@example.com", "team": "Team Epsilon"},
    {"username": "trader_frank", "email": "frank@example.com", "team": "Team Zeta"},
    {"username": "trader_grace", "email": "grace@example.com", "team": "Team Eta"},
    {"username": "trader_henry", "email": "henry@example.com", "team": "Team Theta"},
    {"username": "trader_ivy", "email": "ivy@example.com", "team": "Team Iota"},
    {"username": "trader_jack", "email": "jack@example.com", "team": "Team Kappa"},
]

class TradingDataGenerator:
    def __init__(self):
        self.registered_users = []
        self.user_tokens = {}
        self.trade_count = 0
        self.admin_token = None
        
    def get_admin_token(self):
        """獲取管理員 token"""
        try:
            response = requests.post(
                f"{BASE_URL}/api/admin/login",
                json={"password": "admin123"}  # 預設管理員密碼
            )
            if response.status_code == 200:
                result = response.json()
                if "token" in result:
                    self.admin_token = result["token"]
                    print("✅ 管理員登入成功")
                    return True
        except Exception as e:
            print(f"⚠️  管理員登入失敗: {e}")
        return False
        
    def register_user(self, user_data):
        """註冊使用者"""
        try:
            response = requests.post(
                f"{BASE_URL}/api/user/register",
                json=user_data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"✅ 使用者 {user_data['username']} 註冊成功")
                    self.registered_users.append(user_data)
                    return True
                else:
                    if "已存在" in result.get('message', ''):
                        print(f"⚠️  使用者 {user_data['username']} 已存在，跳過")
                        self.registered_users.append(user_data)
                        return True
                    else:
                        print(f"❌ 使用者 {user_data['username']} 註冊失敗: {result.get('message')}")
                        return False
        except Exception as e:
            print(f"❌ 註冊使用者 {user_data['username']} 時發生錯誤: {e}")
            return False
            
    def login_user(self, username):
        """使用者登入"""
        try:
            response = requests.post(
                f"{BASE_URL}/api/user/login",
                json={"username": username}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    token = result.get("token")
                    self.user_tokens[username] = token
                    print(f"✅ 使用者 {username} 登入成功")
                    return token
                else:
                    print(f"❌ 使用者 {username} 登入失敗: {result.get('message')}")
                    return None
        except Exception as e:
            print(f"❌ 使用者 {username} 登入時發生錯誤: {e}")
            return None
            
    def give_user_points(self, username, points=50000):
        """給使用者增加點數"""
        if not self.admin_token:
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.post(
                f"{BASE_URL}/api/admin/users/give-points",
                json={
                    "username": username,
                    "type": "user",
                    "amount": points
                },
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    print(f"✅ 給使用者 {username} 增加 {points} 點數")
                    return True
                else:
                    print(f"❌ 給使用者 {username} 增加點數失敗: {result.get('message')}")
                    return False
            else:
                print(f"❌ 給使用者 {username} 增加點數失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 給使用者 {username} 增加點數時發生錯誤: {e}")
            return False
            
    def get_current_price(self):
        """獲取目前股價"""
        try:
            response = requests.get(f"{BASE_URL}/api/price/summary")
            if response.status_code == 200:
                data = response.json()
                return data.get("current_price", 100.0)
        except Exception:
            pass
        return 100.0  # 預設價格
        
    def place_order(self, username, order_data):
        """下股票訂單"""
        token = self.user_tokens.get(username)
        if not token:
            return False
            
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/user/stock/order",
                json=order_data,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    self.trade_count += 1
                    side_chinese = "買入" if order_data["side"] == "buy" else "賣出"
                    type_chinese = "市價單" if order_data["order_type"] == "market" else "限價單"
                    price_info = f"@{order_data.get('price', 'market')}" if order_data["order_type"] == "limit" else "@市價"
                    
                    print(f"✅ [{self.trade_count:3d}] {username} {side_chinese} {order_data['quantity']} 股 ({type_chinese} {price_info})")
                    return True
                else:
                    print(f"❌ {username} 下單失敗: {result.get('message')}")
                    return False
        except Exception as e:
            print(f"❌ {username} 下單時發生錯誤: {e}")
            return False
            
    def generate_random_order(self, current_price):
        """產生隨機訂單"""
        order_type = random.choice(["market", "market", "limit"])  # 更多市價單
        side = random.choice(["buy", "sell"])
        quantity = random.randint(1, 10)
        
        order = {
            "order_type": order_type,
            "side": side,
            "quantity": quantity
        }
        
        if order_type == "limit":
            # 限價單的價格在目前價格 ±10% 範圍內
            price_variation = random.uniform(0.9, 1.1)
            order["price"] = round(current_price * price_variation, 2)
            
        return order


def generate_100_trades():
    """產生 100 筆交易資料"""
    generator = TradingDataGenerator()
    
    print("🚀 開始產生 100 筆股票交易資料...")
    
    # 1. 管理員登入
    print("\n🔑 管理員登入...")
    if not generator.get_admin_token():
        print("❌ 無法獲取管理員權限，無法增加使用者資金")
        return False
    
    # 2. 註冊使用者
    print(f"\n📝 註冊 {len(MOCK_USERS)} 個模擬使用者...")
    for user_data in MOCK_USERS:
        generator.register_user(user_data)
        time.sleep(0.1)  # 避免請求過快
        
    if not generator.registered_users:
        print("❌ 沒有成功註冊任何使用者")
        return False
        
    # 3. 使用者登入
    print(f"\n🔐 使用者登入...")
    for user_data in generator.registered_users:
        generator.login_user(user_data["username"])
        time.sleep(0.1)
        
    if not generator.user_tokens:
        print("❌ 沒有成功登入任何使用者")
        return False
        
    # 4. 給使用者增加初始點數
    print(f"\n💰 給使用者增加初始交易資金...")
    for username in generator.user_tokens.keys():
        generator.give_user_points(username, 50000)  # 給每個使用者 50,000 點數
        time.sleep(0.1)
        
    # 5. 開始產生交易
    print(f"\n📈 開始產生 100 筆交易...")
    target_trades = 100
    
    while generator.trade_count < target_trades:
        # 隨機選擇一個使用者
        username = random.choice(list(generator.user_tokens.keys()))
        
        # 獲取目前股價
        current_price = generator.get_current_price()
        
        # 產生隨機訂單
        order = generator.generate_random_order(current_price)
        
        # 下單
        generator.place_order(username, order)
        
        # 隨機等待一段時間（0.1-1秒）
        time.sleep(random.uniform(0.1, 1.0))
        
    print(f"\n🎉 成功產生 {generator.trade_count} 筆交易記錄！")
    
    # 6. 顯示統計信息
    print(f"\n📊 交易統計:")
    print(f"   - 註冊使用者數: {len(generator.registered_users)}")
    print(f"   - 成功登入使用者數: {len(generator.user_tokens)}")
    print(f"   - 總交易筆數: {generator.trade_count}")
    
    return True
def main():
    """主函數"""
    print("="*60)
    print("🏦 股票交易資料產生器")
    print("="*60)
    
    # 檢查服務是否執行
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ 後端服務未正常執行，請先啟動: python main.py")
            return
    except:
        print("❌ 無法連線到後端服務，請先啟動: python main.py")
        return
    
    # 執行交易資料產生
    try:
        success = generate_100_trades()
        if success:
            print("\n✅ 交易資料產生完成！")
            print("\n🔍 您現在可以：")
            print("   1. 訪問前端頁面 http://localhost:3000")
            print("   2. 查看交易記錄和市場深度")
            print("   3. 測試排行榜功能")
            print("\n📊 可用的 API 端點：")
            print("   - GET /api/price/summary - 價格摘要")
            print("   - GET /api/market/depth - 市場深度")
            print("   - GET /api/market/trades - 最新交易")
            print("   - GET /api/leaderboard - 排行榜")
        else:
            print("\n⚠️  交易資料產生失敗，請檢查錯誤訊息。")
    except KeyboardInterrupt:
        print("\n\n👋 程序被使用者中斷")
    except Exception as e:
        print(f"\n❌ 程序執行過程中發生錯誤: {e}")
    
    print("="*60)


if __name__ == "__main__":
    main()
