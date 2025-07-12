#!/usr/bin/env python3
"""
使用 JWT token 查詢 API 來檢查資料結構
"""

import requests
import json
import base64
from datetime import datetime

# 提供的 JWT token
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiOTA1MjUyMTQ1NSIsInRlbGVncmFtX2lkIjo2OTc4ODQyMzg1LCJ0eXBlIjoidXNlciIsImV4cCI6MTc1MjQzOTM5NX0.gBz9b7WjEuyb6AlJI7ed4vmL-RI-eb7ARo5eJRmLCC4"

# API 基礎 URL
BASE_URL = "http://localhost:8000"

def decode_token(token):
    """解碼 JWT token (不驗證簽名)"""
    try:
        # JWT token 由三部分組成，用 '.' 分隔
        parts = token.split('.')
        if len(parts) != 3:
            print("❌ 無效的 JWT token 格式")
            return None
        
        # 解碼 payload (第二部分)
        payload = parts[1]
        
        # 補齊 base64 padding
        missing_padding = len(payload) % 4
        if missing_padding:
            payload += '=' * (4 - missing_padding)
        
        # Base64 解碼
        decoded_bytes = base64.urlsafe_b64decode(payload)
        decoded = json.loads(decoded_bytes.decode('utf-8'))
        
        print("🔍 JWT Token 內容:")
        for key, value in decoded.items():
            if key == "exp":
                # 轉換過期時間為可讀格式
                exp_time = datetime.fromtimestamp(value)
                print(f"  {key}: {value} ({exp_time})")
            else:
                print(f"  {key}: {value}")
        return decoded
    except Exception as e:
        print(f"❌ 無法解碼 token: {e}")
        return None

def check_server_status():
    """檢查後端服務狀態"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ 後端服務運行正常")
            return True
        else:
            print(f"❌ 後端服務狀態異常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到後端服務 (Connection refused)")
        return False
    except Exception as e:
        print(f"❌ 檢查服務狀態時發生錯誤: {e}")
        return False

def query_user_info(token):
    """查詢使用者資訊"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        print("\n📊 查詢使用者資訊...")
        # 嘗試不同的使用者資訊端點
        endpoints = [
            "/api/user/info",
            "/api/user/profile", 
            "/api/user/portfolio"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
                if response.status_code == 200:
                    user_info = response.json()
                    print(f"✅ 端點 {endpoint} 查詢成功:")
                    print(json.dumps(user_info, indent=2, ensure_ascii=False))
                    return user_info
                elif response.status_code == 404:
                    print(f"⚠️ 端點 {endpoint} 不存在")
                else:
                    print(f"⚠️ 端點 {endpoint} 返回: {response.status_code}")
                    if response.text:
                        print(f"    錯誤詳情: {response.text}")
            except Exception as e:
                print(f"⚠️ 端點 {endpoint} 查詢錯誤: {e}")
        
        return None
    except Exception as e:
        print(f"❌ 查詢使用者資訊時發生錯誤: {e}")
        return None

def query_point_history(token):
    """查詢點數歷史記錄"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        print("\n📈 查詢點數歷史記錄...")
        # 嘗試不同的可能的 API 端點
        endpoints = [
            "/api/user/logs",
            "/api/user/points/history",
            "/api/user/point_logs",
            "/api/user/points",
            "/api/user/history"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ 端點 {endpoint} 查詢成功:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    return data
                elif response.status_code == 404:
                    print(f"⚠️ 端點 {endpoint} 不存在")
                else:
                    print(f"⚠️ 端點 {endpoint} 返回: {response.status_code}")
                    if response.text:
                        print(f"    錯誤詳情: {response.text}")
            except Exception as e:
                print(f"⚠️ 端點 {endpoint} 查詢錯誤: {e}")
        
        print("❌ 所有點數歷史查詢端點都失敗")
        return None
        
    except Exception as e:
        print(f"❌ 查詢點數歷史時發生錯誤: {e}")
        return None

def query_portfolio(token):
    """查詢投資組合"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        print("\n💼 查詢投資組合...")
        response = requests.get(f"{BASE_URL}/api/user/portfolio", headers=headers, timeout=5)
        
        if response.status_code == 200:
            portfolio = response.json()
            print("✅ 投資組合查詢成功:")
            print(json.dumps(portfolio, indent=2, ensure_ascii=False))
            return portfolio
        else:
            print(f"❌ 查詢失敗: {response.status_code}")
            print(f"  回應: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 查詢投資組合時發生錯誤: {e}")
        return None

def list_available_endpoints():
    """嘗試列出可用的 API 端點"""
    print("\n🔍 嘗試找出可用的 API 端點...")
    
    # 嘗試一些常見的端點
    common_endpoints = [
        "/docs",
        "/api/docs", 
        "/api/user/",
        "/api/admin/",
        "/api/public/",
        "/openapi.json"
    ]
    
    for endpoint in common_endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=3)
            if response.status_code == 200:
                print(f"✅ 可用端點: {endpoint}")
            elif response.status_code in [401, 403]:
                print(f"🔒 需要認證: {endpoint}")
            elif response.status_code == 404:
                print(f"❌ 不存在: {endpoint}")
            else:
                print(f"⚠️ {endpoint}: {response.status_code}")
        except Exception:
            pass

def main():
    """主函數"""
    print("🔍 使用 JWT Token 查詢資料結構")
    print("="*50)
    
    # 1. 解碼 token
    decoded_payload = decode_token(JWT_TOKEN)
    if not decoded_payload:
        print("❌ 無法解碼 token，停止執行")
        return
    
    # 2. 檢查後端服務狀態
    if not check_server_status():
        print("❌ 後端服務不可用，停止執行")
        return
    
    # 3. 列出可用端點
    list_available_endpoints()
    
    # 4. 查詢使用者相關資訊
    user_info = query_user_info(JWT_TOKEN)
    point_history = query_point_history(JWT_TOKEN)
    portfolio = query_portfolio(JWT_TOKEN)
    
    # 5. 總結
    print("\n" + "="*50)
    print("📋 查詢結果總結:")
    print("="*50)
    
    if decoded_payload:
        print(f"✅ Token 解碼成功，使用者 ID: {decoded_payload.get('user_id')}")
    
    if user_info:
        print("✅ 成功獲取使用者資訊")
    else:
        print("❌ 無法獲取使用者資訊")
    
    if point_history:
        print("✅ 成功獲取點數歷史")
    else:
        print("❌ 無法獲取點數歷史")
    
    if portfolio:
        print("✅ 成功獲取投資組合")
    else:
        print("❌ 無法獲取投資組合")
    
    print("\n💡 建議:")
    print("1. 確認後端服務是否正確啟動")
    print("2. 檢查 JWT token 是否有效且未過期")
    print("3. 確認 API 端點路徑是否正確")

if __name__ == "__main__":
    main()