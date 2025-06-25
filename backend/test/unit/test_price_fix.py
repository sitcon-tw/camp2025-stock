#!/usr/bin/env python3
"""
Test script to verify the stock price calculation fix
"""

import asyncio
import aiohttp
import json

BASE_URL = "http://localhost:8000"
ADMIN_PASSWORD = "admin123"

async def test_price_fix():
    async with aiohttp.ClientSession() as session:
        # First get admin token
        async with session.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PASSWORD}) as resp:
            if resp.status != 200:
                print("❌ Admin login failed")
                return
            admin_data = await resp.json()
            admin_token = admin_data["token"]
            print("✅ Admin login successful")
        
        # Check current stock price
        async with session.get(f"{BASE_URL}/api/price/summary") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"📊 Current stock price: {data.get('lastPrice')} 元")
            else:
                print("❌ Failed to get current price")
        
        # Check recent trades
        async with session.get(f"{BASE_URL}/api/price/recent") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"📈 Recent trades: {len(data)} trades")
                if data:
                    for i, trade in enumerate(data[:5]):
                        print(f"   {i+1}. Price: {trade['price']} 元, Quantity: {trade['quantity']}")
            else:
                print("❌ Failed to get recent trades")
        
        # Check pending orders
        async with session.get(f"{BASE_URL}/api/price/depth") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"📋 Order book:")
                print(f"   Sell orders: {len(data.get('sell', []))}")
                for order in data.get('sell', [])[:3]:
                    print(f"      Sell {order['quantity']} @ {order['price']} 元")
                print(f"   Buy orders: {len(data.get('buy', []))}")
                for order in data.get('buy', [])[:3]:
                    print(f"      Buy {order['quantity']} @ {order['price']} 元")
            else:
                print("❌ Failed to get order book")

if __name__ == "__main__":
    print("🧪 Testing stock price calculation fix...")
    asyncio.run(test_price_fix())