from __future__ import annotations
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database, Collections
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from typing import Optional
import logging
import random

logger = logging.getLogger(__name__)

def get_game_service() -> GameService:
    """GameService 的依賴注入函數"""
    return GameService()

class GameService:
    """遊戲服務 - 負責處理 PvP 猜拳遊戲相關功能"""
    
    def __init__(self, db: AsyncIOMotorDatabase = None):
        if db is None:
            self.db = get_database()
        else:
            self.db = db
            
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
                    'message': f'點數不足，目前餘額：{current_balance}，需要：{amount}',
                    'balance_before': current_balance,
                    'balance_after': current_balance
                }
            
            # 扣除成功，記錄變動
            user_after = await self.db[Collections.USERS].find_one({"_id": user_id}, session=session)
            balance_after = user_after.get("points", 0) if user_after else 0
            balance_before = balance_after + amount
            
            # 記錄點數變動
            try:
                log_entry = {
                    "user_id": user_id,
                    "type": "game_deduction",
                    "amount": -amount,  # 負數表示扣除
                    "note": operation_note,
                    "balance_after": balance_after,
                    "created_at": datetime.now(timezone.utc)
                }
                await self.db[Collections.POINT_LOGS].insert_one(log_entry, session=session)
                logger.info(f"Point deduction logged: user_id={user_id}, amount=-{amount}, balance_after={balance_after}")
            except Exception as e:
                logger.error(f"Failed to log point deduction: {e}")
                # 不影響主要業務邏輯
            
            return {
                'success': True,
                'message': '點數扣除成功',
                'balance_before': balance_before,
                'balance_after': balance_after
            }
            
        except Exception as e:
            logger.error(f"Safe deduct points failed: {e}")
            return {
                'success': False,
                'message': f'點數扣除失敗：{str(e)}',
                'balance_before': 0,
                'balance_after': 0
            }
    
    async def create_pvp_challenge(self, from_user: str, amount: int, chat_id: str):
        """建立 PVP 挑戰"""
        from app.schemas.bot import PVPResponse
        
        try:
            # 檢查發起者是否存在且有足夠點數
            user = await self.db[Collections.USERS].find_one({"telegram_id": from_user})
            if not user:
                return PVPResponse(
                    success=False,
                    message="使用者不存在，請先註冊"
                )
            
            # 使用債務驗證服務檢查發起者狀態和資金
            from app.core.user_validation import UserValidationService
            validation_service = UserValidationService(self.db)
            
            validation_result = await validation_service.validate_user_can_spend(
                user_id=user["_id"],
                amount=amount,
                operation_type="發起PvP挑戰"
            )
            
            if not validation_result['can_spend']:
                error_code = validation_result.get('error_code', 'UNKNOWN')
                
                if error_code == 'ACCOUNT_DISABLED':
                    message = "帳戶未啟用，無法發起 PvP 挑戰"
                elif error_code == 'ACCOUNT_FROZEN':
                    message = "帳戶已凍結，無法發起 PvP 挑戰"
                elif error_code == 'HAS_DEBT':
                    owed_points = validation_result.get('user_data', {}).get('owed_points', 0)
                    message = f"帳戶有欠款 {owed_points} 點，請先償還後才能發起 PvP 挑戰"
                elif error_code == 'INSUFFICIENT_BALANCE':
                    available_balance = validation_result.get('available_balance', 0)
                    current_points = validation_result.get('user_data', {}).get('points', 0)
                    owed_points = validation_result.get('user_data', {}).get('owed_points', 0)
                    if owed_points > 0:
                        message = f"可用點數不足！需要：{amount} 點，目前點數：{current_points} 點，欠款：{owed_points} 點，實際可用：{available_balance} 點"
                    else:
                        message = f"點數不足！需要：{amount} 點，目前點數：{available_balance} 點"
                else:
                    message = validation_result['message']
                
                return PVPResponse(
                    success=False,
                    message=message
                )
            
            # 檢查是否已有進行中的挑戰
            existing_challenge = await self.db[Collections.PVP_CHALLENGES].find_one({
                "challenger": from_user,
                "status": {"$in": ["pending", "waiting_accepter"]}
            })
            
            if existing_challenge:
                # 檢查挑戰是否過期，如果過期則自動清理
                expires_at = existing_challenge["expires_at"]
                if not expires_at.tzinfo:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) > expires_at:
                    await self.db[Collections.PVP_CHALLENGES].update_one(
                        {"_id": existing_challenge["_id"]},
                        {"$set": {"status": "expired"}}
                    )
                else:
                    # 提供更詳細的訊息
                    challenge_status = existing_challenge.get("status", "pending")
                    if challenge_status == "waiting_accepter":
                        return PVPResponse(
                            success=False,
                            message="你已經有一個等待接受的挑戰！請等待其他人接受或過期後再建立新挑戰。"
                        )
                    else:
                        return PVPResponse(
                            success=False,
                            message="你已經有一個進行中的挑戰！請完成後再建立新挑戰。"
                        )
            
            # 建立挑戰記錄
            challenge_oid = ObjectId()
            challenge_doc = {
                "_id": challenge_oid,
                "challenger": from_user,
                "challenger_name": user.get("name", "未知使用者"),
                "amount": amount,
                "chat_id": chat_id,
                "status": "waiting_accepter",  # 直接設為等待接受
                "created_at": datetime.now(timezone.utc),
                "expires_at": datetime.now(timezone.utc) + timedelta(hours=3)  # 3小時過期
            }
            
            await self.db[Collections.PVP_CHALLENGES].insert_one(challenge_doc)
            
            return PVPResponse(
                success=True,
                message=f"🎯 {user.get('name', '未知使用者')} 發起了 {amount} 點的 PVP 挑戰！\n點選按鈕接受挑戰，50% 機率決定勝負！",
                challenge_id=str(challenge_oid),
                amount=amount
            )
            
        except Exception as e:
            logger.error(f"Error creating PVP challenge: {e}")
            return PVPResponse(
                success=False,
                message="建立挑戰失敗，請稍後再試"
            )
    
    async def set_pvp_creator_choice(self, from_user: str, challenge_id: str, choice: str):
        """設定 PVP 發起人的選擇"""
        from app.schemas.bot import PVPResponse
        
        try:
            # 將 challenge_id 轉換為 ObjectId
            try:
                challenge_oid = ObjectId(challenge_id)
            except Exception:
                return PVPResponse(
                    success=False,
                    message="無效的挑戰 ID"
                )
            
            # 查找挑戰
            challenge = await self.db[Collections.PVP_CHALLENGES].find_one({
                "_id": challenge_oid,
                "status": "pending"
            })
            
            if not challenge:
                return PVPResponse(
                    success=False,
                    message="挑戰不存在或已結束"
                )
            
            # 檢查是否為發起者本人
            if challenge["challenger"] != from_user:
                return PVPResponse(
                    success=False,
                    message="只有發起者可以設定選擇！"
                )
            
            # 檢查是否已設定過選擇
            if challenge.get("challenger_choice"):
                return PVPResponse(
                    success=False,
                    message="你已經設定過選擇了！"
                )
            
            # 更新挑戰，設定發起人選擇
            await self.db[Collections.PVP_CHALLENGES].update_one(
                {"_id": challenge_oid},
                {
                    "$set": {
                        "challenger_choice": choice,
                        "status": "waiting_accepter"
                    }
                }
            )
            
            # 返回成功訊息，包含挑戰資訊供前端顯示
            challenger_name = challenge["challenger_name"]
            amount = challenge["amount"]
            
            return PVPResponse(
                success=True,
                message=f"🎯 {challenger_name} 發起了 {amount} 點的 PVP 挑戰！\n\n發起者已經選擇了他出的拳，有誰想來挑戰嗎？選擇你出的拳吧！\n⏰ 如果 3 小時沒有人接受，系統會重新提醒"
            )
            
        except Exception as e:
            logger.error(f"Error setting PVP creator choice: {e}")
            return PVPResponse(
                success=False,
                message="設定選擇失敗，請稍後再試"
            )

    async def accept_pvp_challenge(self, from_user: str, challenge_id: str, choice: str):
        """接受 PVP 挑戰並進行猜拳遊戲"""
        from app.schemas.bot import PVPResponse
        
        try:
            # 將 challenge_id 轉換為 ObjectId
            try:
                challenge_oid = ObjectId(challenge_id)
            except Exception:
                return PVPResponse(
                    success=False,
                    message="無效的挑戰 ID"
                )
            
            # 查找挑戰
            challenge = await self.db[Collections.PVP_CHALLENGES].find_one({
                "_id": challenge_oid,
                "status": {"$in": ["pending", "waiting_accepter"]}
            })
            
            if not challenge:
                return PVPResponse(
                    success=False,
                    message="挑戰不存在或已結束"
                )
            
            # 檢查發起人是否已選擇
            if not challenge.get("challenger_choice"):
                return PVPResponse(
                    success=False,
                    message="發起人尚未選擇猜拳，請稍後再試"
                )
            
            # 檢查是否過期
            expires_at = challenge["expires_at"]
            if not expires_at.tzinfo:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires_at:
                await self.db[Collections.PVP_CHALLENGES].update_one(
                    {"_id": challenge_oid},
                    {"$set": {"status": "expired"}}
                )
                return PVPResponse(
                    success=False,
                    message="挑戰已過期"
                )
            
            # 檢查是否為發起者本人
            if challenge["challenger"] == from_user:
                return PVPResponse(
                    success=False,
                    message="不能接受自己的挑戰！"
                )
            
            # 檢查接受者是否存在且有足夠點數
            accepter = await self.db[Collections.USERS].find_one({"telegram_id": from_user})
            if not accepter:
                return PVPResponse(
                    success=False,
                    message="使用者不存在，請先註冊"
                )
            
            amount = challenge["amount"]
            
            # 使用債務驗證服務檢查用戶狀態和資金
            from app.core.user_validation import UserValidationService
            validation_service = UserValidationService(self.db)
            
            validation_result = await validation_service.validate_user_can_spend(
                user_id=accepter["_id"],
                amount=amount,
                operation_type="PvP挑戰"
            )
            
            if not validation_result['can_spend']:
                error_code = validation_result.get('error_code', 'UNKNOWN')
                
                if error_code == 'ACCOUNT_DISABLED':
                    message = "帳戶未啟用，無法參與 PvP 挑戰"
                elif error_code == 'ACCOUNT_FROZEN':
                    message = "帳戶已凍結，無法參與 PvP 挑戰"
                elif error_code == 'HAS_DEBT':
                    owed_points = validation_result.get('user_data', {}).get('owed_points', 0)
                    message = f"帳戶有欠款 {owed_points} 點，請先償還後才能參與 PvP 挑戰"
                elif error_code == 'INSUFFICIENT_BALANCE':
                    available_balance = validation_result.get('available_balance', 0)
                    current_points = validation_result.get('user_data', {}).get('points', 0)
                    owed_points = validation_result.get('user_data', {}).get('owed_points', 0)
                    if owed_points > 0:
                        message = f"可用點數不足！需要：{amount} 點，目前點數：{current_points} 點，欠款：{owed_points} 點，實際可用：{available_balance} 點"
                    else:
                        message = f"點數不足！需要：{amount} 點，目前點數：{available_balance} 點"
                else:
                    message = validation_result['message']
                
                return PVPResponse(
                    success=False,
                    message=message
                )
            
            # 使用發起者預先選擇的猜拳
            challenger_choice = challenge["challenger_choice"]
            
            # 判斷勝負
            result = self._determine_winner(challenger_choice, choice)
            
            # 更新挑戰狀態
            await self.db[Collections.PVP_CHALLENGES].update_one(
                {"_id": challenge_oid},
                {
                    "$set": {
                        "accepter": from_user,
                        "accepter_name": accepter.get("name", "未知使用者"),
                        "accepter_choice": choice,
                        "result": result,
                        "status": "completed",
                        "completed_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            # 處理點數轉移
            challenger_user = await self.db[Collections.USERS].find_one({"telegram_id": challenge["challenger"]})
            
            if result == "challenger_wins":
                # 發起者勝利
                winner_name = challenge["challenger_name"]
                loser_name = accepter.get("name", "未知使用者")
                
                # 轉移點數 - 使用安全扣除
                deduction_result = await self._safe_deduct_points(
                    user_id=accepter["_id"],
                    amount=amount,
                    operation_note=f"PVP 失敗失去 {amount} 點 (對手: {winner_name})"
                )
                
                if not deduction_result['success']:
                    # 點數扣除失敗，應該不會發生，但作為安全措施
                    logger.error(f"PVP game point deduction failed: {deduction_result['message']}")
                    return PVPResponse(
                        success=False,
                        message=f"遊戲結算失敗：{deduction_result['message']}"
                    )
                
                # 增加勝利者點數
                await self.db[Collections.USERS].update_one(
                    {"telegram_id": challenge["challenger"]},
                    {"$inc": {"points": amount}}
                )
                
                # 記錄點數變動
                await self._log_point_change(
                    user_id=challenger_user["_id"],
                    change_type="pvp_win",
                    amount=amount,
                    note=f"PVP 勝利獲得 {amount} 點 (對手: {loser_name})"
                )
                await self._log_point_change(
                    user_id=accepter["_id"],
                    change_type="pvp_lose",
                    amount=-amount,
                    note=f"PVP 失敗失去 {amount} 點 (對手: {winner_name})"
                )
                
                return PVPResponse(
                    success=True,
                    message=f"🎉 遊戲結束！\n{self._get_choice_emoji(challenger_choice)} {winner_name} 出 {self._get_choice_name(challenger_choice)}\n{self._get_choice_emoji(choice)} {loser_name} 出 {self._get_choice_name(choice)}\n\n🏆 {winner_name} 勝利！獲得 {amount} 點！",
                    winner=challenge["challenger"],
                    loser=from_user,
                    amount=amount
                )
                
            elif result == "accepter_wins":
                # 接受者勝利
                winner_name = accepter.get("name", "未知使用者")
                loser_name = challenge["challenger_name"]
                
                # 轉移點數 - 使用安全扣除
                deduction_result = await self._safe_deduct_points(
                    user_id=challenger_user["_id"],
                    amount=amount,
                    operation_note=f"PVP 失敗失去 {amount} 點 (對手: {winner_name})"
                )
                
                if not deduction_result['success']:
                    # 點數扣除失敗，應該不會發生，但作為安全措施
                    logger.error(f"PVP game point deduction failed: {deduction_result['message']}")
                    return PVPResponse(
                        success=False,
                        message=f"遊戲結算失敗：{deduction_result['message']}"
                    )
                
                # 增加勝利者點數
                await self.db[Collections.USERS].update_one(
                    {"telegram_id": from_user},
                    {"$inc": {"points": amount}}
                )
                
                # 記錄點數變動
                await self._log_point_change(
                    user_id=accepter["_id"],
                    change_type="pvp_win",
                    amount=amount,
                    note=f"PVP 勝利獲得 {amount} 點 (對手: {loser_name})"
                )
                await self._log_point_change(
                    user_id=challenger_user["_id"],
                    change_type="pvp_lose",
                    amount=-amount,
                    note=f"PVP 失敗失去 {amount} 點 (對手: {winner_name})"
                )
                
                return PVPResponse(
                    success=True,
                    message=f"🎉 遊戲結束！\n{self._get_choice_emoji(challenger_choice)} {loser_name} 出 {self._get_choice_name(challenger_choice)}\n{self._get_choice_emoji(choice)} {winner_name} 出 {self._get_choice_name(choice)}\n\n🏆 {winner_name} 勝利！獲得 {amount} 點！",
                    winner=from_user,
                    loser=challenge["challenger"],
                    amount=amount
                )
                
            else:  # tie
                return PVPResponse(
                    success=True,
                    message=f"🤝 平手！\n{self._get_choice_emoji(challenger_choice)} {challenge['challenger_name']} 出 {self._get_choice_name(challenger_choice)}\n{self._get_choice_emoji(choice)} {accepter.get('name', '未知使用者')} 出 {self._get_choice_name(choice)}\n\n沒有點數變動！",
                    amount=0
                )
                
        except Exception as e:
            logger.error(f"Error accepting PVP challenge: {e}")
            return PVPResponse(
                success=False,
                message="接受挑戰失敗，請稍後再試"
            )
    
    async def cancel_pvp_challenge(self, user_id: str, challenge_id: str):
        """取消 PVP 挑戰"""
        from app.schemas.bot import PVPResponse
        
        try:
            # 將 challenge_id 轉換為 ObjectId
            try:
                challenge_oid = ObjectId(challenge_id)
            except Exception:
                return PVPResponse(
                    success=False,
                    message="無效的挑戰 ID"
                )
            
            # 查找挑戰
            challenge = await self.db[Collections.PVP_CHALLENGES].find_one({
                "_id": challenge_oid,
                "challenger": user_id,
                "status": {"$in": ["pending", "waiting_accepter"]}
            })
            
            if not challenge:
                return PVPResponse(
                    success=False,
                    message="挑戰不存在、已結束或你不是發起者"
                )
            
            # 更新挑戰狀態為取消
            await self.db[Collections.PVP_CHALLENGES].update_one(
                {"_id": challenge_oid},
                {
                    "$set": {
                        "status": "cancelled",
                        "cancelled_at": datetime.now(timezone.utc),
                        "cancel_reason": "使用者主動取消"
                    }
                }
            )
            
            logger.info(f"PVP 挑戰 {challenge_id} 已被使用者 {user_id} 取消")
            
            return PVPResponse(
                success=True,
                message="PVP 挑戰已成功取消"
            )
            
        except Exception as e:
            logger.error(f"Error cancelling PVP challenge: {e}")
            return PVPResponse(
                success=False,
                message="取消挑戰失敗，請稍後再試"
            )

    async def get_user_active_challenges(self, user_id: str) -> dict:
        """查詢使用者的活躍 PVP 挑戰"""
        try:
            # 查找使用者的活躍挑戰
            challenges = await self.db[Collections.PVP_CHALLENGES].find({
                "challenger": user_id,
                "status": {"$in": ["pending", "waiting_accepter"]}
            }).to_list(length=None)
            
            challenge_list = []
            for challenge in challenges:
                challenge_info = {
                    "challenge_id": str(challenge["_id"]),
                    "amount": challenge.get("amount", 0),
                    "status": challenge.get("status", "unknown"),
                    "created_at": challenge.get("created_at"),
                    "expires_at": challenge.get("expires_at"),
                    "chat_id": challenge.get("chat_id")
                }
                challenge_list.append(challenge_info)
            
            logger.info(f"Found {len(challenge_list)} active challenges for user {user_id}")
            
            return {
                "success": True,
                "message": f"找到 {len(challenge_list)} 個活躍挑戰",
                "challenges": challenge_list
            }
            
        except Exception as e:
            logger.error(f"Error getting user active challenges: {e}")
            return {
                "success": False,
                "message": "查詢挑戰時發生錯誤",
                "challenges": []
            }
    
    def _determine_winner(self, choice1: str, choice2: str) -> str:
        """判斷猜拳勝負"""
        if choice1 == choice2:
            return "tie"
        
        winning_combinations = {
            ("rock", "scissors"): "challenger_wins",
            ("paper", "rock"): "challenger_wins", 
            ("scissors", "paper"): "challenger_wins",
            ("scissors", "rock"): "accepter_wins",
            ("rock", "paper"): "accepter_wins",
            ("paper", "scissors"): "accepter_wins"
        }
        
        return winning_combinations.get((choice1, choice2), "tie")
    
    def _get_choice_emoji(self, choice: str) -> str:
        """獲取選擇對應的 emoji"""
        emojis = {
            "rock": "🪨",
            "paper": "📄", 
            "scissors": "✂️"
        }
        return emojis.get(choice, "❓")
    
    def _get_choice_name(self, choice: str) -> str:
        """獲取選擇對應的中文名稱"""
        names = {
            "rock": "石頭",
            "paper": "布",
            "scissors": "剪刀"
        }
        return names.get(choice, "未知")
    
    def _escape_markdown(self, text: str) -> str:
        """轉義 Markdown V2 特殊字符"""
        # MarkdownV2 需要轉義的字符
        escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    async def _log_point_change(self, user_id, change_type: str, amount: int, note: str = ""):
        """記錄點數變動"""
        try:
            # 獲取使用者當前餘額
            user = await self.db[Collections.USERS].find_one({"_id": user_id})
            balance_after = user.get("points", 0) if user else 0
            
            log_entry = {
                "user_id": user_id,
                "type": change_type,  # 使用統一的欄位名稱
                "amount": amount,
                "note": note,
                "balance_after": balance_after,  # 添加餘額記錄
                "created_at": datetime.now(timezone.utc)  # 使用統一的時間欄位名稱
            }
            await self.db[Collections.POINT_LOGS].insert_one(log_entry)
            logger.info(f"Point change logged: user_id={user_id}, type={change_type}, amount={amount}, balance_after={balance_after}")
            
        except Exception as e:
            logger.error(f"Failed to log point change: {e}")
            # 不拋出異常，避免影響主要業務邏輯
    
    async def simple_accept_pvp_challenge(self, from_user: str, challenge_id: str):
        """簡單 PVP 挑戰接受 - 純 50% 機率決定勝負"""
        from app.schemas.bot import PVPResponse
        
        logger.info(f"Simple PVP accept: user {from_user}, challenge {challenge_id}")
        
        try:
            # 將 challenge_id 轉換為 ObjectId
            try:
                challenge_oid = ObjectId(challenge_id)
            except Exception as e:
                logger.error(f"Invalid challenge_id format: {challenge_id}, error: {e}")
                return PVPResponse(
                    success=False,
                    message="無效的挑戰 ID"
                )
            
            # 查找挑戰
            challenge = await self.db[Collections.PVP_CHALLENGES].find_one({
                "_id": challenge_oid,
                "status": {"$in": ["pending", "waiting_accepter"]}
            })
            
            logger.info(f"Looking for challenge {challenge_id}, found: {challenge is not None}")
            
            if not challenge:
                # 嘗試查找任何狀態的挑戰來調試
                any_challenge = await self.db[Collections.PVP_CHALLENGES].find_one({"_id": challenge_oid})
                if any_challenge:
                    logger.warning(f"Challenge {challenge_id} exists but has status: {any_challenge.get('status')}")
                else:
                    logger.warning(f"Challenge {challenge_id} does not exist in database")
                
                return PVPResponse(
                    success=False,
                    message="挑戰不存在或已結束"
                )
            
            # 檢查是否過期
            expires_at = challenge["expires_at"]
            if not expires_at.tzinfo:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires_at:
                await self.db[Collections.PVP_CHALLENGES].update_one(
                    {"_id": challenge_oid},
                    {"$set": {"status": "expired"}}
                )
                return PVPResponse(
                    success=False,
                    message="挑戰已過期"
                )
            
            # 檢查是否為發起者本人
            if challenge["challenger"] == from_user:
                return PVPResponse(
                    success=False,
                    message="不能接受自己的挑戰！"
                )
            
            # 檢查接受者是否存在
            accepter = await self.db[Collections.USERS].find_one({"telegram_id": from_user})
            if not accepter:
                return PVPResponse(
                    success=False,
                    message="使用者不存在，請先註冊"
                )
            
            amount = challenge["amount"]
            
            # 使用債務驗證服務檢查接受者狀態和資金
            from app.core.user_validation import UserValidationService
            validation_service = UserValidationService(self.db)
            
            validation_result = await validation_service.validate_user_can_spend(
                user_id=accepter["_id"],
                amount=amount,
                operation_type="PvP挑戰"
            )
            
            if not validation_result['can_spend']:
                error_code = validation_result.get('error_code', 'UNKNOWN')
                
                if error_code == 'ACCOUNT_DISABLED':
                    message = "帳戶未啟用，無法參與 PvP 挑戰"
                elif error_code == 'ACCOUNT_FROZEN':
                    message = "帳戶已凍結，無法參與 PvP 挑戰"
                elif error_code == 'HAS_DEBT':
                    owed_points = validation_result.get('user_data', {}).get('owed_points', 0)
                    message = f"帳戶有欠款 {owed_points} 點，請先償還後才能參與 PvP 挑戰"
                elif error_code == 'INSUFFICIENT_BALANCE':
                    available_balance = validation_result.get('available_balance', 0)
                    current_points = validation_result.get('user_data', {}).get('points', 0)
                    owed_points = validation_result.get('user_data', {}).get('owed_points', 0)
                    if owed_points > 0:
                        message = f"可用點數不足！需要：{amount} 點，目前點數：{current_points} 點，欠款：{owed_points} 點，實際可用：{available_balance} 點"
                    else:
                        message = f"點數不足！需要：{amount} 點，目前點數：{available_balance} 點"
                else:
                    message = validation_result['message']
                
                return PVPResponse(
                    success=False,
                    message=message
                )
            
            # 檢查發起者也有足夠點數
            challenger_user = await self.db[Collections.USERS].find_one({"telegram_id": challenge["challenger"]})
            if not challenger_user:
                return PVPResponse(
                    success=False,
                    message="發起者不存在"
                )
                
            challenger_validation = await validation_service.validate_user_can_spend(
                user_id=challenger_user["_id"],
                amount=amount,
                operation_type="PvP挑戰"
            )
            
            if not challenger_validation['can_spend']:
                return PVPResponse(
                    success=False,
                    message="發起者點數不足，挑戰無效"
                )
            
            # 50% 機率決定勝負
            accepter_wins = bool(random.getrandbits(1))
            logger.info(f"PVP result: accepter_wins = {accepter_wins}")
            
            # 更新挑戰狀態
            await self.db[Collections.PVP_CHALLENGES].update_one(
                {"_id": challenge_oid},
                {
                    "$set": {
                        "accepter": from_user,
                        "accepter_name": accepter.get("name", "未知使用者"),
                        "result": "accepter_wins" if accepter_wins else "challenger_wins",
                        "status": "completed",
                        "completed_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            # 處理點數轉移
            logger.info(f"Starting point transfer: amount={amount}, accepter_wins={accepter_wins}")
            
            if accepter_wins:
                # 接受者勝利
                winner_name = accepter.get("name", "未知使用者")
                loser_name = challenge["challenger_name"]
                logger.info(f"Accepter wins: {winner_name} gets {amount} points from {loser_name}")
                
                # 使用安全扣除
                deduction_result = await self._safe_deduct_points(
                    user_id=challenger_user["_id"],
                    amount=amount,
                    operation_note=f"PVP 失敗失去 {amount} 點 (對手: {winner_name})"
                )
                
                if not deduction_result['success']:
                    logger.error(f"PVP game point deduction failed: {deduction_result['message']}")
                    return PVPResponse(
                        success=False,
                        message=f"遊戲結算失敗：{deduction_result['message']}"
                    )
                
                # 增加勝利者點數並記錄
                update_result = await self.db[Collections.USERS].update_one(
                    {"telegram_id": from_user},
                    {"$inc": {"points": amount}}
                )
                
                if update_result.modified_count > 0:
                    # 記錄勝利者點數變動（敗方的點數扣除已在 _safe_deduct_points 中記錄）
                    await self._log_point_change(
                        user_id=accepter["_id"],
                        change_type="pvp_win",
                        amount=amount,
                        note=f"PVP 勝利獲得 {amount} 點 (對手: {loser_name})"
                    )
                else:
                    logger.error("Failed to update accepter's points")
                    return PVPResponse(
                        success=False,
                        message="點數增加失敗"
                    )
                
                return PVPResponse(
                    success=True,
                    message=f"🎉 *遊戲結束！*\n\n🏆 *{self._escape_markdown(winner_name)}* 勝利！獲得 *{amount}* 點！\n💔 *{self._escape_markdown(loser_name)}* 失去 *{amount}* 點！",
                    winner=from_user,
                    loser=challenge["challenger"],
                    amount=amount
                )
                
            else:
                # 發起者勝利
                winner_name = challenge["challenger_name"]
                loser_name = accepter.get("name", "未知使用者")
                logger.info(f"Challenger wins: {winner_name} gets {amount} points from {loser_name}")
                
                # 使用安全扣除
                deduction_result = await self._safe_deduct_points(
                    user_id=accepter["_id"],
                    amount=amount,
                    operation_note=f"PVP 失敗失去 {amount} 點 (對手: {winner_name})"
                )
                
                if not deduction_result['success']:
                    logger.error(f"PVP game point deduction failed: {deduction_result['message']}")
                    return PVPResponse(
                        success=False,
                        message=f"遊戲結算失敗：{deduction_result['message']}"
                    )
                
                # 增加勝利者點數並記錄
                update_result = await self.db[Collections.USERS].update_one(
                    {"telegram_id": challenge["challenger"]},
                    {"$inc": {"points": amount}}
                )
                
                if update_result.modified_count > 0:
                    # 記錄勝利者點數變動（敗方的點數扣除已在 _safe_deduct_points 中記錄）
                    await self._log_point_change(
                        user_id=challenger_user["_id"],
                        change_type="pvp_win",
                        amount=amount,
                        note=f"PVP 勝利獲得 {amount} 點 (對手: {loser_name})"
                    )
                else:
                    logger.error("Failed to update challenger's points")
                    return PVPResponse(
                        success=False,
                        message="點數增加失敗"
                    )
                
                return PVPResponse(
                    success=True,
                    message=f"🎉 *遊戲結束！*\n\n🏆 *{self._escape_markdown(winner_name)}* 勝利！獲得 *{amount}* 點！\n💔 *{self._escape_markdown(loser_name)}* 失去 *{amount}* 點！",
                    winner=challenge["challenger"],
                    loser=from_user,
                    amount=amount
                )
                
        except Exception as e:
            logger.error(f"Error in simple PVP challenge: {e}")
            return PVPResponse(
                success=False,
                message="接受挑戰失敗，請稍後再試"
            )