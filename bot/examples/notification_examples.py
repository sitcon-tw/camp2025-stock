"""
Telegram Bot DM 通知功能使用範例
"""

import asyncio
import httpx
from os import environ
from dotenv import load_dotenv

load_dotenv()

# 設定
BACKEND_TOKEN = environ.get("BACKEND_TOKEN")
BOT_BASE_URL = "http://localhost:8000"  # 根據實際部署調整
HEADERS = {"Authorization": f"Bearer {BACKEND_TOKEN}"}


async def example_send_dm():
    """傳送簡單 DM 的範例"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BOT_BASE_URL}/notifications/dm/send",
            headers=HEADERS,
            json={
                "user_id": 123456789,  # 替換為實際的 Telegram 使用者 ID
                "message": "🔔 *測試通知*\n\n這是一個測試私人訊息\\!",
                "parse_mode": "MarkdownV2"
            }
        )
        print(f"Send DM Response: {response.status_code} - {response.json()}")


async def example_bulk_dm():
    """批量傳送 DM 的範例"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BOT_BASE_URL}/notifications/dm/bulk",
            headers=HEADERS,
            json={
                "user_ids": [123456789, 987654321],  # 替換為實際的使用者 ID 列表
                "message": "📢 *批量通知*\n\n這是一個批量傳送的測試訊息\\!",
                "parse_mode": "MarkdownV2",
                "delay_seconds": 0.5
            }
        )
        print(f"Bulk DM Response: {response.status_code} - {response.json()}")


async def example_trade_notification():
    """交易通知範例"""
    async with httpx.AsyncClient() as client:
        # 範例1: 使用預設的 SITC 股票代號（推薦用法）
        response1 = await client.post(
            f"{BOT_BASE_URL}/notifications/notification/trade",
            headers=HEADERS,
            json={
                "user_id": 123456789,
                "action": "buy",
                "quantity": 10,
                "price": 150.50,
                "total_amount": 1505.00,
                "order_id": "ORDER123456"
            }
        )
        print(f"Trade Notification (默認 SITC): {response1.status_code} - {response1.json()}")
        
        # 範例2: 明確指定 SITC 股票代號（也可以這樣用）
        response2 = await client.post(
            f"{BOT_BASE_URL}/notifications/notification/trade",
            headers=HEADERS,
            json={
                "user_id": 123456789,
                "action": "sell",
                "stock_symbol": "SITC",
                "quantity": 5,
                "price": 155.25,
                "total_amount": 776.25,
                "order_id": "ORDER789012"
            }
        )
        print(f"Trade Notification (指定 SITC): {response2.status_code} - {response2.json()}")


async def example_transfer_notification():
    """轉帳通知範例"""
    async with httpx.AsyncClient() as client:
        # 傳送者通知
        response1 = await client.post(
            f"{BOT_BASE_URL}/notifications/notification/transfer",
            headers=HEADERS,
            json={
                "user_id": 123456789,
                "transfer_type": "sent",
                "amount": 100.00,
                "other_user": "UserB",
                "transfer_id": "TRANS123456"
            }
        )
        
        # 接收者通知
        response2 = await client.post(
            f"{BOT_BASE_URL}/notifications/notification/transfer",
            headers=HEADERS,
            json={
                "user_id": 987654321,
                "transfer_type": "received",
                "amount": 100.00,
                "other_user": "UserA",
                "transfer_id": "TRANS123456"
            }
        )
        
        print(f"Transfer Notification (Sender): {response1.status_code} - {response1.json()}")
        print(f"Transfer Notification (Receiver): {response2.status_code} - {response2.json()}")


async def example_system_notification():
    """系統通知範例"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BOT_BASE_URL}/notifications/notification/system",
            headers=HEADERS,
            json={
                "user_id": 123456789,
                "title": "系統維護通知",
                "content": "系統將於今晚 23:00 進行維護，預計維護時間 2 小時。",
                "priority": "high"
            }
        )
        print(f"System Notification Response: {response.status_code} - {response.json()}")


async def example_custom_notification():
    """自定義通知範例"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BOT_BASE_URL}/notifications/notification/send",
            headers=HEADERS,
            json={
                "user_id": 123456789,
                "notification_type": "promotion",
                "title": "限時優惠",
                "content": "現在註冊即可獲得 100 元獎勵金！",
                "additional_data": {
                    "優惠代碼": "WELCOME100",
                    "有效期限": "2024-12-31",
                    "適用對象": "新使用者"
                }
            }
        )
        print(f"Custom Notification Response: {response.status_code} - {response.json()}")


async def example_health_check():
    """健康檢查範例"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BOT_BASE_URL}/notifications/health")
        print(f"Health Check Response: {response.status_code} - {response.json()}")


async def main():
    """執行所有範例"""
    print("=== Telegram Bot DM 通知功能測試 ===\n")
    
    try:
        # 健康檢查
        print("1. 健康檢查...")
        await example_health_check()
        print()
        
        # 簡單 DM
        print("2. 傳送簡單 DM...")
        await example_send_dm()
        print()
        
        # 交易通知
        print("3. 傳送交易通知...")
        await example_trade_notification()
        print()
        
        # 轉帳通知
        print("4. 傳送轉帳通知...")
        await example_transfer_notification()
        print()
        
        # 系統通知
        print("5. 傳送系統通知...")
        await example_system_notification()
        print()
        
        # 自定義通知
        print("6. 傳送自定義通知...")
        await example_custom_notification()
        print()
        
        # 批量 DM (謹慎使用)
        print("7. 傳送批量 DM...")
        await example_bulk_dm()
        print()
        
    except Exception as e:
        print(f"錯誤: {e}")


if __name__ == "__main__":
    asyncio.run(main())