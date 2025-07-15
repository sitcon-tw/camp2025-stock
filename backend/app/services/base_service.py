from __future__ import annotations
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database, Collections
from app.services.cache_service import get_cache_service
from app.services.cache_invalidation import get_cache_invalidator
from datetime import datetime, timezone
from bson import ObjectId
import logging
import time
from collections import defaultdict
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class BaseService:
    """基礎服務類別，提供所有服務的共用功能"""
    
    def __init__(self, db: AsyncIOMotorDatabase = None):
        if db is None:
            self.db = get_database()
        else:
            self.db = db
        self.cache_service = get_cache_service()
        self.cache_invalidator = get_cache_invalidator()
        
        # 寫入衝突統計
        self.write_conflict_stats = defaultdict(int)
        self.last_conflict_log_time = time.time()
    
    def _log_write_conflict(self, operation: str, attempt: int, max_retries: int):
        """記錄寫入衝突統計"""
        self.write_conflict_stats[operation] += 1
        
        # 每 60 秒輸出一次統計報告
        current_time = time.time()
        if current_time - self.last_conflict_log_time > 60:
            total_conflicts = sum(self.write_conflict_stats.values())
            logger.warning(f"寫入衝突統計報告：總計 {total_conflicts} 次衝突")
            for op, count in self.write_conflict_stats.items():
                logger.warning(f"  {op}: {count} 次")
            self.last_conflict_log_time = current_time
            
        logger.info(f"{operation} WriteConflict 第 {attempt + 1}/{max_retries} 次嘗試失敗，將重試...")
    
    async def _get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """根據 ID 獲取用戶資料"""
        try:
            user_oid = ObjectId(user_id)
            return await self.db[Collections.USERS].find_one({"_id": user_oid})
        except Exception as e:
            logger.error(f"Failed to get user by ID {user_id}: {e}")
            return None
    
    async def _get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """根據 Telegram ID 獲取用戶資料"""
        try:
            return await self.db[Collections.USERS].find_one({"telegram_id": telegram_id})
        except Exception as e:
            logger.error(f"Failed to get user by telegram ID {telegram_id}: {e}")
            return None
    
    async def _log_point_change(self, user_id: ObjectId, change_type: str, amount: int, 
                               description: str = "", related_user_id: ObjectId = None,
                               session=None):
        """記錄點數變化日誌"""
        try:
            log_entry = {
                "user_id": user_id,
                "change_type": change_type,
                "amount": amount,
                "description": description,
                "timestamp": datetime.now(timezone.utc),
                "log_id": str(ObjectId())
            }
            
            if related_user_id:
                log_entry["related_user_id"] = related_user_id
            
            await self.db[Collections.POINT_LOGS].insert_one(log_entry, session=session)
            logger.info(f"Point change logged: user {user_id}, type {change_type}, amount {amount}")
            
        except Exception as e:
            logger.error(f"Failed to log point change: {e}")
    
    async def _validate_transaction_integrity(self, user_ids: list, operation_name: str):
        """驗證交易完整性"""
        try:
            for user_id in user_ids:
                user = await self.db[Collections.USERS].find_one({"_id": user_id})
                if not user:
                    logger.error(f"Transaction integrity check failed: user {user_id} not found during {operation_name}")
                    continue
                    
                points = user.get("points", 0)
                if points < 0:
                    logger.error(f"Transaction integrity violation: user {user_id} has negative points {points} after {operation_name}")
                    await self._check_and_alert_negative_balance(user_id, operation_name)
                    
        except Exception as e:
            logger.error(f"Transaction integrity validation failed: {e}")
    
    async def _check_and_alert_negative_balance(self, user_id: ObjectId, operation_context: str = "") -> bool:
        """檢查並警告負數餘額"""
        try:
            user = await self.db[Collections.USERS].find_one({"_id": user_id})
            if not user:
                return False
                
            points = user.get("points", 0)
            if points < 0:
                username = user.get("username", "unknown")
                logger.error(f"🚨 NEGATIVE BALANCE ALERT: User {username} ({user_id}) has {points} points after {operation_context}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Failed to check negative balance: {e}")
            return False