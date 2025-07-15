from __future__ import annotations
from app.services.base_service import BaseService
from app.core.database import Collections
from app.schemas.user import TransferRequest, TransferResponse
from datetime import datetime, timezone
from bson import ObjectId
import logging
import uuid

logger = logging.getLogger(__name__)

def get_transfer_service() -> TransferService:
    """TransferService 的依賴注入函數"""
    return TransferService()

class TransferService(BaseService):
    """轉帳服務 - 負責處理點數轉帳相關功能"""
    
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
        
        # 檢查接收方狀態
        if not to_user.get("enabled", True):
            return TransferResponse(
                success=False,
                message="接收方帳戶已被禁用，無法接收轉帳"
            )
        
        # 增加接收方點數，並處理債務償還
        repay_result = await self._add_points_with_debt_repay(
            user_id=to_user["_id"],
            amount=request.amount,
            operation_note=f"收到來自 {from_user.get('name', from_user.get('id', 'unknown'))} 的轉帳",
            session=session
        )
        
        if not repay_result['success']:
            return TransferResponse(
                success=False,
                message=f"轉帳處理失敗：{repay_result['message']}"
            )
        
        # 記錄轉帳發送方日誌
        await self._log_point_change(
            from_user_oid,
            "transfer_out",
            -total_deduct,
            f"轉帳給 {to_user.get('name', to_user.get('id', request.to_username))} (含手續費 {fee})",
            transaction_id,
            session=session
        )
        
        # 接收方的記錄已在 _add_points_with_debt_repay 中處理
        # 如果沒有債務，需要補充記錄
        if repay_result.get('debt_repaid', 0) == 0:
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
        
        # 構建轉帳成功訊息
        success_message = "轉帳成功"
        if repay_result.get('debt_repaid', 0) > 0:
            success_message += f"，接收方自動償還欠款 {repay_result['debt_repaid']} 點"
            if repay_result.get('remaining_debt', 0) > 0:
                success_message += f"，剩餘欠款 {repay_result['remaining_debt']} 點"
            else:
                success_message += "，欠款已完全償還"
        
        
        return TransferResponse(
            success=True,
            message=success_message,
            transaction_id=transaction_id,
            fee=fee
        )
    
    async def _safe_deduct_points(self, user_id: ObjectId, amount: int, 
                                operation_note: str, session=None) -> dict:
        """
        安全地扣除使用者點數，防止產生負數餘額（含欠款檢查）
        
        Args:
            user_id: 使用者ID
            amount: 要扣除的點數
            operation_note: 操作說明
            session: 資料庫session（用於交易）
            
        Returns:
            dict: {'success': bool, 'message': str, 'balance_before': int, 'balance_after': int}
        """
        try:
            # 首先檢查用戶狀態和欠款情況
            user = await self.db[Collections.USERS].find_one({"_id": user_id}, session=session)
            if not user:
                return {
                    'success': False,
                    'message': '使用者不存在',
                    'balance_before': 0,
                    'balance_after': 0
                }
            
            # 檢查帳戶狀態
            if not user.get("enabled", True):
                return {
                    'success': False,
                    'message': '帳戶未啟用',
                    'balance_before': user.get("points", 0),
                    'balance_after': user.get("points", 0)
                }
            
            if user.get("frozen", False):
                return {
                    'success': False,
                    'message': '帳戶已凍結，無法進行轉帳',
                    'balance_before': user.get("points", 0),
                    'balance_after': user.get("points", 0)
                }
            
            # 檢查欠款情況
            points = user.get("points", 0)
            owed_points = user.get("owed_points", 0)
            
            if owed_points > 0:
                return {
                    'success': False,
                    'message': f'帳戶有欠款 {owed_points} 點，請先償還後才能進行轉帳',
                    'balance_before': points,
                    'balance_after': points,
                    'owed_points': owed_points
                }
            
            # 計算實際可用餘額
            available_balance = points - owed_points
            
            if available_balance < amount:
                return {
                    'success': False,
                    'message': f'餘額不足（含欠款檢查）。需要: {amount} 點，可用: {available_balance} 點',
                    'balance_before': points,
                    'balance_after': points,
                    'available_balance': available_balance
                }
            
            # 使用 MongoDB 的條件更新確保原子性（包含凍結和欠款檢查）
            update_result = await self.db[Collections.USERS].update_one(
                {
                    "_id": user_id,
                    "points": {"$gte": amount},  # 確保扣除後不會變負數
                    "frozen": {"$ne": True},     # 確保不是凍結狀態
                    "$or": [
                        {"owed_points": {"$exists": False}},  # 沒有欠款字段
                        {"owed_points": {"$lte": 0}}          # 或者欠款為0
                    ]
                },
                {"$inc": {"points": -amount}},
                session=session
            )
            
            if update_result.modified_count == 0:
                # 扣除失敗，重新檢查原因
                user_recheck = await self.db[Collections.USERS].find_one({"_id": user_id}, session=session)
                current_balance = user_recheck.get("points", 0) if user_recheck else 0
                current_owed = user_recheck.get("owed_points", 0) if user_recheck else 0
                
                return {
                    'success': False,
                    'message': f'轉帳失敗。可能原因：餘額不足、帳戶凍結或有欠款。目前餘額: {current_balance} 點，欠款: {current_owed} 點',
                    'balance_before': current_balance,
                    'balance_after': current_balance
                }
            
            # 扣除成功，取得更新後的餘額
            user_after = await self.db[Collections.USERS].find_one({"_id": user_id}, session=session)
            balance_after = user_after.get("points", 0) if user_after else 0
            balance_before = balance_after + amount
            
            # 點數扣除記錄由外部調用者處理，避免重複記錄
            
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
        """記錄點數變動（擴展基類方法以支援 transaction_id）"""
        try:
            # 確保 user_id 是 ObjectId
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
                
            user = await self.db[Collections.USERS].find_one({"_id": user_id}, session=session)
            current_balance = user.get("points", 0) if user else 0
            
            log_entry = {
                "user_id": user_id,
                "change_type": change_type,  # 使用 change_type 而不是 type
                "amount": amount,
                "description": note,  # 使用 description 而不是 note
                "balance_after": current_balance,
                "timestamp": datetime.now(timezone.utc),  # 使用 timestamp 而不是 created_at
                "log_id": str(ObjectId()),
                "transaction_id": transaction_id
            }
            
            await self.db[Collections.POINT_LOGS].insert_one(log_entry, session=session)
        except Exception as e:
            logger.error(f"Failed to log point change: {e}")
    
    async def _add_points_with_debt_repay(self, user_id: ObjectId, amount: int, 
                                         operation_note: str, session=None) -> dict:
        """
        增加用戶點數，如果有欠款則優先償還
        
        Args:
            user_id: 用戶ID
            amount: 要增加的點數
            operation_note: 操作說明
            session: 資料庫session（用於交易）
            
        Returns:
            dict: 操作結果
        """
        try:
            # 獲取用戶目前狀態
            user = await self.db[Collections.USERS].find_one({"_id": user_id}, session=session)
            if not user:
                return {
                    'success': False,
                    'message': '用戶不存在'
                }
            
            current_points = user.get("points", 0)
            current_owed = user.get("owed_points", 0)
            
            if current_owed > 0:
                # 有欠款，優先償還
                # 總可用於償還的金額 = 現有點數 + 新轉入的點數
                total_available = current_points + amount
                
                # 計算實際償還金額（不能超過欠款總額）
                actual_repay = min(total_available, current_owed)
                
                # 計算償還後剩餘的點數
                remaining_points = total_available - actual_repay
                
                # 更新用戶資料：設定新的點數，減少欠款
                update_doc = {
                    "$set": {"points": remaining_points},
                    "$inc": {"owed_points": -actual_repay}
                }
                
                # 如果完全償還，解除凍結
                if actual_repay == current_owed:
                    update_doc["$set"]["frozen"] = False
                
                await self.db[Collections.USERS].update_one(
                    {"_id": user_id},
                    update_doc,
                    session=session
                )
                
                # 記錄債務償還日誌（使用標準格式）
                if actual_repay > 0:
                    await self._log_point_change(
                        user_id=user_id,
                        change_type="debt_repayment",
                        amount=actual_repay,
                        note=f"債務償還 {actual_repay} 點（轉帳自動償還）",
                        transaction_id=None,
                        session=session
                    )
                
                # 如果有剩餘點數，記錄為轉帳收入
                if remaining_points > current_points:
                    net_increase = remaining_points - current_points
                    await self._log_point_change(
                        user_id=user_id,
                        change_type="transfer_in",
                        amount=net_increase,
                        note=f"轉帳收入 {net_increase} 點（償還債務後剩餘）",
                        transaction_id=None,
                        session=session
                    )
                
                logger.info(f"Transfer with debt repay: user {user_id}, transfer {amount}, repaid {actual_repay}, remaining debt {current_owed - actual_repay}")
                
                return {
                    'success': True,
                    'message': f'轉帳成功，自動償還欠款 {actual_repay} 點',
                    'debt_repaid': actual_repay,
                    'remaining_debt': current_owed - actual_repay,
                    'final_points': remaining_points
                }
            else:
                # 沒有欠款，直接增加點數
                await self.db[Collections.USERS].update_one(
                    {"_id": user_id},
                    {"$inc": {"points": amount}},
                    session=session
                )
                
                # 點數增加記錄由外部調用者處理，避免重複記錄
                
                return {
                    'success': True,
                    'message': '轉帳成功',
                    'debt_repaid': 0,
                    'remaining_debt': 0,
                    'final_points': current_points + amount
                }
                
        except Exception as e:
            logger.error(f"Error adding points with debt repay for user {user_id}: {e}")
            return {
                'success': False,
                'message': f'處理轉帳失敗: {str(e)}'
            }

    async def _check_and_alert_negative_balance(self, user_id: ObjectId, operation_context: str = "") -> bool:
        """
        檢查指定使用者是否有負點數，如有則傳送警報（擴展基類方法）
        
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
                logger.error(f"🚨 NEGATIVE BALANCE ALERT: User {username} ({user_id}) has {current_balance} points after {operation_context}")
                
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