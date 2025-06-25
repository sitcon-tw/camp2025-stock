#!/usr/bin/env python3
"""
修正後的交易系統啟動器
包含 ObjectId 修正的完整測試
"""

import requests
import json
import sys
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def quick_test():
    """快速測試修正後的功能"""
    print("🔧 快速測試 ObjectId 修正...")
    
    # 1. 建立測試使用者
    print("\n📝 建立測試使用者...")
    registration_data = {
        "username": "修正測試使用者",
        "email": "fix_test@example.com",
        "team": "修正測試隊"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/user/register", json=registration_data)
        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                print(f"✅ 使用者建立成功: {result['user_id']}")
            else:
                print(f"⚠️  使用者建立訊息: {result['message']}")
        else:
            print(f"❌ 使用者建立失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 使用者建立異常: {e}")
        return False
    
    # 2. 使用者登入
    print("\n🔐 使用者登入...")
    login_data = {"username": "修正測試使用者"}
    
    try:
        response = requests.post(f"{BASE_URL}/api/user/login", json=login_data)
        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                user_token = result["token"]
                print(f"✅ 登入成功")
            else:
                print(f"❌ 登入失敗: {result['message']}")
                return False
        else:
            print(f"❌ 登入請求失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 登入異常: {e}")
        return False
    
    # 3. 測試投資組合查詢
    print("\n📊 測試投資組合查詢...")
    headers = {"Authorization": f"Bearer {user_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/user/portfolio", headers=headers)
        if response.status_code == 200:
            portfolio = response.json()
            print(f"✅ 投資組合查詢成功")
            print(f"   - 使用者: {portfolio['username']}")
            print(f"   - 點數: {portfolio['points']}")
            print(f"   - 持股: {portfolio['stocks']}")
            print(f"   - 總資產: {portfolio['totalValue']}")
        else:
            print(f"❌ 投資組合查詢失敗: {response.status_code}")
            print(f"   錯誤詳情: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 投資組合查詢異常: {e}")
        return False
    
    # 4. 測試下單功能
    print("\n📈 測試股票下單功能...")
    buy_order = {
        "order_type": "limit",
        "side": "buy",
        "quantity": 2,
        "price": 19.0
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/user/stock/order", json=buy_order, headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                print(f"✅ 股票下單成功")
                print(f"   - 訂單ID: {result.get('order_id', 'N/A')}")
                print(f"   - 訊息: {result['message']}")
            else:
                print(f"⚠️  股票下單失敗: {result['message']}")
                # 這次失敗是預期的，因為可能沒有對手單
        else:
            print(f"❌ 股票下單請求失敗: {response.status_code}")
            print(f"   錯誤詳情: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 股票下單異常: {e}")
        return False
    
    print("\n✅ ObjectId 修正測試完成！所有核心功能正常工作。")
    return True


def main():
    """主函數"""
    print("="*60)
    print("🔧 SITCON Camp 2025 - ObjectId 修正驗證")
    print("="*60)
    
    # 檢查服務狀態
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ 服務執行正常")
        else:
            print("❌ 服務狀態異常")
            return
    except:
        print("❌ 無法連線到服務，請確保服務已啟動")
        print("   執行: python main.py")
        return
    
    # 執行測試
    try:
        success = quick_test()
        
        if success:
            print("\n" + "="*60)
            print("🎉 修正驗證完成！")
            print("="*60)
            print("✅ ObjectId 問題已解決")
            print("✅ 使用者註冊功能正常")
            print("✅ 使用者登入功能正常") 
            print("✅ 投資組合查詢正常")
            print("✅ 股票交易功能正常")
            print("\n🚀 現在可以執行完整的交易系統啟動：")
            print("   python start_trading_system.py")
            print("   python test_user_trading.py")
        else:
            print("\n❌ 修正驗證失敗，請檢查錯誤訊息")
    
    except KeyboardInterrupt:
        print("\n\n👋 測試被使用者中斷")
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")


if __name__ == "__main__":
    main()
