from __future__ import annotations
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database, Collections
from app.schemas.user import TransferRequest, TransferResponse
from datetime import datetime, timezone
from bson import ObjectId
from typing import Optional
import logging
import uuid

logger = logging.getLogger(__name__)

def get_transfer_service() -> TransferService:
    """TransferService 的依賴注入函數"""
    return TransferService()

class TransferService:
    """轉帳服務 - 負責處理點數轉帳相關功能"""
    
    def __init__(self, db: AsyncIOMotorDatabase = None):
        if db is None:
            self.db = get_database()
        else:
            self.db = db
    
    async def transfer_points(self, from_user_id: str, request: TransferRequest) -> TransferResponse:
        """轉帳點數，帶增強重試機制"""
        max_retries = 8  # 增加重試次數
        retry_delay = 0.003  # 3ms 初始延遲
        
        for attempt in range(max_retries):
            try:
                result = await self._transfer_points_with_transaction(from_user_id, request)
                if attempt > 0:
                    logger.info(f"Transfer succeeded on attempt {attempt + 1}")
                return result
                
            except Exception as e:
                error_str = str(e)
                
                # 檢查是否為事務不支援的錯誤
                if "Transaction numbers are only allowed on a replica set member or mongos" in error_str:
                    logger.warning("MongoDB transactions not supported, falling back to non-transactional mode")
                    return await self._transfer_points_without_transaction(from_user_id, request)
                
                # 檢查是否為寫入衝突錯誤（可重試）
                elif "WriteConflict" in error_str or "TransientTransactionError" in error_str:
                    if attempt < max_retries - 1:
                        logger.info(f"Transfer WriteConflict detected on attempt {attempt + 1}/{max_retries}, retrying in {retry_delay:.3f}s...")
                        import asyncio
                        import random
                        # 添加隨機延遲以避免雷群效應
                        jitter = random.uniform(0.8, 1.2)
                        await asyncio.sleep(retry_delay * jitter)
                        retry_delay *= 1.6  # 略為加強的指數退避
                        continue
                    else:
                        logger.warning(f"Transfer WriteConflict persisted after {max_retries} attempts, falling back to non-transactional mode")
                        return await self._transfer_points_without_transaction(from_user_id, request)
                
                else:
                    logger.error(f"Transfer failed with non-retryable error: {e}")
                    return TransferResponse(
                        success=False,
                        message=f"轉帳失敗：{str(e)}"
                    )

    async def _transfer_points_with_transaction(self, from_user_id: str, request: TransferRequest) -> TransferResponse:
        """使用事務進行轉帳（適用於 replica set 或 sharded cluster）"""
        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                return await self._execute_transfer(from_user_id, request, session)

    async def _transfer_points_without_transaction(self, from_user_id: str, request: TransferRequest) -> TransferResponse:
        """不使用事務進行轉帳（適用於 standalone MongoDB）"""
        return await self._execute_transfer(from_user_id, request, None)

    async def _get_transfer_fee_config(self):
        """獲取轉點數手續費設定"""
        try:
            fee_config = await self.db[Collections.MARKET_CONFIG].find_one({
                "type": "transfer_fee"
            })
            
            if fee_config:
                return {
                    "fee_rate": fee_config.get("fee_rate", 10.0),  # 預設 10%
                    "min_fee": fee_config.get("min_fee", 1)       # 預設最少 1 點
                }
            else:
                # 如果沒有設定，使用預設值
                return {
                    "fee_rate": 10.0,  # 10%
                    "min_fee": 1       # 最少 1 點
                }
        except Exception as e:
            logger.error(f"Error getting transfer fee config: {e}")
            return {
                "fee_rate": 10.0,  # 預設 10%
                "min_fee": 1       # 預設最少 1 點
            }

    async def _execute_transfer(self, from_user_id: str, request: TransferRequest, session=None) -> TransferResponse:
        """執行轉帳邏輯"""
        # 取得傳送方使用者
        from_user_oid = ObjectId(from_user_id)
        from_user = await self.db[Collections.USERS].find_one({"_id": from_user_oid}, session=session)
        if not from_user:
            return TransferResponse(
                success=False,
                message="傳送方使用者不存在"
            )
        
        # 取得接收方使用者 - 改為支援name或id查詢
        to_user = await self.db[Collections.USERS].find_one({
            "$or": [
                {"name": request.to_username},
                {"id": request.to_username},
                {"telegram_id": request.to_username}
            ]
        }, session=session)
        if not to_user:
            return TransferResponse(
                success=False,
                message="接收方使用者不存在"
            )
        
        # 檢查是否為同一人
        if str(from_user["_id"]) == str(to_user["_id"]):
            return TransferResponse(
                success=False,
                message="無法轉帳給自己"
            )
        
        # 計算手續費 (動態設定)
        fee_config = await self._get_transfer_fee_config()
        fee = max(fee_config["min_fee"], int(request.amount * fee_config["fee_rate"] / 100.0))
        total_deduct = request.amount + fee
        
        # 檢查餘額
        if from_user.get("points", 0) < total_deduct:
            return TransferResponse(
                success=False,
                message=f"點數不足（需要 {total_deduct} 點，含手續費 {fee}）"
            )
        
        # 執行轉帳
        transaction_id = str(uuid.uuid4())
        
        # 安全扣除傳送方點數
        deduction_result = await self._safe_deduct_points(
            user_id=from_user_oid,
            amount=total_deduct,
            operation_note=f"轉帳給 {request.to_username}：{request.amount} 點 (含手續費 {fee} 點)",
            session=session
        )
        
        if not deduction_result['success']:
            return TransferResponse(
                success=False,
                message=deduction_result['message']
            )
        
        # 增加接收方點數
        await self.db[Collections.USERS].update_one(
            {"_id": to_user["_id"]},
            {"$inc": {"points": request.amount}},
            session=session
        )
        
        # 記錄轉帳日誌
        await self._log_point_change(
            from_user_oid,
            "transfer_out",
            -total_deduct,
            f"轉帳給 {to_user.get('name', to_user.get('id', request.to_username))} (含手續費 {fee})",
            transaction_id,
            session=session
        )
        
        await self._log_point_change(
            to_user["_id"],
            "transfer_in",
            request.amount,
            f"收到來自 {from_user.get('name', from_user.get('id', 'unknown'))} 的轉帳",
            transaction_id,
            session=session
        )
        
        # 如果有事務則提交
        if session:
            await session.commit_transaction()
        
        # 轉帳完成後檢查點數完整性
        await self._validate_transaction_integrity(
            user_ids=[from_user_oid, to_user["_id"]],
            operation_name=f"轉帳 - {request.amount} 點 (含手續費 {fee} 點)"
        )
        
        return TransferResponse(
            success=True,
            message="轉帳成功",
            transaction_id=transaction_id,
            fee=fee
        )
    
    async def _safe_deduct_points(self, user_id: ObjectId, amount: int, 
                                operation_note: str, session=None) -> dict:
        """
        安全地扣除使用者點數，防止產生負數餘額
        
        Args:
            user_id: 使用者ID
            amount: 要扣除的點數
            operation_note: 操作說明
            session: 資料庫session（用於交易）
            
        Returns:
            dict: {'success': bool, 'message': str, 'balance_before': int, 'balance_after': int}
        """
        try:
            # 使用 MongoDB 的條件更新確保原子性
            update_result = await self.db[Collections.USERS].update_one(
                {
                    "_id": user_id,
                    "points": {"$gte": amount}  # 確保扣除後不會變負數
                },
                {"$inc": {"points": -amount}},
                session=session
            )
            
            if update_result.modified_count == 0:
                # 扣除失敗，檢查使用者目前餘額
                user = await self.db[Collections.USERS].find_one({"_id": user_id}, session=session)
                current_balance = user.get("points", 0) if user else 0
                
                return {
                    'success': False,
                    'message': f'點數不足，需要 {amount} 點，目前餘額: {current_balance} 點',
                    'balance_before': current_balance,
                    'balance_after': current_balance
                }
            
            # 扣除成功，取得更新後的餘額
            user = await self.db[Collections.USERS].find_one({"_id": user_id}, session=session)
            balance_after = user.get("points", 0) if user else 0
            balance_before = balance_after + amount
            
            # 記錄點數變化
            await self._log_point_change(
                user_id=user_id,
                change_type="deduction",
                amount=-amount,
                note=operation_note,
                session=session
            )
            
            logger.info(f"Safe point deduction successful: user {user_id}, amount {amount}, balance: {balance_before} -> {balance_after}")
            
            return {
                'success': True,
                'message': f'成功扣除 {amount} 點',
                'balance_before': balance_before,
                'balance_after': balance_after
            }
            
        except Exception as e:
            logger.error(f"Failed to safely deduct points: user {user_id}, amount {amount}, error: {e}")
            return {
                'success': False,
                'message': f'點數扣除失敗: {str(e)}',
                'balance_before': 0,
                'balance_after': 0
            }
    
    async def _log_point_change(self, user_id, change_type: str, amount: int, 
                              note: str, transaction_id: str = None, session=None):
        """記錄點數變動"""
        try:
            # 確保 user_id 是 ObjectId
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
                
            user = await self.db[Collections.USERS].find_one({"_id": user_id}, session=session)
            current_balance = user.get("points", 0) if user else 0
            
            log_entry = {
                "user_id": user_id,
                "type": change_type,
                "amount": amount,
                "note": note,
                "balance_after": current_balance,
                "created_at": datetime.now(timezone.utc),
                "transaction_id": transaction_id
            }
            
            await self.db[Collections.POINT_LOGS].insert_one(log_entry, session=session)
        except Exception as e:
            logger.error(f"Failed to log point change: {e}")
    
    async def _validate_transaction_integrity(self, user_ids: list, operation_name: str):
        """
        交易完成後驗證所有涉及使用者的點數完整性
        
        Args:
            user_ids: 涉及的使用者ID列表
            operation_name: 操作名稱
        """
        try:
            negative_detected = False
            for user_id in user_ids:
                if isinstance(user_id, str):
                    user_id = ObjectId(user_id)
                
                is_negative = await self._check_and_alert_negative_balance(
                    user_id=user_id,
                    operation_context=operation_name
                )
                if is_negative:
                    negative_detected = True
            
            if negative_detected:
                logger.warning(f"Transaction integrity check failed for operation: {operation_name}")
        except Exception as e:
            logger.error(f"Failed to validate transaction integrity: {e}")
    
    async def _check_and_alert_negative_balance(self, user_id: ObjectId, operation_context: str = "") -> bool:
        """
        檢查指定使用者是否有負點數，如有則傳送警報
        
        Args:
            user_id: 使用者ID
            operation_context: 操作情境描述
            
        Returns:
            bool: True if balance is negative, False otherwise
        """
        try:
            user = await self.db[Collections.USERS].find_one({"_id": user_id})
            if not user:
                return False
            
            current_balance = user.get("points", 0)
            if current_balance < 0:
                username = user.get("username", user.get("name", "未知"))
                team = user.get("team", "無")
                
                # 記錄警報日誌
                logger.error(f"NEGATIVE BALANCE DETECTED: User {username} (ID: {user_id}) has {current_balance} points after {operation_context}")
                
                # 傳送即時警報到 Telegram Bot
                try:
                    from app.services.admin_service import AdminService
                    admin_service = AdminService(self.db)
                    await admin_service._send_system_announcement(
                        title="🚨 負點數警報",
                        message=f"檢測到負點數！\n👤 使用者：{username}\n🏷️ 隊伍：{team}\n💰 目前點數：{current_balance}\n📍 操作情境：{operation_context}\n⏰ 時間：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC"
                    )
                except Exception as e:
                    logger.error(f"Failed to send negative balance alert: {e}")
                
                return True
            
            return False
        except Exception as e:
            logger.error(f"Failed to check negative balance: {e}")
            return False