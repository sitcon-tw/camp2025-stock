#!/usr/bin/env python3
"""
圈存系統測試腳本
測試圈存系統的完整性和安全性
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config_refactored import config
from app.core.database import Collections
from app.services.escrow_service import EscrowService
from app.core.exceptions import InsufficientPointsException, EscrowException
from bson import ObjectId
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EscrowSystemTester:
    def __init__(self):
        self.client = None
        self.db = None
        self.escrow_service = None
        
    async def setup(self):
        """設置測試環境"""
        try:
            # 連接到 MongoDB
            self.client = AsyncIOMotorClient(config.database.mongo_uri)
            self.db = self.client[config.database.database_name]
            
            # 測試連接
            await self.client.admin.command('ismaster')
            logger.info(f"Connected to MongoDB database: {config.database.database_name}")
            
            # 初始化圈存服務
            self.escrow_service = EscrowService(self.db)
            
            # 創建測試用戶
            await self.create_test_user()
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            raise
    
    async def create_test_user(self):
        """創建測試用戶"""
        test_user = {
            "_id": "test_user_escrow",
            "id": "test_user_escrow",
            "name": "圈存測試用戶",
            "telegram_id": "test_escrow_123",
            "team": "測試團隊",
            "points": 1000,
            "escrow_amount": 0,
            "enabled": True
        }
        
        # 如果用戶已存在，更新餘額
        await self.db[Collections.USERS].update_one(
            {"_id": "test_user_escrow"},
            {"$set": test_user},
            upsert=True
        )
        
        logger.info("Test user created/updated with 1000 points")
    
    async def test_basic_escrow_operations(self):
        """測試基本圈存操作"""
        logger.info("=== Testing Basic Escrow Operations ===")
        
        user_id = "test_user_escrow"
        
        try:
            # 測試創建圈存
            logger.info("Testing escrow creation...")
            escrow_id = await self.escrow_service.create_escrow(
                user_id=user_id,
                amount=100,
                escrow_type="test_order",
                metadata={"test": "basic_operation"}
            )
            logger.info(f"✅ Escrow created: {escrow_id}")
            
            # 驗證用戶餘額變化
            user = await self.db[Collections.USERS].find_one({"_id": user_id})
            assert user["points"] == 900, f"Expected 900 points, got {user['points']}"
            assert user["escrow_amount"] == 100, f"Expected 100 escrow, got {user['escrow_amount']}"
            logger.info("✅ User balance updated correctly")
            
            # 測試完成圈存
            logger.info("Testing escrow completion...")
            success = await self.escrow_service.complete_escrow(escrow_id, 100)
            assert success, "Escrow completion failed"
            
            # 驗證圈存完成後的狀態
            user = await self.db[Collections.USERS].find_one({"_id": user_id})
            assert user["escrow_amount"] == 0, f"Expected 0 escrow, got {user['escrow_amount']}"
            logger.info("✅ Escrow completed successfully")
            
            # 測試部分退款的圈存
            logger.info("Testing partial refund escrow...")
            escrow_id2 = await self.escrow_service.create_escrow(
                user_id=user_id,
                amount=200,
                escrow_type="test_partial",
                metadata={"test": "partial_refund"}
            )
            
            # 只消費150，應該退還50
            success = await self.escrow_service.complete_escrow(escrow_id2, 150)
            assert success, "Partial escrow completion failed"
            
            user = await self.db[Collections.USERS].find_one({"_id": user_id})
            assert user["points"] == 750, f"Expected 750 points, got {user['points']}"  # 900 - 150
            assert user["escrow_amount"] == 0, f"Expected 0 escrow, got {user['escrow_amount']}"
            logger.info("✅ Partial refund escrow completed successfully")
            
            logger.info("=== Basic Escrow Operations Test PASSED ===")
            
        except Exception as e:
            logger.error(f"Basic escrow operations test failed: {e}")
            return False
        
        return True
    
    async def test_insufficient_funds(self):
        """測試餘額不足情況"""
        logger.info("=== Testing Insufficient Funds ===")
        
        user_id = "test_user_escrow"
        
        try:
            # 獲取當前餘額
            user = await self.db[Collections.USERS].find_one({"_id": user_id})
            current_points = user["points"]
            
            # 嘗試圈存超過餘額的金額
            logger.info(f"Attempting to escrow {current_points + 100} points (more than available {current_points})")
            
            try:
                await self.escrow_service.create_escrow(
                    user_id=user_id,
                    amount=current_points + 100,
                    escrow_type="test_insufficient",
                    metadata={"test": "insufficient_funds"}
                )
                logger.error("❌ Should have failed with insufficient funds")
                return False
            except InsufficientPointsException:
                logger.info("✅ Correctly rejected insufficient funds")
            
            # 驗證用戶餘額未改變
            user_after = await self.db[Collections.USERS].find_one({"_id": user_id})
            assert user_after["points"] == current_points, "User points should not change on failed escrow"
            assert user_after["escrow_amount"] == 0, "User escrow amount should not change on failed escrow"
            
            logger.info("=== Insufficient Funds Test PASSED ===")
            
        except Exception as e:
            logger.error(f"Insufficient funds test failed: {e}")
            return False
        
        return True
    
    async def test_escrow_cancellation(self):
        """測試圈存取消"""
        logger.info("=== Testing Escrow Cancellation ===")
        
        user_id = "test_user_escrow"
        
        try:
            # 創建圈存
            escrow_id = await self.escrow_service.create_escrow(
                user_id=user_id,
                amount=300,
                escrow_type="test_cancel",
                metadata={"test": "cancellation"}
            )
            
            # 記錄圈存前的狀態
            user_before = await self.db[Collections.USERS].find_one({"_id": user_id})
            points_before = user_before["points"]
            
            # 取消圈存
            success = await self.escrow_service.cancel_escrow(escrow_id, "test_cancellation")
            assert success, "Escrow cancellation failed"
            
            # 驗證資金已退還
            user_after = await self.db[Collections.USERS].find_one({"_id": user_id})
            assert user_after["points"] == points_before + 300, "Points should be refunded"
            assert user_after["escrow_amount"] == 0, "Escrow amount should be 0 after cancellation"
            
            logger.info("✅ Escrow cancelled and funds refunded successfully")
            
            logger.info("=== Escrow Cancellation Test PASSED ===")
            
        except Exception as e:
            logger.error(f"Escrow cancellation test failed: {e}")
            return False
        
        return True
    
    async def test_concurrent_escrows(self):
        """測試並發圈存操作"""
        logger.info("=== Testing Concurrent Escrows ===")
        
        user_id = "test_user_escrow"
        
        try:
            # 創建多個圈存
            escrow_ids = []
            for i in range(5):
                escrow_id = await self.escrow_service.create_escrow(
                    user_id=user_id,
                    amount=50,
                    escrow_type="test_concurrent",
                    metadata={"test": f"concurrent_{i}"}
                )
                escrow_ids.append(escrow_id)
            
            # 驗證用戶狀態
            user = await self.db[Collections.USERS].find_one({"_id": user_id})
            assert user["escrow_amount"] == 250, f"Expected 250 total escrow, got {user['escrow_amount']}"
            
            # 完成部分圈存
            await self.escrow_service.complete_escrow(escrow_ids[0], 50)
            await self.escrow_service.complete_escrow(escrow_ids[1], 50)
            
            # 取消部分圈存
            await self.escrow_service.cancel_escrow(escrow_ids[2], "test_cancel")
            await self.escrow_service.cancel_escrow(escrow_ids[3], "test_cancel")
            
            # 驗證最終狀態
            user_final = await self.db[Collections.USERS].find_one({"_id": user_id})
            assert user_final["escrow_amount"] == 50, f"Expected 50 remaining escrow, got {user_final['escrow_amount']}"
            
            # 清理剩餘圈存
            await self.escrow_service.cancel_escrow(escrow_ids[4], "cleanup")
            
            logger.info("✅ Concurrent escrows handled correctly")
            
            logger.info("=== Concurrent Escrows Test PASSED ===")
            
        except Exception as e:
            logger.error(f"Concurrent escrows test failed: {e}")
            return False
        
        return True
    
    async def test_escrow_statistics(self):
        """測試圈存統計功能"""
        logger.info("=== Testing Escrow Statistics ===")
        
        user_id = "test_user_escrow"
        
        try:
            # 創建不同類型的圈存記錄
            escrow_types = ["stock_order", "pvp_battle", "transfer"]
            escrow_ids = []
            
            for escrow_type in escrow_types:
                escrow_id = await self.escrow_service.create_escrow(
                    user_id=user_id,
                    amount=100,
                    escrow_type=escrow_type,
                    metadata={"test": f"stats_{escrow_type}"}
                )
                escrow_ids.append(escrow_id)
            
            # 測試用戶圈存查詢
            user_escrows = await self.escrow_service.get_user_escrows(user_id)
            assert len(user_escrows) >= 3, "Should have at least 3 escrows"
            
            # 測試活躍圈存查詢
            active_escrows = await self.escrow_service.get_user_escrows(user_id, "active")
            assert len(active_escrows) == 3, "Should have 3 active escrows"
            
            # 測試圈存總額計算
            total_escrow = await self.escrow_service.get_user_total_escrow(user_id)
            assert total_escrow == 300, f"Expected 300 total escrow, got {total_escrow}"
            
            # 清理測試圈存
            for escrow_id in escrow_ids:
                await self.escrow_service.cancel_escrow(escrow_id, "test_cleanup")
            
            logger.info("✅ Escrow statistics working correctly")
            
            logger.info("=== Escrow Statistics Test PASSED ===")
            
        except Exception as e:
            logger.error(f"Escrow statistics test failed: {e}")
            return False
        
        return True
    
    async def test_data_integrity(self):
        """測試資料完整性"""
        logger.info("=== Testing Data Integrity ===")
        
        user_id = "test_user_escrow"
        
        try:
            # 獲取初始狀態
            user_initial = await self.db[Collections.USERS].find_one({"_id": user_id})
            initial_points = user_initial["points"]
            
            # 執行一系列操作
            operations = []
            
            # 創建圈存
            escrow_id1 = await self.escrow_service.create_escrow(user_id, 100, "test_integrity1")
            operations.append(("create", 100))
            
            # 部分完成圈存
            await self.escrow_service.complete_escrow(escrow_id1, 80)
            operations.append(("complete", 80))
            
            # 創建另一個圈存
            escrow_id2 = await self.escrow_service.create_escrow(user_id, 150, "test_integrity2")
            operations.append(("create", 150))
            
            # 取消圈存
            await self.escrow_service.cancel_escrow(escrow_id2, "test_integrity")
            operations.append(("cancel", 150))
            
            # 驗證最終狀態
            user_final = await self.db[Collections.USERS].find_one({"_id": user_id})
            expected_points = initial_points - 80  # 只有80點被實際消費
            
            assert user_final["points"] == expected_points, f"Points mismatch: expected {expected_points}, got {user_final['points']}"
            assert user_final["escrow_amount"] == 0, f"Escrow amount should be 0, got {user_final['escrow_amount']}"
            
            logger.info("✅ Data integrity maintained across operations")
            
            logger.info("=== Data Integrity Test PASSED ===")
            
        except Exception as e:
            logger.error(f"Data integrity test failed: {e}")
            return False
        
        return True
    
    async def cleanup(self):
        """清理測試環境"""
        try:
            # 清理測試用戶
            await self.db[Collections.USERS].delete_one({"_id": "test_user_escrow"})
            
            # 清理測試圈存記錄
            await self.db[Collections.ESCROWS].delete_many({"user_id": "test_user_escrow"})
            
            # 清理測試圈存日誌
            await self.db[Collections.ESCROW_LOGS].delete_many({"user_id": "test_user_escrow"})
            
            logger.info("Test environment cleaned up")
            
            if self.client:
                self.client.close()
                
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    async def run_all_tests(self):
        """運行所有測試"""
        logger.info("Starting Escrow System Tests...")
        
        test_results = []
        
        test_methods = [
            ("Basic Escrow Operations", self.test_basic_escrow_operations),
            ("Insufficient Funds", self.test_insufficient_funds),
            ("Escrow Cancellation", self.test_escrow_cancellation),
            ("Concurrent Escrows", self.test_concurrent_escrows),
            ("Escrow Statistics", self.test_escrow_statistics),
            ("Data Integrity", self.test_data_integrity),
        ]
        
        for test_name, test_method in test_methods:
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"Running: {test_name}")
                result = await test_method()
                test_results.append((test_name, result))
                if result:
                    logger.info(f"✅ {test_name} PASSED")
                else:
                    logger.error(f"❌ {test_name} FAILED")
            except Exception as e:
                logger.error(f"❌ {test_name} ERROR: {e}")
                test_results.append((test_name, False))
        
        # 測試結果總結
        logger.info(f"\n{'='*60}")
        logger.info("TEST SUMMARY:")
        logger.info(f"{'='*60}")
        
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "PASSED" if result else "FAILED"
            logger.info(f"{test_name:.<40} {status}")
        
        logger.info(f"{'='*60}")
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {total - passed}")
        logger.info(f"Success Rate: {passed/total*100:.1f}%")
        
        return passed == total

async def main():
    """主測試函數"""
    tester = EscrowSystemTester()
    
    try:
        await tester.setup()
        success = await tester.run_all_tests()
        
        if success:
            logger.info("\n🎉 All tests passed! Escrow system is working correctly.")
            sys.exit(0)
        else:
            logger.error("\n❌ Some tests failed. Please check the system.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())