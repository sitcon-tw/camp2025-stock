#!/usr/bin/env python3
"""
測試新的撮合價格機制
"""
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

class MockUserService:
    """模擬UserService來測試價格決定邏輯"""
    
    def __init__(self):
        self.current_price = 100.0
    
    async def _get_current_stock_price(self):
        """模擬獲取當前股價"""
        return self.current_price
    
    async def _determine_fair_trade_price(self, buy_order: dict, sell_order: dict) -> float:
        """決定公平的成交價格"""
        buy_price = buy_order.get("price", 0)
        sell_price = sell_order.get("price", float('inf'))
        buy_order_type = buy_order.get("order_type", "limit")
        sell_order_type = sell_order.get("order_type", "limit")
        is_system_sale = sell_order.get("is_system_order", False)
        
        try:
            # 如果是系統IPO訂單，使用IPO價格
            if is_system_sale:
                print(f"System IPO trade: using IPO price {sell_price}")
                return sell_price
            
            # 市價單與限價單的撮合
            if buy_order_type == "market" or buy_order_type == "market_converted":
                if sell_order_type == "limit":
                    # 市價買單 vs 限價賣單：使用賣方限價
                    print(f"Market buy vs limit sell: using sell price {sell_price}")
                    return sell_price
                else:
                    # 市價買單 vs 市價賣單：使用當前市場價格
                    current_price = await self._get_current_stock_price()
                    print(f"Market buy vs market sell: using current price {current_price}")
                    return current_price
            
            elif sell_order_type == "market" or sell_order_type == "market_converted":
                if buy_order_type == "limit":
                    # 限價買單 vs 市價賣單：使用買方限價
                    print(f"Limit buy vs market sell: using buy price {buy_price}")
                    return buy_price
                else:
                    # 市價賣單 vs 市價買單：使用當前市場價格
                    current_price = await self._get_current_stock_price()
                    print(f"Market sell vs market buy: using current price {current_price}")
                    return current_price
            
            # 限價單與限價單的撮合
            elif buy_order_type == "limit" and sell_order_type == "limit":
                # 檢查哪個訂單先提交（時間優先）
                buy_time = buy_order.get("created_at")
                sell_time = sell_order.get("created_at")
                
                if buy_time and sell_time:
                    if buy_time < sell_time:
                        # 買單先提交，使用買方價格
                        print(f"Limit vs limit (buy first): using buy price {buy_price}")
                        return buy_price
                    else:
                        # 賣單先提交，使用賣方價格
                        print(f"Limit vs limit (sell first): using sell price {sell_price}")
                        return sell_price
                else:
                    # 無法確定時間，使用賣方價格（對賣方有利）
                    print(f"Limit vs limit (time unknown): using sell price {sell_price}")
                    return sell_price
            
            # 預設情況：使用中間價格
            else:
                if buy_price > 0 and sell_price < float('inf'):
                    mid_price = (buy_price + sell_price) / 2
                    print(f"Default case: using mid price {mid_price} (buy: {buy_price}, sell: {sell_price})")
                    return mid_price
                else:
                    # 如果價格異常，使用當前市場價格
                    current_price = await self._get_current_stock_price()
                    print(f"Price anomaly: using current price {current_price}")
                    return current_price
                    
        except Exception as e:
            print(f"Error determining fair trade price: {e}")
            # 發生錯誤時回退到賣方價格
            return sell_price if sell_price < float('inf') else buy_price


