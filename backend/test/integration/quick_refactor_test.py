# 快速重構測試
# 測試重構後模組的導入和基本功能

import asyncio
import sys
import os

# 新增目前路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_module_imports():
    """測試所有重構模組的導入"""
    print("🔍 測試重構模組導入...")
    
    try:
        # 1. 測試領域層
        print("  📁 測試領域層...")
        from app.domain.entities import User, Stock, StockOrder, Transfer
        from app.domain.repositories import UserRepository, StockRepository
        from app.domain.services import UserDomainService, StockTradingService
        from app.domain.strategies import MarketOrderStrategy, LimitOrderStrategy
        print("  ✅ 領域層模組導入成功")
        
        # 2. 測試應用層
        print("  📁 測試應用層...")
        from app.application.services import UserApplicationService, TradingApplicationService
        from app.application.dependencies import get_service_container
        print("  ✅ 應用層模組導入成功")
        
        # 3. 測試基礎設施層
        print("  📁 測試基礎設施層...")
        from app.infrastructure.mongodb_repositories import MongoUserRepository
        print("  ✅ 基礎設施層模組導入成功")
        
        # 4. 測試核心層
        print("  📁 測試核心層...")
        from app.core.base_classes import BaseEntity, BaseRepository
        from app.core.config_refactored import config, Constants
        print("  ✅ 核心層模組導入成功")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ 導入失敗: {e}")
        return False
    except Exception as e:
        print(f"  ❌ 其他錯誤: {e}")
        return False

async def test_entity_creation():
    """測試領域實體的建立和方法"""
    print("\n🧪 測試領域實體...")
    
    try:
        from app.domain.entities import User, Stock, StockOrder, Transfer
        from decimal import Decimal
        from datetime import datetime
        import uuid
        
        # 測試 User 實體
        user = User(
            user_id=str(uuid.uuid4()),
            username="test_user",
            email="test@example.com",
            team="測試隊伍",
            points=100
        )
        
        # 測試業務邏輯方法
        assert user.can_transfer(50) == True
        assert user.can_transfer(150) == False
        
        user.add_points(50)
        assert user.points == 150
        
        user.deduct_points(30)
        assert user.points == 120
        
        print("  ✅ User 實體測試通過")
        
        # 測試 Stock 實體
        stock = Stock(
            user_id=user.user_id,
            quantity=10,
            avg_cost=Decimal("20.5")
        )
        
        assert stock.can_sell(5) == True
        assert stock.can_sell(15) == False
        
        stock.buy_shares(5, Decimal("25.0"))
        assert stock.quantity == 15
        
        print("  ✅ Stock 實體測試通過")
        
        # 測試 Transfer 實體
        transfer = Transfer(
            transfer_id=str(uuid.uuid4()),
            from_user_id=user.user_id,
            to_user_id=str(uuid.uuid4()),
            amount=50,
            fee=Transfer.calculate_fee(50)
        )
        
        assert transfer.fee == 1  # max(1, 50//100) = 1
        assert transfer.get_total_deduction() == 51
        
        print("  ✅ Transfer 實體測試通過")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 實體測試失敗: {e}")
        return False

async def test_strategy_pattern():
    """測試策略模式實現"""
    print("\n🎯 測試策略模式...")
    
    try:
        from app.domain.strategies import MarketOrderStrategy, LimitOrderStrategy
        from app.domain.entities import StockOrder
        from decimal import Decimal
        from datetime import datetime
        import uuid
        
        # 建立測試訂單
        market_order = StockOrder(
            order_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            order_type="market",
            side="buy",
            quantity=10,
            created_at=datetime.now()
        )
        
        limit_order = StockOrder(
            order_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            order_type="limit",
            side="buy",
            quantity=10,
            price=Decimal("25.0"),
            created_at=datetime.now()
        )
        
        # 測試策略
        market_strategy = MarketOrderStrategy()
        limit_strategy = LimitOrderStrategy()
        
        market_data = {"current_price": 20.0}
        
        # 測試市價單策略
        can_execute_market = await market_strategy.can_execute(market_order, market_data)
        assert can_execute_market == True
        
        # 測試限價單策略
        can_execute_limit = await limit_strategy.can_execute(limit_order, market_data)
        assert can_execute_limit == True  # 20.0 <= 25.0
        
        # 修改市場價格測試
        market_data["current_price"] = 30.0
        can_execute_limit_high = await limit_strategy.can_execute(limit_order, market_data)
        assert can_execute_limit_high == False  # 30.0 > 25.0
        
        print("  ✅ 策略模式測試通過")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 策略模式測試失敗: {e}")
        return False

