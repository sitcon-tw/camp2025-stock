#!/usr/bin/env python3
"""
SITCON Camp 2025 交易系統啟動指南
完整的系統啟動和使用者註冊流程
"""

import requests
import json
import sys
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

class TradingSystemStarter:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.admin_token = None
        
    def check_system_health(self):
        """檢查系統健康狀態"""
        print("🏥 檢查系統狀態...")
        
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ 系統健康狀態: {health_data['status']}")
                print(f"   - 資料庫: {health_data.get('database', 'Unknown')}")
                print(f"   - 環境: {health_data.get('environment', 'Unknown')}")
                return True
            else:
                print(f"❌ 系統健康檢查失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 無法連線到系統: {e}")
            return False
    
    def admin_login(self):
        """管理員登入"""
        print("\n🔐 管理員登入...")
        
        admin_password = input("請輸入管理員密碼: ").strip()
        if not admin_password:
            print("❌ 密碼不能為空")
            return False
        
        try:
            response = requests.post(
                f"{self.base_url}/api/admin/login",
                json={"password": admin_password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data["token"]
                print("✅ 管理員登入成功")
                return True
            else:
                print(f"❌ 管理員登入失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 登入請求失敗: {e}")
            return False
    
    def setup_initial_market_config(self):
        """設定初始市場配置"""
        if not self.admin_token:
            print("❌ 需要管理員權限")
            return False
        
        print("\n⚙️ 設定初始市場配置...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # 設定市場開放時間（全天開放）
        current_time = datetime.now()
        start_time = int(current_time.timestamp())
        end_time = int((current_time + timedelta(days=7)).timestamp())  # 一週後結束
        
        market_config = {
            "openTime": [
                {
                    "start": start_time,
                    "end": end_time
                }
            ]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/admin/market/update",
                json=market_config,
                headers=headers
            )
            
            if response.status_code == 200:
                print("✅ 市場開放時間設定成功")
            else:
                print(f"⚠️  市場時間設定失敗: {response.status_code}")
        
        except Exception as e:
            print(f"❌ 設定市場時間失敗: {e}")
        
        # 設定漲跌限制
        limit_config = {"limitPercent": 20.0}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/admin/market/set-limit",
                json=limit_config,
                headers=headers
            )
            
            if response.status_code == 200:
                print("✅ 漲跌限制設定成功 (±20%)")
            else:
                print(f"⚠️  漲跌限制設定失敗: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 設定漲跌限制失敗: {e}")
        
        return True
    
    def create_sample_users(self):
        """建立範例使用者"""
        print("\n👥 建立範例使用者...")
        
        sample_users = [
            {
                "username": "小明",
                "email": "xiaoming@example.com",
                "team": "藍隊"
            },
            {
                "username": "小華",
                "email": "xiaohua@example.com", 
                "team": "紅隊"
            },
            {
                "username": "小美",
                "email": "xiaomei@example.com",
                "team": "綠隊"
            },
            {
                "username": "小強",
                "email": "xiaoqiang@example.com",
                "team": "藍隊"
            }
        ]
        
        created_users = []
        
        for user_data in sample_users:
            try:
                response = requests.post(
                    f"{self.base_url}/api/user/register",
                    json=user_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result["success"]:
                        print(f"✅ 使用者 {user_data['username']} 建立成功")
                        created_users.append(user_data["username"])
                    else:
                        print(f"⚠️  使用者 {user_data['username']} 建立失敗: {result['message']}")
                else:
                    print(f"❌ 使用者 {user_data['username']} 建立請求失敗: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ 建立使用者 {user_data['username']} 時發生錯誤: {e}")
        
        print(f"\n✅ 成功建立 {len(created_users)} 個範例使用者")
        return created_users
    
    def test_user_login_and_trading(self, username="小明"):
        """測試使用者登入和交易功能"""
        print(f"\n🧪 測試使用者 {username} 的交易功能...")
        
        # 使用者登入
        try:
            login_response = requests.post(
                f"{self.base_url}/api/user/login",
                json={"username": username}
            )
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                if login_data["success"]:
                    user_token = login_data["token"]
                    print(f"✅ 使用者 {username} 登入成功")
                    
                    user_headers = {"Authorization": f"Bearer {user_token}"}
                    
                    # 查詢投資組合
                    portfolio_response = requests.get(
                        f"{self.base_url}/api/user/portfolio",
                        headers=user_headers
                    )
                    
                    if portfolio_response.status_code == 200:
                        portfolio = portfolio_response.json()
                        print(f"📊 {username} 的投資組合:")
                        print(f"   - 點數: {portfolio['points']}")
                        print(f"   - 持股: {portfolio['stocks']}")
                        print(f"   - 總資產: {portfolio['totalValue']}")
                    
                    # 測試下買單
                    buy_order = {
                        "order_type": "limit",
                        "side": "buy",
                        "quantity": 2,
                        "price": 19.0
                    }
                    
                    order_response = requests.post(
                        f"{self.base_url}/api/user/stock/order",
                        json=buy_order,
                        headers=user_headers
                    )
                    
                    if order_response.status_code == 200:
                        order_result = order_response.json()
                        if order_result["success"]:
                            print(f"✅ {username} 下買單成功")
                        else:
                            print(f"⚠️  {username} 下買單失敗: {order_result['message']}")
                    
                    return True
                else:
                    print(f"❌ 使用者 {username} 登入失敗: {login_data['message']}")
            else:
                print(f"❌ 使用者 {username} 登入請求失敗: {login_response.status_code}")
                
        except Exception as e:
            print(f"❌ 測試使用者交易功能時發生錯誤: {e}")
        
        return False
    
    def show_market_status(self):
        """顯示市場狀態"""
        print("\n📈 目前市場狀態:")
        
        try:
            # 市場狀態
            status_response = requests.get(f"{self.base_url}/api/status")
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"   - 市場開放: {'是' if status_data['isOpen'] else '否'}")
                print(f"   - 目前時間: {status_data['currentTime']}")
            
            # 股票價格
            price_response = requests.get(f"{self.base_url}/api/price/summary")
            if price_response.status_code == 200:
                price_data = price_response.json()
                print(f"   - 目前股價: {price_data['lastPrice']}")
                print(f"   - 漲跌: {price_data['change']} ({price_data['changePercent']})")
                print(f"   - 成交量: {price_data['volume']}")
            
            # 排行榜
            leaderboard_response = requests.get(f"{self.base_url}/api/leaderboard")
            if leaderboard_response.status_code == 200:
                leaderboard = leaderboard_response.json()
                print(f"   - 註冊使用者數: {len(leaderboard)}")
                if leaderboard:
                    print("   - 前三名:")
                    for i, user in enumerate(leaderboard[:3]):
                        total_value = user['points'] + user['stockValue']
                        print(f"     {i+1}. {user['username']} ({user['team']}) - 總資產: {total_value}")
            
        except Exception as e:
            print(f"❌ 取得市場狀態失敗: {e}")
    
    def create_initial_announcement(self):
        """建立初始公告"""
        if not self.admin_token:
            return
        
        print("\n📢 發布歡迎公告...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        announcement = {
            "title": "🎉 SITCON Camp 2025 股票交易系統正式啟動！",
            "message": "歡迎大家使用股票交易系統！每人初始擁有 100 點數，快來體驗買賣股票的樂趣吧！記得查看排行榜，看看誰是最佳投資者！",
            "broadcast": False
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/admin/announcement",
                json=announcement,
                headers=headers
            )
            
            if response.status_code == 200:
                print("✅ 歡迎公告發布成功")
            else:
                print(f"⚠️  公告發布失敗: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 發布公告失敗: {e}")
    
    def run_complete_setup(self):
        """執行完整的系統設定"""
        print("="*60)
        print("🚀 SITCON Camp 2025 交易系統啟動器")
        print("="*60)
        
        # 1. 檢查系統健康狀態
        if not self.check_system_health():
            print("\n❌ 系統健康檢查失敗，請先啟動服務")
            print("   執行: python main.py")
            return False
        
        # 2. 管理員登入
        if not self.admin_login():
            print("\n❌ 管理員登入失敗，無法繼續設定")
            return False
        
        # 3. 設定市場配置
        self.setup_initial_market_config()
        
        # 4. 建立範例使用者
        created_users = self.create_sample_users()
        
        # 5. 測試使用者功能
        if created_users:
            self.test_user_login_and_trading(created_users[0])
        
        # 6. 發布歡迎公告
        self.create_initial_announcement()
        
        # 7. 顯示系統狀態
        self.show_market_status()
        
        # 8. 顯示總結
        print("\n" + "="*60)
        print("🎉 交易系統啟動完成！")
        print("="*60)
        print("📱 您現在可以:")
        print("   - 存取 API 文件: http://localhost:8000/docs")
        print("   - 查看市場狀態: http://localhost:8000/api/status")
        print("   - 查看排行榜: http://localhost:8000/api/leaderboard")
        print("   - 查看股票價格: http://localhost:8000/api/price/summary")
        print("\n🔐 管理員功能:")
        print("   - 管理員登入後可以給點數、發公告、設定市場參數")
        print("   - 管理員後台: http://localhost:8000/api/admin/*")
        print("\n👥 使用者功能:")
        print("   - 使用者可以註冊、登入、交易股票、轉帳點數")
        print("   - 使用者 API: http://localhost:8000/api/user/*")
        print("\n🎯 接下來的步驟:")
        print("   1. 讓學員註冊帳號")
        print("   2. 開始股票交易")
        print("   3. 觀察排行榜變化")
        print("   4. 舉辦交易競賽！")
        print("="*60)
        
        return True


def main():
    """主程序"""
    starter = TradingSystemStarter()
    
    try:
        success = starter.run_complete_setup()
        if success:
            print("\n🚀 系統準備就緒！開始您的交易之旅吧！")
        else:
            print("\n❌ 系統設定未完成，請檢查錯誤訊息")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 設定被使用者中斷")
    except Exception as e:
        print(f"\n❌ 設定過程中發生錯誤: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
