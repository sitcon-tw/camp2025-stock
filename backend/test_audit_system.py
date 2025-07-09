#!/usr/bin/env python3
"""
測試審計記錄系統
驗證操作者資訊是否正確記錄和顯示
"""

import asyncio
import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.admin_service import AdminService
from app.schemas.public import GivePointsRequest
from app.core.database import get_database, Collections
from motor.motor_asyncio import AsyncIOMotorClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_audit_system():
    """測試審計記錄系統"""
    try:
        # 連接資料庫
        db = get_database()
        admin_service = AdminService(db)
        
        # 模擬管理員資訊
        admin_user = {
            "user_id": "test_admin_001",
            "username": "test_admin",
            "role": "admin"
        }
        
        logger.info("🧪 開始測試審計記錄系統...")
        
        # 測試 1: 給予點數操作（個人）
        logger.info("📝 測試 1: 給予個人點數...")
        give_points_request = GivePointsRequest(
            username="test_user",
            type="user",
            amount=100
        )
        
        try:
            result = await admin_service.give_points(give_points_request, admin_user)
            logger.info(f"✅ 給予個人點數測試完成: {result.message}")
        except Exception as e:
            logger.info(f"ℹ️ 給予個人點數測試 (預期可能失敗，使用者可能不存在): {e}")
        
        # 測試 2: 查詢點數日誌
        logger.info("📝 測試 2: 查詢點數日誌...")
        try:
            point_logs = await admin_service.get_all_point_logs(10)
            logger.info(f"✅ 查詢到 {len(point_logs)} 筆點數日誌")
            
            # 檢查最新的日誌是否包含操作者資訊
            if point_logs:
                latest_log = point_logs[0]
                logger.info(f"📋 最新日誌資訊:")
                logger.info(f"   - 用戶ID: {latest_log.user_id}")
                logger.info(f"   - 操作類型: {latest_log.type}")
                logger.info(f"   - 操作者: {latest_log.performed_by}")
                logger.info(f"   - 管理員資訊: {latest_log.admin_info}")
        except Exception as e:
            logger.error(f"❌ 查詢點數日誌失敗: {e}")
        
        # 測試 3: 查詢圈存日誌
        logger.info("📝 測試 3: 查詢圈存日誌...")
        try:
            escrow_logs = await admin_service.get_all_escrow_logs(10)
            logger.info(f"✅ 查詢到 {len(escrow_logs)} 筆圈存日誌")
            
            if escrow_logs:
                latest_log = escrow_logs[0]
                logger.info(f"📋 最新圈存日誌資訊:")
                logger.info(f"   - 用戶ID: {latest_log.user_id}")
                logger.info(f"   - 操作類型: {latest_log.action}")
                logger.info(f"   - 操作者: {latest_log.performed_by}")
                logger.info(f"   - 管理員資訊: {latest_log.admin_info}")
        except Exception as e:
            logger.error(f"❌ 查詢圈存日誌失敗: {e}")
        
        # 測試 4: 檢查資料庫連接
        logger.info("📝 測試 4: 檢查資料庫集合...")
        try:
            point_logs_count = await db[Collections.POINT_LOGS].count_documents({})
            escrow_logs_count = await db[Collections.ESCROW_LOGS].count_documents({})
            logger.info(f"✅ 資料庫統計:")
            logger.info(f"   - 點數日誌總數: {point_logs_count}")
            logger.info(f"   - 圈存日誌總數: {escrow_logs_count}")
        except Exception as e:
            logger.error(f"❌ 檢查資料庫失敗: {e}")
        
        logger.info("🎉 審計記錄系統測試完成！")
        
    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_audit_system())