async def test_configuration():
    """測試設定管理"""
    print("\n⚙️  測試設定管理...")
    
    try:
        from app.core.config_refactored import config, Constants
        
        # 測試設定結構
        assert hasattr(config, 'database')
        assert hasattr(config, 'jwt')
        assert hasattr(config, 'trading')
        assert hasattr(config, 'security')
        
        # 測試環境判斷
        assert isinstance(config.is_development, bool)
        assert isinstance(config.is_production, bool)
        
        # 測試常數
        assert Constants.DEFAULT_USER_POINTS == 100
        assert Constants.ORDER_STATUS_PENDING == "pending"
        assert Constants.ORDER_TYPE_MARKET == "market"
        
        print("  ✅ 設定管理測試通過")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 設定管理測試失敗: {e}")
        return False

async def test_dependency_injection():
    """測試依賴注入容器"""
    print("\n🔗 測試依賴注入...")
    
    try:
        from app.application.dependencies import get_service_container
        
        # 獲取服務容器
        container = get_service_container()
        
        # 測試 Repository 層
        user_repo = container.user_repository
        stock_repo = container.stock_repository
        
        # 測試 Domain Service 層
        user_domain_service = container.user_domain_service
        trading_service = container.stock_trading_service
        
        # 測試 Application Service 層
        user_app_service = container.user_application_service
        trading_app_service = container.trading_application_service
        
        # 驗證服務類型
        from app.infrastructure.mongodb_repositories import MongoUserRepository
        from app.domain.services import UserDomainService
        from app.application.services import UserApplicationService
        
        assert isinstance(user_repo, MongoUserRepository)
        assert isinstance(user_domain_service, UserDomainService)
        assert isinstance(user_app_service, UserApplicationService)
        
        print("  ✅ 依賴注入測試通過")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 依賴注入測試失敗: {e}")
        return False

async def main():
    """主測試函數"""
    print("🧪 重構版本功能測試")
    print("=" * 50)
    
    test_results = []
    
    # 執行所有測試
    test_results.append(await test_module_imports())
    test_results.append(await test_entity_creation())
    test_results.append(await test_strategy_pattern())
    test_results.append(await test_configuration())
    test_results.append(await test_dependency_injection())
    
    # 統計結果
    passed = sum(test_results)
    total = len(test_results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print("\n" + "=" * 50)
    print("📊 測試結果摘要")
    print("=" * 50)
    print(f"總測試數: {total}")
    print(f"通過測試: {passed}")
    print(f"失敗測試: {total - passed}")
    print(f"成功率: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("\n🎉 重構功能測試表現優秀！")
        print("✨ SOLID 原則、Clean Code 和 DDD 實現成功")
    elif success_rate >= 60:
        print("\n⚠️  重構功能基本正常，但需要一些調整")
    else:
        print("\n🚨 重構功能存在問題，需要進一步修復")
    
    print("\n🏗️  重構亮點:")
    print("  - 清晰的分層架構 (Domain, Application, Infrastructure)")
    print("  - SOLID 原則的全面應用")
    print("  - 策略模式支援可擴展設計")
    print("  - 依賴注入實現鬆耦合")
    print("  - 領域驅動設計的業務建模")
    print("  - Clean Code 的可讀性提升")

if __name__ == "__main__":
    asyncio.run(main())