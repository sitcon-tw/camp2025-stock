#!/usr/bin/env python3
"""
測試市場開關狀態一致性
"""
import asyncio
import os
import sys

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.user_service import UserService
from app.services.public_service import PublicService
from app.services.admin_service import AdminService
from app.core.database import get_database

async def test_market_consistency():
    """測試不同服務中市場狀態的一致性"""
    db = get_database()
    
    # 初始化服務
    user_service = UserService(db)
    public_service = PublicService(db)
    admin_service = AdminService(db)
    
    print("=== 市場狀態一致性測試 ===")
    
    # 測試手動收盤
    print("\n1. 執行手動收盤...")
    close_result = await admin_service.close_market()
    print(f"收盤結果: {close_result}")
    
    # 檢查各服務的市場狀態
    print("\n2. 檢查各服務的市場狀態...")
    
    # UserService 狀態
    user_market_open = await user_service._is_market_open()
    print(f"UserService._is_market_open(): {user_market_open}")
    
    # PublicService 狀態
    public_market_open = await public_service._is_market_open()
    print(f"PublicService._is_market_open(): {public_market_open}")
    
    # AdminService 狀態
    admin_status = await admin_service.get_manual_market_status()
    print(f"AdminService.get_manual_market_status(): {admin_status}")
    
    # PublicService 市場價格資訊
    market_price_info = await public_service.get_market_price_info()
    print(f"PublicService.get_market_price_info().marketIsOpen: {market_price_info.marketIsOpen}")
    
    # 檢查一致性
    print("\n3. 一致性檢查...")
    all_services_consistent = (
        user_market_open == public_market_open == 
        admin_status.get('is_open', False) == 
        market_price_info.marketIsOpen
    )
    
    if all_services_consistent:
        print("✅ 所有服務的市場狀態一致！")
        print(f"統一狀態: {'開盤中' if user_market_open else '已收盤'}")
    else:
        print("❌ 市場狀態不一致！")
        print("詳細狀態:")
        print(f"  UserService: {user_market_open}")
        print(f"  PublicService: {public_market_open}")
        print(f"  AdminService: {admin_status.get('is_open', False)}")
        print(f"  MarketPriceInfo: {market_price_info.marketIsOpen}")
    
    # 測試手動開盤
    print("\n4. 測試手動開盤...")
    open_result = await admin_service.open_market()
    print(f"開盤結果: {open_result}")
    
    # 再次檢查狀態
    user_market_open_2 = await user_service._is_market_open()
    public_market_open_2 = await public_service._is_market_open()
    admin_status_2 = await admin_service.get_manual_market_status()
    market_price_info_2 = await public_service.get_market_price_info()
    
    print("\n5. 開盤後狀態檢查...")
    all_services_consistent_2 = (
        user_market_open_2 == public_market_open_2 == 
        admin_status_2.get('is_open', False) == 
        market_price_info_2.marketIsOpen
    )
    
    if all_services_consistent_2:
        print("✅ 開盤後所有服務的市場狀態一致！")
        print(f"統一狀態: {'開盤中' if user_market_open_2 else '已收盤'}")
    else:
        print("❌ 開盤後市場狀態不一致！")

if __name__ == "__main__":
    asyncio.run(test_market_consistency())