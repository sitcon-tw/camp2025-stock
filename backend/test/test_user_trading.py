#!/usr/bin/env python3
"""
快速測試使用者交易功能的腳本
測試完整的使用者註冊、登入、交易流程
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_user_registration_and_trading():
    """測試使用者註冊和交易功能"""
    print("🧪 測試使用者註冊和交易功能...")
    
    # 1. 使用者註冊
    print("\n📝 1. 測試使用者註冊...")
    registration_data = {
        "username": "測試小王",
        "email": "test_wang@example.com",
        "team": "測試隊"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/user/register",
            json=registration_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                print(f"✅ 使用者註冊成功: {result['message']}")
                user_id = result.get("user_id")
            else:
                print(f"⚠️  使用者註冊失敗: {result['message']}")
                if "已存在" in result['message']:
                    print("   使用者可能已存在，繼續測試登入...")
                else:
                    return False
        else:
            print(f"❌ 使用者註冊請求失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 使用者註冊異常: {e}")
        return False
    
    # 2. 使用者登入
    print("\n🔐 2. 測試使用者登入...")
    login_data = {
        "username": "測試小王"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/user/login",
            json=login_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                user_token = result["token"]
                user_info = result["user"]
                print(f"✅ 使用者登入成功")
                print(f"   - 使用者: {user_info['username']}")
                print(f"   - 隊伍: {user_info['team']}")
                print(f"   - 點數: {user_info['points']}")
            else:
                print(f"❌ 使用者登入失敗: {result['message']}")
                return False
        else:
            print(f"❌ 使用者登入請求失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 使用者登入異常: {e}")
        return False
    
    # 3. 查詢投資組合
    print("\n📊 3. 測試查詢投資組合...")
    headers = {"Authorization": f"Bearer {user_token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/user/portfolio",
            headers=headers
        )
        
        if response.status_code == 200:
            portfolio = response.json()
            print(f"✅ 投資組合查詢成功")
            print(f"   - 使用者: {portfolio['username']}")
            print(f"   - 點數: {portfolio['points']}")
            print(f"   - 持股: {portfolio['stocks']}")
            print(f"   - 股票價值: {portfolio['stockValue']}")
            print(f"   - 總資產: {portfolio['totalValue']}")
        else:
            print(f"❌ 投資組合查詢失敗: {response.status_code}")
            print(f"   回應: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 投資組合查詢異常: {e}")
        return False
    
    # 4. 測試下限價買單
    print("\n📈 4. 測試下限價買單...")
    buy_order = {
        "order_type": "limit",
        "side": "buy",
        "quantity": 2,
        "price": 19.5
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/user/stock/order",
            json=buy_order,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                print(f"✅ 限價買單成功")
                print(f"   - 訂單ID: {result.get('order_id', 'N/A')}")
                print(f"   - 訊息: {result['message']}")
            else:
                print(f"⚠️  限價買單失敗: {result['message']}")
        else:
            print(f"❌ 限價買單請求失敗: {response.status_code}")
            print(f"   回應: {response.text}")
    except Exception as e:
        print(f"❌ 限價買單異常: {e}")
    
    # 5. 測試下市價買單
    print("\n📈 5. 測試下市價買單...")
    market_buy_order = {
        "order_type": "market",
        "side": "buy",
        "quantity": 1
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/user/stock/order",
            json=market_buy_order,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                print(f"✅ 市價買單成功")
                print(f"   - 訂單ID: {result.get('order_id', 'N/A')}")
                print(f"   - 成交價格: {result.get('executed_price', 'N/A')}")
                print(f"   - 成交數量: {result.get('executed_quantity', 'N/A')}")
            else:
                print(f"⚠️  市價買單失敗: {result['message']}")
        else:
            print(f"❌ 市價買單請求失敗: {response.status_code}")
            print(f"   回應: {response.text}")
    except Exception as e:
        print(f"❌ 市價買單異常: {e}")
    
    # 6. 再次查詢投資組合
    print("\n📊 6. 交易後查詢投資組合...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/user/portfolio",
            headers=headers
        )
        
        if response.status_code == 200:
            portfolio = response.json()
            print(f"✅ 交易後投資組合:")
            print(f"   - 點數: {portfolio['points']}")
            print(f"   - 持股: {portfolio['stocks']}")
            print(f"   - 股票價值: {portfolio['stockValue']}")
            print(f"   - 總資產: {portfolio['totalValue']}")
            print(f"   - 平均成本: {portfolio['avgCost']}")
        else:
            print(f"❌ 交易後投資組合查詢失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 交易後投資組合查詢異常: {e}")
    
    # 7. 查詢點數記錄
    print("\n📝 7. 查詢點數記錄...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/user/points/history?limit=10",
            headers=headers
        )
        
        if response.status_code == 200:
            logs = response.json()
            print(f"✅ 點數記錄查詢成功，共 {len(logs)} 筆記錄")
            for i, log in enumerate(logs[:3]):  # 只顯示前3筆
                print(f"   {i+1}. {log['type']}: {log['amount']} ({log['note']})")
        else:
            print(f"❌ 點數記錄查詢失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 點數記錄查詢異常: {e}")
    
    # 8. 查詢股票訂單記錄
    print("\n📋 8. 查詢股票訂單記錄...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/user/stock/orders?limit=10",
            headers=headers
        )
        
        if response.status_code == 200:
            orders = response.json()
            print(f"✅ 股票訂單記錄查詢成功，共 {len(orders)} 筆記錄")
            for i, order in enumerate(orders):
                print(f"   {i+1}. {order['side']} {order['quantity']}股 @ {order['price']} ({order['status']})")
        else:
            print(f"❌ 股票訂單記錄查詢失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 股票訂單記錄查詢異常: {e}")
    
    print("\n✅ 使用者交易功能測試完成！")
    return True


def main():
    """主函數"""
    print("="*60)
    print("🧪 使用者交易功能測試")
    print("="*60)
    
    # 檢查服務是否執行
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ 服務未正常執行，請先啟動: python main.py")
            return
    except:
        print("❌ 無法連線到服務，請先啟動: python main.py")
        return
    
    # 執行測試
    try:
        success = test_user_registration_and_trading()
        if success:
            print("\n🎉 所有測試通過！使用者交易功能正常工作。")
        else:
            print("\n⚠️  部分測試失敗，請檢查錯誤訊息。")
    except KeyboardInterrupt:
        print("\n\n👋 測試被使用者中斷")
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
    
    print("="*60)


if __name__ == "__main__":
    main()
