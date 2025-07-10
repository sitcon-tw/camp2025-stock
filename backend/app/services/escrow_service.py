from __future__ import annotations
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database, Collections
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import logging
from bson import ObjectId
from app.core.exceptions import InsufficientPointsException, EscrowException

logger = logging.getLogger(__name__)

class EscrowService:
    """
    圈存服務 - 類似銀行的資金圈存機制
    
    功能：
    1. 預先凍結使用者資金用於特定交易
    2. 確保交易執行時有足夠資金
    3. 避免超額消費和負餘額
    4. 提供交易回滾機制
    """
    
    def __init__(self, db: AsyncIOMotorDatabase = None):
        if db is None:
            self.db = get_database()
        else:
            self.db = db
    
    async def create_escrow(self, user_id: str, amount: int, escrow_type: str, 
                           reference_id: str = None, metadata: Dict[str, Any] = None) -> str:
        """
        創建圈存記錄
        
        Args:
            user_id: 使用者ID
            amount: 圈存金額
            escrow_type: 圈存類型 ('stock_order', 'pvp_battle', 'transfer')
            reference_id: 相關交易ID (如訂單ID、PVP ID等)
            metadata: 附加資料
            
        Returns:
            escrow_id: 圈存記錄ID
            
        Raises:
            InsufficientPointsException: 餘額不足
            EscrowException: 圈存失敗
        """
        try:
            # 使用事務確保原子性
            async with await self.db.client.start_session() as session:
                async with session.start_transaction():
                    # 檢查使用者餘額並扣除可用餘額
                    user_update_result = await self.db[Collections.USERS].update_one(
                        {
                            "_id": user_id,
                            "points": {"$gte": amount}  # 確保有足夠餘額
                        },
                        {
                            "$inc": {
                                "points": -amount,           # 扣除可用餘額
                                "escrow_amount": amount      # 增加圈存金額
                            }
                        },
                        session=session
                    )
                    
                    if user_update_result.matched_count == 0:
                        raise InsufficientPointsException(f"餘額不足，無法圈存 {amount} 點")
                    
                    # 創建圈存記錄
                    escrow_doc = {
                        "user_id": user_id,
                        "amount": amount,
                        "type": escrow_type,
                        "reference_id": reference_id,
                        "metadata": metadata or {},
                        "status": "active",
                        "created_at": datetime.now(timezone.utc),
                        "expires_at": None,  # 可以設置過期時間
                        "completed_at": None,
                        "cancelled_at": None
                    }
                    
                    escrow_result = await self.db[Collections.ESCROWS].insert_one(
                        escrow_doc, session=session
                    )
                    
                    escrow_id = str(escrow_result.inserted_id)
                    
                    # 記錄圈存日誌
                    await self._log_escrow_change(
                        user_id, "create", amount, escrow_id, 
                        f"圈存創建 - {escrow_type}", session
                    )
                    
                    logger.info(f"Escrow created: {escrow_id} for user {user_id}, amount: {amount}")
                    return escrow_id
                    
        except InsufficientPointsException:
            raise
        except Exception as e:
            logger.error(f"Failed to create escrow: {e}")
            raise EscrowException(f"圈存創建失敗: {str(e)}")
    
    async def complete_escrow(self, escrow_id: str, actual_amount: int = None, session=None) -> bool:
        """
        完成圈存 - 實際執行交易
        
        Args:
            escrow_id: 圈存記錄ID
            actual_amount: 實際消費金額 (如果不同於圈存金額)
            session: 可選的數據庫會話（用於事務中）
            
        Returns:
            success: 是否成功完成
        """
        try:
            if session is not None:
                # 使用提供的會話（已在事務中）
                return await self._complete_escrow_logic(escrow_id, actual_amount, session)
            else:
                # 創建新的會話和事務
                async with await self.db.client.start_session() as new_session:
                    async with new_session.start_transaction():
                        return await self._complete_escrow_logic(escrow_id, actual_amount, new_session)
                        
        except Exception as e:
            logger.error(f"Failed to complete escrow {escrow_id}: {e}")
            raise EscrowException(f"圈存完成失敗: {str(e)}")
    
    async def _complete_escrow_logic(self, escrow_id: str, actual_amount: int = None, session=None) -> bool:
        """圈存完成的核心邏輯"""
        # 獲取圈存記錄
        escrow_doc = await self.db[Collections.ESCROWS].find_one(
            {"_id": ObjectId(escrow_id), "status": "active"},
            session=session
        )
        
        if not escrow_doc:
            raise EscrowException("圈存記錄不存在或已處理")
        
        user_id = escrow_doc["user_id"]
        escrowed_amount = escrow_doc["amount"]
        final_amount = actual_amount if actual_amount is not None else escrowed_amount
        
        # 計算退還金額
        refund_amount = escrowed_amount - final_amount
        
        # 更新使用者餘額
        user_update = {
            "$inc": {
                "escrow_amount": -escrowed_amount,  # 減少圈存金額
            }
        }
        
        if refund_amount > 0:
            # 如果有退款，返還到可用餘額
            user_update["$inc"]["points"] = refund_amount
        
        await self.db[Collections.USERS].update_one(
            {"_id": user_id},
            user_update,
            session=session
        )
        
        # 標記圈存為已完成
        await self.db[Collections.ESCROWS].update_one(
            {"_id": ObjectId(escrow_id)},
            {
                "$set": {
                    "status": "completed",
                    "actual_amount": final_amount,
                    "refund_amount": refund_amount,
                    "completed_at": datetime.now(timezone.utc)
                }
            },
            session=session
        )
        
        # 記錄完成日誌
        await self._log_escrow_change(
            user_id, "complete", final_amount, escrow_id,
            f"圈存完成 - 消費: {final_amount}, 退還: {refund_amount}", session
        )
        
        logger.info(f"Escrow completed: {escrow_id}, consumed: {final_amount}, refunded: {refund_amount}")
        return True
    async def cancel_escrow(self, escrow_id: str, reason: str = "cancelled") -> bool:
        """
        取消圈存 - 退還全部資金
        
        Args:
            escrow_id: 圈存記錄ID
            reason: 取消原因
            
        Returns:
            success: 是否成功取消
        """
        try:
            async with await self.db.client.start_session() as session:
                async with session.start_transaction():
                    # 獲取圈存記錄
                    escrow_doc = await self.db[Collections.ESCROWS].find_one(
                        {"_id": ObjectId(escrow_id), "status": "active"},
                        session=session
                    )
                    
                    if not escrow_doc:
                        raise EscrowException("圈存記錄不存在或已處理")
                    
                    user_id = escrow_doc["user_id"]
                    amount = escrow_doc["amount"]
                    
                    # 退還資金到使用者餘額
                    await self.db[Collections.USERS].update_one(
                        {"_id": user_id},
                        {
                            "$inc": {
                                "points": amount,           # 退還到可用餘額
                                "escrow_amount": -amount    # 減少圈存金額
                            }
                        },
                        session=session
                    )
                    
                    # 標記圈存為已取消
                    await self.db[Collections.ESCROWS].update_one(
                        {"_id": ObjectId(escrow_id)},
                        {
                            "$set": {
                                "status": "cancelled",
                                "cancellation_reason": reason,
                                "cancelled_at": datetime.now(timezone.utc)
                            }
                        },
                        session=session
                    )
                    
                    # 記錄取消日誌
                    await self._log_escrow_change(
                        user_id, "cancel", amount, escrow_id,
                        f"圈存取消 - {reason}", session
                    )
                    
                    logger.info(f"Escrow cancelled: {escrow_id}, refunded: {amount}")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to cancel escrow {escrow_id}: {e}")
            raise EscrowException(f"圈存取消失敗: {str(e)}")
    
    async def get_user_escrows(self, user_id: str, status: str = None) -> List[Dict]:
        """
        獲取使用者的圈存記錄
        
        Args:
            user_id: 使用者ID (字符串格式)
            status: 狀態篩選 ('active', 'completed', 'cancelled')
            
        Returns:
            escrows: 圈存記錄列表
        """
        try:
            from bson import ObjectId
            
            # 嘗試轉換為 ObjectId（因為資料庫中儲存的可能是 ObjectId）
            try:
                user_oid = ObjectId(user_id)
                query_user_id = user_oid
            except:
                # 如果轉換失敗，使用原始字符串
                query_user_id = user_id
                
            query = {"user_id": query_user_id}
            if status:
                query["status"] = status
            
            escrows_cursor = self.db[Collections.ESCROWS].find(query).sort("created_at", -1)
            escrows = await escrows_cursor.to_list(length=None)
            
            # 轉換ObjectId為字串
            for escrow in escrows:
                escrow["_id"] = str(escrow["_id"])
            
            return escrows
            
        except Exception as e:
            logger.error(f"Failed to get user escrows: {e}")
            raise EscrowException(f"獲取圈存記錄失敗: {str(e)}")
    
    async def get_escrow_by_id(self, escrow_id: str) -> Optional[Dict]:
        """
        根據ID獲取圈存記錄
        
        Args:
            escrow_id: 圈存記錄ID
            
        Returns:
            escrow: 圈存記錄，如果不存在返回None
        """
        try:
            escrow_doc = await self.db[Collections.ESCROWS].find_one(
                {"_id": ObjectId(escrow_id)}
            )
            
            if escrow_doc:
                escrow_doc["_id"] = str(escrow_doc["_id"])
            
            return escrow_doc
            
        except Exception as e:
            logger.error(f"Failed to get escrow by ID {escrow_id}: {e}")
            return None
    
    async def get_user_total_escrow(self, user_id: str) -> int:
        """
        獲取使用者總圈存金額
        
        Args:
            user_id: 使用者ID (字符串格式)
            
        Returns:
            total_escrow: 總圈存金額
        """
        try:
            from bson import ObjectId
            
            # 嘗試轉換為 ObjectId（因為資料庫中儲存的可能是 ObjectId）
            try:
                user_oid = ObjectId(user_id)
                query_user_id = user_oid
            except:
                # 如果轉換失敗，使用原始字符串
                query_user_id = user_id
            
            # 使用聚合計算活躍圈存的總金額
            pipeline = [
                {"$match": {"user_id": query_user_id, "status": "active"}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]
            
            result = await self.db[Collections.ESCROWS].aggregate(pipeline).to_list(length=1)
            
            if result:
                return result[0]["total"]
            else:
                return 0
                
        except Exception as e:
            logger.error(f"Failed to get user total escrow: {e}")
            return 0
    
    async def cleanup_expired_escrows(self, max_age_hours: int = 24) -> int:
        """
        清理過期的圈存記錄
        
        Args:
            max_age_hours: 過期時間（小時）
            
        Returns:
            cleanup_count: 清理的記錄數量
        """
        try:
            from datetime import timedelta
            
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
            
            # 查找過期的活躍圈存
            expired_escrows = await self.db[Collections.ESCROWS].find({
                "status": "active",
                "created_at": {"$lt": cutoff_time}
            }).to_list(length=None)
            
            cleanup_count = 0
            
            for escrow in expired_escrows:
                try:
                    await self.cancel_escrow(
                        str(escrow["_id"]), 
                        reason="expired_cleanup"
                    )
                    cleanup_count += 1
                except Exception as e:
                    logger.error(f"Failed to cleanup expired escrow {escrow['_id']}: {e}")
            
            logger.info(f"Cleaned up {cleanup_count} expired escrows")
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired escrows: {e}")
            return 0
    
    async def _log_escrow_change(self, user_id: str, action: str, amount: int, 
                                escrow_id: str, note: str, session=None,
                                performed_by: str = None, admin_info: dict = None):
        """
        記錄圈存變更日誌
        
        Args:
            user_id: 使用者ID
            action: 動作類型
            amount: 金額
            escrow_id: 圈存ID
            note: 備註
            session: MongoDB session
            performed_by: 操作者用戶ID
            admin_info: 管理員詳細資訊
        """
        try:
            log_entry = {
                "user_id": user_id,
                "type": f"escrow_{action}",
                "action": action,
                "amount": amount,
                "escrow_id": escrow_id,
                "note": note,
                "created_at": datetime.now(timezone.utc),
                "performed_by": performed_by,  # 操作者用戶ID
                "admin_info": admin_info or {}  # 管理員詳細資訊
            }
            
            await self.db[Collections.ESCROW_LOGS].insert_one(log_entry, session=session)
            
        except Exception as e:
            logger.error(f"Failed to log escrow change: {e}")

# 依賴注入函數
def get_escrow_service() -> EscrowService:
    """EscrowService 的依賴注入函數"""
    return EscrowService()