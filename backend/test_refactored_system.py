# 重構版本系統測試
# 目的：確保重構後的系統功能正常運作

import asyncio
import httpx
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RefactoredSystemTester:
    """
    重構系統測試器
    SRP 原則：專注於系統測試
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.test_user_token = None
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    async def setup(self):
        """初始化測試環境"""
        self.session = httpx.AsyncClient(timeout=30.0)
        logger.info("🚀 開始測試重構後的系統...")
    
    async def teardown(self):
        """清理測試環境"""
        if self.session:
            await self.session.aclose()
        logger.info("🧹 測試環境清理完成")
    
    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        """記錄測試結果"""
        if success:
            self.test_results["passed"] += 1
            logger.info(f"✅ {test_name}: 通過 - {details}")
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {details}")
            logger.error(f"❌ {test_name}: 失敗 - {details}")
    
    async def test_health_check(self):
        """測試健康檢查端點"""
        try:
            response = await self.session.get(f"{self.base_url}/api/health")
            if response.status_code == 200:
                data = response.json()
                self.log_test_result(
                    "健康檢查", 
                    True, 
                    f"版本: {data.get('version', 'unknown')}, 架構: {data.get('architecture', 'unknown')}"
                )
                return True
            else:
                self.log_test_result("健康檢查", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("健康檢查", False, str(e))
            return False
    
    async def test_architecture_info(self):
        """測試架構資訊端點"""
        try:
            response = await self.session.get(f"{self.base_url}/api/architecture")
            if response.status_code == 200:
                data = response.json()
                principles = data.get("principles_applied", {})
                expected_principles = ["SRP", "OCP", "LSP", "ISP", "DIP"]
                
                all_principles_present = all(p in principles for p in expected_principles)
                self.log_test_result(
                    "架構資訊", 
                    all_principles_present,
                    f"SOLID 原則: {', '.join(principles.keys())}"
                )
                return all_principles_present
            else:
                self.log_test_result("架構資訊", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("架構資訊", False, str(e))
            return False
    
    async def test_user_registration(self):
        """測試使用者註冊"""
        try:
            test_user_data = {
                "username": f"test_user_{int(datetime.now().timestamp())}",
                "email": "test@example.com",
                "team": "測試隊伍",
                "telegram_id": 123456789
            }
            
            response = await self.session.post(
                f"{self.base_url}/api/user/register",
                json=test_user_data
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get("success", False)
                self.log_test_result(
                    "使用者註冊", 
                    success,
                    f"用戶: {test_user_data['username']}, 訊息: {data.get('message')}"
                )
                return success, test_user_data
            else:
                self.log_test_result("使用者註冊", False, f"HTTP {response.status_code}")
                return False, None
        except Exception as e:
            self.log_test_result("使用者註冊", False, str(e))
            return False, None
    
    async def test_user_login(self, user_data: Dict[str, Any]):
        """測試使用者登入"""
        try:
            login_data = {
                "username": user_data["username"],
                "telegram_id": user_data["telegram_id"]
            }
            
            response = await self.session.post(
                f"{self.base_url}/api/user/login",
                json=login_data
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get("success", False)
                token = data.get("token")
                
                if success and token:
                    self.test_user_token = token
                    self.log_test_result(
                        "使用者登入", 
                        True,
                        f"用戶: {user_data['username']}, Token 長度: {len(token)}"
                    )
                    return True
                else:
                    self.log_test_result("使用者登入", False, "無法獲取 Token")
                    return False
            else:
                self.log_test_result("使用者登入", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("使用者登入", False, str(e))
            return False
    
    async def test_user_portfolio(self):
        """測試獲取使用者投資組合"""
        try:
            if not self.test_user_token:
                self.log_test_result("投資組合查詢", False, "無有效 Token")
                return False
            
            headers = {"Authorization": f"Bearer {self.test_user_token}"}
            response = await self.session.get(
                f"{self.base_url}/api/user/portfolio",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["username", "points", "stocks", "totalValue"]
                all_fields_present = all(field in data for field in required_fields)
                
                self.log_test_result(
                    "投資組合查詢", 
                    all_fields_present,
                    f"點數: {data.get('points', 0)}, 持股: {data.get('stocks', 0)}"
                )
                return all_fields_present
            else:
                self.log_test_result("投資組合查詢", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("投資組合查詢", False, str(e))
            return False
    
    async def test_ipo_purchase(self):
        """測試 IPO 購買"""
        try:
            if not self.test_user_token:
                self.log_test_result("IPO 購買", False, "無有效 Token")
                return False
            
            headers = {"Authorization": f"Bearer {self.test_user_token}"}
            response = await self.session.post(
                f"{self.base_url}/api/user/stock/ipo?quantity=1",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get("success", False)
                self.log_test_result(
                    "IPO 購買", 
                    success,
                    f"訊息: {data.get('message')}, 執行價格: {data.get('executed_price')}"
                )
                return success
            else:
                self.log_test_result("IPO 購買", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("IPO 購買", False, str(e))
            return False
    
    async def test_stock_order(self):
        """測試股票下單"""
        try:
            if not self.test_user_token:
                self.log_test_result("股票下單", False, "無有效 Token")
                return False
            
            order_data = {
                "order_type": "market",
                "side": "sell",
                "quantity": 1
            }
            
            headers = {"Authorization": f"Bearer {self.test_user_token}"}
            response = await self.session.post(
                f"{self.base_url}/api/user/stock/order",
                json=order_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get("success", False)
                self.log_test_result(
                    "股票下單", 
                    success,
                    f"訊息: {data.get('message')}, 訂單ID: {data.get('order_id')}"
                )
                return success
            else:
                self.log_test_result("股票下單", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("股票下單", False, str(e))
            return False
    
    async def test_user_orders_history(self):
        """測試訂單歷史查詢"""
        try:
            if not self.test_user_token:
                self.log_test_result("訂單歷史", False, "無有效 Token")
                return False
            
            headers = {"Authorization": f"Bearer {self.test_user_token}"}
            response = await self.session.get(
                f"{self.base_url}/api/user/stock/orders",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                is_list = isinstance(data, list)
                self.log_test_result(
                    "訂單歷史", 
                    is_list,
                    f"訂單數量: {len(data) if is_list else 0}"
                )
                return is_list
            else:
                self.log_test_result("訂單歷史", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("訂單歷史", False, str(e))
            return False
    
    async def test_service_health(self):
        """測試使用者服務健康狀態"""
        try:
            response = await self.session.get(f"{self.base_url}/api/user/health")
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                is_healthy = status == "healthy"
                self.log_test_result(
                    "服務健康檢查", 
                    is_healthy,
                    f"狀態: {status}, 訊息: {data.get('message')}"
                )
                return is_healthy
            else:
                self.log_test_result("服務健康檢查", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("服務健康檢查", False, str(e))
            return False
    
    async def run_all_tests(self):
        """執行所有測試"""
        await self.setup()
        
        try:
            # 基礎測試
            logger.info("📋 執行基礎功能測試...")
            await self.test_health_check()
            await self.test_architecture_info()
            await self.test_service_health()
            
            # 使用者功能測試
            logger.info("👤 執行使用者功能測試...")
            success, user_data = await self.test_user_registration()
            
            if success and user_data:
                login_success = await self.test_user_login(user_data)
                
                if login_success:
                    await self.test_user_portfolio()
                    await self.test_ipo_purchase()
                    await self.test_stock_order()
                    await self.test_user_orders_history()
            
            # 輸出測試結果
            self.print_test_summary()
            
        finally:
            await self.teardown()
    
    def print_test_summary(self):
        """輸出測試摘要"""
        total_tests = self.test_results["passed"] + self.test_results["failed"]
        success_rate = (self.test_results["passed"] / total_tests * 100) if total_tests > 0 else 0
        
        logger.info("\n" + "="*60)
        logger.info("📊 重構系統測試結果摘要")
        logger.info("="*60)
        logger.info(f"總測試數量: {total_tests}")
        logger.info(f"通過測試: {self.test_results['passed']}")
        logger.info(f"失敗測試: {self.test_results['failed']}")
        logger.info(f"成功率: {success_rate:.1f}%")
        
        if self.test_results["errors"]:
            logger.info("\n❌ 失敗的測試:")
            for error in self.test_results["errors"]:
                logger.info(f"  - {error}")
        
        if success_rate >= 80:
            logger.info("\n🎉 重構系統測試整體表現良好！")
        elif success_rate >= 60:
            logger.info("\n⚠️  重構系統需要一些調整")
        else:
            logger.info("\n🚨 重構系統存在嚴重問題，需要修復")
        
        logger.info("="*60)


# 獨立測試函數
async def test_import_dependencies():
    """測試重構後的依賴是否能正常導入"""
    logger.info("🔍 測試模組導入...")
    
    try:
        # 測試領域層
        from app.domain.entities import User, Stock, StockOrder, Transfer
        from app.domain.repositories import UserRepository, StockRepository
        from app.domain.services import UserDomainService, StockTradingService
        from app.domain.strategies import MarketOrderStrategy, LimitOrderStrategy
        
        # 測試應用層
        from app.application.services import UserApplicationService, TradingApplicationService
        from app.application.dependencies import get_service_container
        
        # 測試基礎設施層
        from app.infrastructure.mongodb_repositories import MongoUserRepository
        
        # 測試核心層
        from app.core.base_classes import BaseEntity, BaseRepository
        from app.core.config_refactored import config
        
        logger.info("✅ 所有重構模組導入成功")
        return True
        
    except ImportError as e:
        logger.error(f"❌ 模組導入失敗: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 模組導入錯誤: {e}")
        return False


async def main():
    """主測試函數"""
    logger.info("🧪 開始重構版本系統測試")
    
    # 1. 測試模組導入
    import_success = await test_import_dependencies()
    
    if not import_success:
        logger.error("💥 基礎模組導入失敗，無法進行進一步測試")
        return
    
    # 2. 測試 API 端點
    tester = RefactoredSystemTester()
    await tester.run_all_tests()
    
    logger.info("🏁 重構版本系統測試完成")


if __name__ == "__main__":
    asyncio.run(main())