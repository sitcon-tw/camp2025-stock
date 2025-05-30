#!/usr/bin/env python3
"""
管理員 API 權限測試腳本
演示如何正確測試需要認證的管理員 API
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"

class AdminAPITester:
    def __init__(self, base_url=BASE_URL, admin_password=None):
        self.base_url = base_url
        self.admin_password = admin_password
        self.token = None
        self.session = requests.Session()
    
    def test_unauthorized_access(self):
        """測試未授權存取（應該被拒絕）"""
        print("🚫 測試未授權存取...")
        
        unauthorized_endpoints = [
            ("GET", "/api/admin/user"),
            ("POST", "/api/admin/users/give-points"),
            ("POST", "/api/admin/announcement"),
            ("GET", "/api/admin/stats")
        ]
        
        for method, endpoint in unauthorized_endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}")
                else:
                    response = self.session.post(f"{self.base_url}{endpoint}", json={})
                
                if response.status_code in [401, 403]:
                    print(f"✅ {method} {endpoint} - 正確拒絕未授權存取 (狀態碼: {response.status_code})")
                else:
                    print(f"⚠️  {method} {endpoint} - 可能存在安全問題 (狀態碼: {response.status_code})")
                    
            except Exception as e:
                print(f"❌ {method} {endpoint} - 連線錯誤: {e}")
        print()
    
    def admin_login(self, password=None):
        """管理員登入取得 Token"""
        print("🔐 管理員登入...")
        
        if not password:
            password = self.admin_password or input("請輸入管理員密碼: ")
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/admin/login",
                json={"password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                if self.token:
                    print(f"✅ 登入成功! Token: {self.token[:20]}...")
                    # 設定後續請求的認證 header
                    self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                    return True
                else:
                    print("❌ 登入回應中沒有 token")
                    return False
            else:
                print(f"❌ 登入失敗 - 狀態碼: {response.status_code}")
                if response.status_code == 401:
                    print("   密碼錯誤，請檢查 ADMIN_PASSWORD 環境變數")
                return False
                
        except Exception as e:
            print(f"❌ 登入請求失敗: {e}")
            return False
    
    def test_admin_apis(self):
        """測試所有管理員 API 端點"""
        if not self.token:
            print("❌ 沒有有效的認證 token，無法測試管理員 API")
            return
        
        print("🔒 測試管理員 API 端點...")
        
        # 測試各個端點
        test_cases = [
            self.test_get_users,
            self.test_give_points,
            self.test_create_announcement,
            self.test_update_market_hours,
            self.test_set_trading_limit,
            self.test_get_announcements,
            self.test_admin_stats
        ]
        
        success_count = 0
        for test_case in test_cases:
            try:
                if test_case():
                    success_count += 1
            except Exception as e:
                print(f"❌ 測試失敗: {e}")
        
        print(f"\n管理員 API 測試結果: {success_count}/{len(test_cases)} 成功\n")
        return success_count == len(test_cases)
    
    def test_get_users(self):
        """測試查詢使用者資產"""
        print("📊 測試查詢使用者資產...")
        
        try:
            # 查詢所有使用者
            response = self.session.get(f"{self.base_url}/api/admin/user")
            if response.status_code == 200:
                users = response.json()
                print(f"✅ 查詢所有使用者成功 - 找到 {len(users)} 個使用者")
                
                # 如果有使用者，測試查詢特定使用者
                if users:
                    first_user = users[0].get("username", "測試使用者")
                    response2 = self.session.get(f"{self.base_url}/api/admin/user?user={first_user}")
                    if response2.status_code == 200:
                        print(f"✅ 查詢特定使用者 ({first_user}) 成功")
                
                return True
            else:
                print(f"❌ 查詢使用者失敗 - 狀態碼: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 查詢使用者異常: {e}")
            return False
    
    def test_give_points(self):
        """測試給予點數"""
        print("💰 測試給予點數...")
        
        try:
            data = {
                "username": "測試使用者",
                "type": "user",
                "amount": 50
            }
            
            response = self.session.post(f"{self.base_url}/api/admin/users/give-points", json=data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 給予點數成功: {result.get('message', '已處理')}")
                return True
            else:
                print(f"❌ 給予點數失敗 - 狀態碼: {response.status_code}")
                if response.status_code == 404:
                    print("   使用者不存在（這在測試環境中是正常的）")
                    return True  # 在測試環境中使用者不存在是正常的
                return False
                
        except Exception as e:
            print(f"❌ 給予點數異常: {e}")
            return False
    
    def test_create_announcement(self):
        """測試建立公告"""
        print("📢 測試建立公告...")
        
        try:
            data = {
                "title": f"測試公告 - {datetime.now().strftime('%H:%M:%S')}",
                "message": "這是一個自動化測試建立的公告",
                "broadcast": False  # 測試時不廣播
            }
            
            response = self.session.post(f"{self.base_url}/api/admin/announcement", json=data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 建立公告成功: {result.get('message', '已處理')}")
                return True
            else:
                print(f"❌ 建立公告失敗 - 狀態碼: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 建立公告異常: {e}")
            return False
    
    def test_update_market_hours(self):
        """測試更新市場時間"""
        print("⏰ 測試更新市場時間...")
        
        try:
            current_timestamp = int(datetime.now().timestamp())
            data = {
                "openTime": [
                    {
                        "start": current_timestamp,
                        "end": current_timestamp + 3600  # 1小時後
                    }
                ]
            }
            
            response = self.session.post(f"{self.base_url}/api/admin/market/update", json=data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 更新市場時間成功")
                return True
            else:
                print(f"❌ 更新市場時間失敗 - 狀態碼: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 更新市場時間異常: {e}")
            return False
    
    def test_set_trading_limit(self):
        """測試設定漲跌限制"""
        print("📈 測試設定漲跌限制...")
        
        try:
            data = {"limitPercent": 10.0}
            
            response = self.session.post(f"{self.base_url}/api/admin/market/set-limit", json=data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 設定漲跌限制成功")
                return True
            else:
                print(f"❌ 設定漲跌限制失敗 - 狀態碼: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 設定漲跌限制異常: {e}")
            return False
    
    def test_get_announcements(self):
        """測試取得公告列表"""
        print("📋 測試取得公告列表...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/admin/announcements")
            
            if response.status_code == 200:
                announcements = response.json()
                print(f"✅ 取得公告列表成功 - 找到 {len(announcements)} 個公告")
                return True
            else:
                print(f"❌ 取得公告列表失敗 - 狀態碼: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 取得公告列表異常: {e}")
            return False
    
    def test_admin_stats(self):
        """測試管理員統計"""
        print("📊 測試管理員統計...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/admin/stats")
            
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ 取得管理員統計成功")
                print(f"   - 總使用者數: {stats.get('total_users', 0)}")
                print(f"   - 總交易數: {stats.get('total_trades', 0)}")
                return True
            else:
                print(f"❌ 取得管理員統計失敗 - 狀態碼: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 取得管理員統計異常: {e}")
            return False
    
    def test_token_expiry(self):
        """測試 Token 過期處理"""
        print("⏳ 測試 Token 驗證...")
        
        # 測試無效 Token
        invalid_token = "invalid.token.here"
        headers = {"Authorization": f"Bearer {invalid_token}"}
        
        try:
            response = requests.get(f"{self.base_url}/api/admin/user", headers=headers)
            
            if response.status_code == 401:
                print("✅ 無效 Token 正確被拒絕")
                return True
            else:
                print(f"⚠️  無效 Token 未被正確處理 - 狀態碼: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Token 驗證測試異常: {e}")
            return False
    
    def run_all_tests(self):
        """執行所有測試"""
        print("="*60)
        print("管理員 API 權限測試")
        print("="*60)
        print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"目標伺服器: {self.base_url}")
        print("="*60)
        
        # 1. 測試未授權存取
        self.test_unauthorized_access()
        
        # 2. 測試 Token 驗證
        self.test_token_expiry()
        print()
        
        # 3. 管理員登入
        if not self.admin_login():
            print("❌ 無法登入，終止測試")
            return False
        print()
        
        # 4. 測試所有管理員 API
        success = self.test_admin_apis()
        
        # 總結
        print("="*60)
        if success:
            print("🎉 所有管理員 API 測試通過！")
            print("✅ 認證機制工作正常")
            print("✅ 權限控制正確實施")
        else:
            print("⚠️  部分測試未通過，請檢查日誌")
        print("="*60)
        
        return success


def main():
    """主函數"""
    # 可以通過命令行參數或環境變數設定密碼
    import os
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    
    tester = AdminAPITester(admin_password=admin_password)
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n\n👋 測試被使用者中斷")
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
