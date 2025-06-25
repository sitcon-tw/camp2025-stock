#!/usr/bin/env python3
"""
API 端點快速驗證腳本
用於驗證所有 API 端點是否正常工作
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_public_apis():
    """測試公開 API 端點"""
    print("🔍 測試公開 API 端點...")
    
    public_endpoints = [
        ("GET", "/api/price/summary", "股票價格摘要"),
        ("GET", "/api/price/depth", "五檔報價"),
        ("GET", "/api/price/trades", "成交記錄"),
        ("GET", "/api/leaderboard", "排行榜"),
        ("GET", "/api/status", "市場狀態"),
        ("GET", "/api/price/current", "目前股價"),
        ("GET", "/api/stats", "系統統計")
    ]
    
    success_count = 0
    for method, endpoint, description in public_endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {description} ({endpoint}) - 正常")
                success_count += 1
            else:
                print(f"❌ {description} ({endpoint}) - 狀態碼: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {description} ({endpoint}) - 連線失敗: {e}")
    
    print(f"\n公開 API 測試結果: {success_count}/{len(public_endpoints)} 成功\n")
    return success_count == len(public_endpoints)


def test_admin_apis(admin_token=None):
    """測試管理員 API 端點"""
    print("🔒 測試管理員 API 端點...")
    
    # 如果沒有提供 token，嘗試登入
    if not admin_token:
        print("嘗試管理員登入...")
        admin_password = input("請輸入管理員密碼（或按 Enter 跳過）: ").strip()
        if not admin_password:
            print("⏭️  跳過管理員 API 測試")
            return False
        
        try:
            login_response = requests.post(
                f"{BASE_URL}/api/admin/login",
                json={"password": admin_password},
                timeout=5
            )
            if login_response.status_code == 200:
                admin_token = login_response.json().get("token")
                print("✅ 管理員登入成功")
            else:
                print(f"❌ 管理員登入失敗 - 狀態碼: {login_response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ 管理員登入失敗 - 連線錯誤: {e}")
            return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    admin_endpoints = [
        ("GET", "/api/admin/user", "查詢使用者資產"),
        ("GET", "/api/admin/announcements", "取得公告列表"),
        ("GET", "/api/admin/stats", "管理員統計")
    ]
    
    success_count = 0
    for method, endpoint, description in admin_endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
            if response.status_code == 200:
                print(f"✅ {description} ({endpoint}) - 正常")
                success_count += 1
            else:
                print(f"❌ {description} ({endpoint}) - 狀態碼: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {description} ({endpoint}) - 連線失敗: {e}")
    
    print(f"\n管理員 API 測試結果: {success_count}/{len(admin_endpoints)} 成功\n")
    return success_count == len(admin_endpoints)


def test_api_spec_compliance():
    """測試 API 規格書符合性"""
    print("📋 驗證 API 規格書符合性...")
    
    # API 規格書要求的端點
    required_endpoints = [
        # 公開 API
        ("GET", "/api/price/summary"),
        ("GET", "/api/price/depth"),
        ("GET", "/api/price/trades"),
        ("GET", "/api/leaderboard"),
        ("GET", "/api/status"),
        
        # 管理員 API（這些需要認證，所以測試存在性即可）
        ("POST", "/api/admin/login"),
        ("GET", "/api/admin/user"),
        ("POST", "/api/admin/users/give-points"),
        ("POST", "/api/admin/announcement"),
        ("POST", "/api/admin/market/update"),
        ("POST", "/api/admin/market/set-limit")
    ]
    
    success_count = 0
    for method, endpoint in required_endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json={}, timeout=5)
            
            # 端點存在（不是 404）就算成功
            if response.status_code != 404:
                print(f"✅ {method} {endpoint} - 端點存在")
                success_count += 1
            else:
                print(f"❌ {method} {endpoint} - 端點不存在 (404)")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {method} {endpoint} - 連線失敗: {e}")
    
    print(f"\nAPI 規格書符合性: {success_count}/{len(required_endpoints)} 端點實作")
    print(f"符合度: {success_count/len(required_endpoints)*100:.1f}%\n")
    
    return success_count == len(required_endpoints)


def test_server_health():
    """測試伺服器健康狀態"""
    print("🏥 檢查伺服器健康狀態...")
    
    try:
        # 檢查根端點
        root_response = requests.get(f"{BASE_URL}/", timeout=5)
        if root_response.status_code == 200:
            print("✅ 根端點正常")
            data = root_response.json()
            print(f"   - 服務: {data.get('message', 'Unknown')}")
            print(f"   - 版本: {data.get('version', 'Unknown')}")
            print(f"   - 環境: {data.get('environment', 'Unknown')}")
        
        # 檢查健康檢查端點
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ 健康檢查正常")
            health_data = health_response.json()
            print(f"   - 狀態: {health_data.get('status', 'Unknown')}")
            print(f"   - 資料庫: {health_data.get('database', 'Unknown')}")
        
        # 檢查 API 文件
        docs_response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if docs_response.status_code == 200:
            print("✅ API 文件可存取")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 伺服器連線失敗: {e}")
        print("請確保伺服器正在執行: python main.py")
        return False


def main():
    """主函數"""
    print("="*60)
    print("SITCON Camp 2025 點數系統 - API 端點驗證")
    print("="*60)
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目標伺服器: {BASE_URL}")
    print("="*60)
    
    # 測試伺服器健康狀態
    if not test_server_health():
        print("\n❌ 伺服器無法連線，請先啟動服務")
        sys.exit(1)
    
    print()
    
    # 測試 API 規格書符合性
    spec_ok = test_api_spec_compliance()
    
    # 測試公開 API
    public_ok = test_public_apis()
    
    # 測試管理員 API
    admin_ok = test_admin_apis()
    
    # 總結
    print("="*60)
    print("測試總結:")
    print(f"✅ API 規格書符合性: {'通過' if spec_ok else '未通過'}")
    print(f"✅ 公開 API 功能: {'正常' if public_ok else '異常'}")
    print(f"✅ 管理員 API 功能: {'正常' if admin_ok else '跳過/異常'}")
    
    if spec_ok and public_ok:
        print("\n🎉 恭喜！所有 API 端點執行正常！")
        print("🌐 您可以存取以下位址：")
        print(f"   - API 文件: {BASE_URL}/docs")
        print(f"   - ReDoc: {BASE_URL}/redoc")
        print(f"   - 健康檢查: {BASE_URL}/health")
    else:
        print("\n⚠️  部分功能可能存在問題，請檢查日誌")
    
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 測試被使用者中斷")
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        sys.exit(1)
