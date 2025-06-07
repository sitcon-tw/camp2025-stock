#!/usr/bin/env python3
"""
SITCON Camp 2025 System API 學員註冊測試腳本

測試新的學員註冊 API: POST /api/system/users/register
"""

import requests
import json
import os

# API 設定
BASE_URL = "http://localhost:8000"
SYSTEM_API_URL = f"{BASE_URL}/api/system"

# 從環境變數獲取 token（或使用預設值）
BOT_TOKEN = os.getenv("INTERNAL_API_KEY", "your_internal_api_key_here")

# 測試用學員資料
TEST_STUDENTS = [
    {"id": "1234567890", "name": "毛宥鈞"},
    {"id": "0987654321", "name": "測試學員"},
    {"id": "1111111111", "name": "張小明"}
]

class SystemAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "token": BOT_TOKEN  # 使用 header 進行認證
        })
        self.test_results = []

    def log_test(self, test_name: str, success: bool, message: str):
        """記錄測試結果"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })

    def test_student_registration(self, student_data):
        """測試學員註冊"""
        try:
            response = self.session.post(f"{SYSTEM_API_URL}/users/register", json=student_data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok") and result.get("message") == "成功註冊":
                    self.log_test(
                        f"Student Registration ({student_data['name']})", 
                        True, 
                        f"學員 {student_data['name']} (ID: {student_data['id']}) 註冊成功"
                    )
                    return True
                else:
                    self.log_test(
                        f"Student Registration ({student_data['name']})", 
                        False, 
                        f"註冊回應異常: {result}"
                    )
                    return False
            else:
                self.log_test(
                    f"Student Registration ({student_data['name']})", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                f"Student Registration ({student_data['name']})", 
                False, 
                f"請求失敗: {str(e)}"
            )
            return False

    def test_invalid_token(self):
        """測試無效 token"""
        try:
            # 創建一個使用無效 token 的 session
            invalid_session = requests.Session()
            invalid_session.headers.update({
                "Content-Type": "application/json",
                "token": "invalid_token_123"
            })
            
            data = {"id": "1234567890", "name": "測試學員"}
            response = invalid_session.post(f"{SYSTEM_API_URL}/users/register", json=data)
            
            if response.status_code == 401:
                error = response.json()
                if "Invalid token" in error.get("detail", ""):
                    self.log_test("Invalid Token", True, "無效 token 正確被拒絕")
                else:
                    self.log_test("Invalid Token", False, f"錯誤訊息不正確: {error}")
            else:
                self.log_test("Invalid Token", False, f"應該返回 401，但得到 {response.status_code}")
                
        except Exception as e:
            self.log_test("Invalid Token", False, f"請求失敗: {str(e)}")

    def test_missing_token(self):
        """測試缺少 token"""
        try:
            # 創建一個沒有 token 的 session
            no_token_session = requests.Session()
            no_token_session.headers.update({"Content-Type": "application/json"})
            
            data = {"id": "1234567890", "name": "測試學員"}
            response = no_token_session.post(f"{SYSTEM_API_URL}/users/register", json=data)
            
            if response.status_code == 422:
                # FastAPI 會返回 422 當缺少必要的 header
                self.log_test("Missing Token", True, "缺少 token 正確被拒絕")
            else:
                self.log_test("Missing Token", False, f"應該返回 422，但得到 {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Missing Token", False, f"請求失敗: {str(e)}")

    def test_duplicate_registration(self):
        """測試重複註冊"""
        try:
            # 使用相同的學員資料註冊兩次
            student_data = {"id": "9999999999", "name": "重複測試學員"}
            
            # 第一次註冊
            response1 = self.session.post(f"{SYSTEM_API_URL}/users/register", json=student_data)
            
            # 第二次註冊（應該也返回成功）
            response2 = self.session.post(f"{SYSTEM_API_URL}/users/register", json=student_data)
            
            if response1.status_code == 200 and response2.status_code == 200:
                result1 = response1.json()
                result2 = response2.json()
                
                if result1.get("ok") and result2.get("ok"):
                    self.log_test("Duplicate Registration", True, "重複註冊正確處理（都返回成功）")
                else:
                    self.log_test("Duplicate Registration", False, f"重複註冊處理異常: {result1}, {result2}")
            else:
                self.log_test("Duplicate Registration", False, f"HTTP 狀態碼異常: {response1.status_code}, {response2.status_code}")
                
        except Exception as e:
            self.log_test("Duplicate Registration", False, f"請求失敗: {str(e)}")

    def run_all_tests(self):
        """執行所有測試"""
        print("🚀 開始執行 System API 學員註冊測試...")
        print(f"📡 API Base URL: {BASE_URL}")
        print(f"🔑 BOT Token: {BOT_TOKEN[:10]}...")
        print("=" * 60)
        
        # 測試認證
        self.test_invalid_token()
        self.test_missing_token()
        
        # 測試學員註冊
        for student in TEST_STUDENTS:
            self.test_student_registration(student)
        
        # 測試重複註冊
        self.test_duplicate_registration()
        
        # 總結測試結果
        print("=" * 60)
        print("📊 測試結果總結:")
        
        passed_tests = [test for test in self.test_results if test["success"]]
        failed_tests = [test for test in self.test_results if not test["success"]]
        
        print(f"✅ 通過: {len(passed_tests)} 個測試")
        print(f"❌ 失敗: {len(failed_tests)} 個測試")
        
        if failed_tests:
            print("\n❌ 失敗的測試:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['message']}")
        
        print(f"\n🎯 總體成功率: {len(passed_tests)}/{len(self.test_results)} ({len(passed_tests)/len(self.test_results)*100:.1f}%)")
        
        if len(failed_tests) == 0:
            print("🎉 所有測試都通過了！學員註冊 API 運作正常。")
        else:
            print("⚠️  有部分測試失敗，請檢查 API 伺服器狀態和設定。")


if __name__ == "__main__":
    tester = SystemAPITester()
    tester.run_all_tests()