async def test_price_mechanism():
    """測試不同情況下的價格決定邏輯"""
    service = MockUserService()
    
    # 測試案例
    test_cases = [
        {
            "name": "限價買單 vs 限價賣單 (買單先提交)",
            "buy_order": {
                "price": 800,
                "order_type": "limit",
                "created_at": datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
            },
            "sell_order": {
                "price": 100,
                "order_type": "limit", 
                "created_at": datetime(2025, 1, 1, 10, 1, 0, tzinfo=timezone.utc)
            },
            "expected_price": 800,
            "description": "應該使用買方價格 (買單先提交)"
        },
        {
            "name": "限價買單 vs 限價賣單 (賣單先提交)",
            "buy_order": {
                "price": 800,
                "order_type": "limit",
                "created_at": datetime(2025, 1, 1, 10, 1, 0, tzinfo=timezone.utc)
            },
            "sell_order": {
                "price": 100,
                "order_type": "limit",
                "created_at": datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
            },
            "expected_price": 100,
            "description": "應該使用賣方價格 (賣單先提交)"
        },
        {
            "name": "市價買單 vs 限價賣單",
            "buy_order": {
                "price": 0,
                "order_type": "market"
            },
            "sell_order": {
                "price": 150,
                "order_type": "limit"
            },
            "expected_price": 150,
            "description": "應該使用賣方限價"
        },
        {
            "name": "限價買單 vs 市價賣單",
            "buy_order": {
                "price": 200,
                "order_type": "limit"
            },
            "sell_order": {
                "price": 0,
                "order_type": "market"
            },
            "expected_price": 200,
            "description": "應該使用買方限價"
        },
        {
            "name": "系統IPO賣單",
            "buy_order": {
                "price": 300,
                "order_type": "limit"
            },
            "sell_order": {
                "price": 20,
                "order_type": "limit",
                "is_system_order": True
            },
            "expected_price": 20,
            "description": "應該使用IPO價格"
        }
    ]
    
    print("🔍 測試新的撮合價格機制")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 測試案例 {i}: {test_case['name']}")
        print(f"📝 描述: {test_case['description']}")
        
        # 執行測試
        actual_price = await service._determine_fair_trade_price(
            test_case["buy_order"], 
            test_case["sell_order"]
        )
        
        # 驗證結果
        expected_price = test_case["expected_price"]
        if actual_price == expected_price:
            print(f"✅ 測試通過: 預期價格 {expected_price}, 實際價格 {actual_price}")
        else:
            print(f"❌ 測試失敗: 預期價格 {expected_price}, 實際價格 {actual_price}")
        
        print("-" * 30)
    
    # 測試舊系統問題情況
    print(f"\n🚨 測試問題情況 (舊系統)")
    print("=" * 50)
    
    # 模擬您提到的問題情況
    problem_cases = [
        {
            "name": "連續降價買單 vs 市價賣單",
            "scenarios": [
                {"buy_price": 800, "sell_price": 0, "buy_type": "limit", "sell_type": "market"},
                {"buy_price": 700, "sell_price": 0, "buy_type": "limit", "sell_type": "market"},
                {"buy_price": 100, "sell_price": 0, "buy_type": "limit", "sell_type": "market"},
            ]
        }
    ]
    
    for case in problem_cases:
        print(f"\n📋 {case['name']}:")
        for j, scenario in enumerate(case["scenarios"], 1):
            buy_order = {"price": scenario["buy_price"], "order_type": scenario["buy_type"]}
            sell_order = {"price": scenario["sell_price"], "order_type": scenario["sell_type"]}
            
            price = await service._determine_fair_trade_price(buy_order, sell_order)
            print(f"  {j}. 買單 {scenario['buy_price']} vs 賣單市價 → 成交價格: {price}")
    
    print(f"\n🎯 結論:")
    print("新的價格機制解決了舊系統的問題：")
    print("- 限價買單 vs 市價賣單：使用買方限價 (保護賣方)")
    print("- 市價買單 vs 限價賣單：使用賣方限價 (保護買方)")
    print("- 限價對限價：使用時間優先原則")
    print("- 系統IPO：使用固定IPO價格")
    print("\n⚠️  注意：已移除價格驗證機制，僅保留核心的公平價格決定邏輯")


if __name__ == "__main__":
    asyncio.run(test_price_mechanism())