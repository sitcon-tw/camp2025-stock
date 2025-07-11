import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Set
from telegram import Bot
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

from utils.logger import setup_logger
from utils import api_helper

logger = setup_logger(__name__)


class PVPManager:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.active_challenges: Dict[str, Dict] = {}  # challenge_id -> challenge_info
        self.user_challenges: Dict[str, str] = {}  # user_id -> challenge_id
        self.timeout_tasks: Dict[str, asyncio.Task] = {}  # challenge_id -> timeout_task
        self.challenge_messages: Dict[str, Dict] = {}  # challenge_id -> {"chat_id": ..., "message_id": ...}

    async def create_challenge(self, user_id: str, username: str, amount: int, chat_id: str) -> Dict:
        existing_challenge_id = self.user_challenges.get(user_id)
        if existing_challenge_id and existing_challenge_id in self.active_challenges:
            existing_challenge = self.active_challenges[existing_challenge_id]

            elapsed = datetime.now() - existing_challenge['created_at']
            remaining = timedelta(hours=3) - elapsed

            if remaining.total_seconds() > 0:
                return {
                    "conflict": True,
                    "existing_challenge": existing_challenge,
                    "remaining_time": int(remaining.total_seconds())
                }

        # 調用後端 API 建立挑戰
        response = api_helper.post("/api/bot/pvp/create", protected_route=True, json={
            "from_user": user_id,
            "amount": amount,
            "chat_id": chat_id
        })

        if response.get("success"):
            challenge_id = response.get("challenge_id")

            # 記錄挑戰資訊
            challenge_info = {
                "challenge_id": challenge_id,
                "user_id": user_id,
                "username": username,
                "amount": amount,
                "chat_id": chat_id,
                "created_at": datetime.now(),
                "status": "waiting_accepter"
            }

            self.active_challenges[challenge_id] = challenge_info
            self.user_challenges[user_id] = challenge_id

            # 啟動 3 小時倒數計時
            timeout_task = asyncio.create_task(self._timeout_challenge(challenge_id))
            self.timeout_tasks[challenge_id] = timeout_task

            logger.info(f"Created challenge {challenge_id}")

            return {
                "conflict": False,
                "challenge_id": challenge_id,
                "response": response
            }
        else:
            return {
                "conflict": False,
                "error": True,
                "response": response
            }

    async def cancel_existing_challenge(self, user_id: str) -> bool:
        logger.info(f"cancel_existing_challenge called with user_id: {user_id}")
        
        # 先檢查本地狀態
        existing_challenge_id = self.user_challenges.get(user_id)
        logger.info(f"local existing_challenge_id: {existing_challenge_id}")
        
        if existing_challenge_id and existing_challenge_id in self.active_challenges:
            logger.info("Found local challenge, cancelling via _cancel_challenge")
            await self._cancel_challenge(existing_challenge_id, "使用者主動取消")
            result = existing_challenge_id not in self.active_challenges
            logger.info(f"Local challenge cleanup result: {result}")
            return result
        
        # 如果本地沒有，直接通過 API 查詢並取消使用者的活躍挑戰
        logger.info("No local challenge found, attempting direct API cancellation")
        try:
            # 查詢使用者的活躍挑戰
            response = api_helper.get(f"/api/bot/pvp/user-challenges/{user_id}", protected_route=True)
            if response and response.get("success") and response.get("challenges"):
                challenges = response.get("challenges", [])
                logger.info(f"Found {len(challenges)} backend challenges for user {user_id}")
                
                # 取消所有活躍的挑戰
                cancelled_any = False
                for challenge in challenges:
                    challenge_id = challenge.get("challenge_id")
                    if challenge_id:
                        cancel_result = await self._direct_api_cancel(user_id, challenge_id)
                        if cancel_result:
                            cancelled_any = True
                            logger.info(f"Successfully cancelled backend challenge {challenge_id}")
                
                return cancelled_any
            else:
                logger.info("No backend challenges found or API error")
                return False
                
        except Exception as e:
            logger.error(f"Error during direct API cancellation: {e}")
            return False

    async def _direct_api_cancel(self, user_id: str, challenge_id: str) -> bool:
        """直接通過 API 取消挑戰，不經過本地狀態管理"""
        try:
            logger.info(f"Direct API cancel: user {user_id}, challenge {challenge_id}")
            cancel_response = api_helper.post("/api/bot/pvp/cancel", protected_route=True, json={
                "challenge_id": challenge_id,
                "user_id": user_id
            })
            
            if cancel_response and cancel_response.get("success"):
                logger.info(f"Direct API cancellation successful for challenge {challenge_id}")
                return True
            else:
                error_msg = cancel_response.get("message", "Unknown error") if cancel_response else "No response"
                logger.warning(f"Direct API cancellation failed for challenge {challenge_id}: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"Exception in direct API cancel: {e}")
            return False

    async def _timeout_challenge(self, challenge_id: str):
        try:
            await asyncio.sleep(10800)  # 3 hours = 10800 seconds

            if challenge_id in self.active_challenges:
                # 3小時後直接取消挑戰
                await self._cancel_challenge(challenge_id, "超時自動取消")

        except asyncio.CancelledError:
            logger.info(f"Challenge {challenge_id} countdown is canceled")


    async def _cancel_challenge(self, challenge_id: str, reason: str):
        if challenge_id not in self.active_challenges:
            return

        challenge_info = self.active_challenges[challenge_id]
        user_id = challenge_info["user_id"]
        username = challenge_info["username"]
        chat_id = challenge_info["chat_id"]
        amount = challenge_info["amount"]

        api_cancel_success = False

        cancel_response = api_helper.post("/api/bot/pvp/cancel", protected_route=True, json={
            "challenge_id": challenge_id,
            "user_id": user_id
        })

        if cancel_response.get("success"):
            api_cancel_success = True
            logger.info(f"Successfully canceled {challenge_id}")
        else:
            logger.warning(f"Failed to cancel PVP challenge: {cancel_response.get('message', 'Unknown error')}")

        # API will return reason in Chinese? Fr?
        # Probably consider some short word or so, though this won't affect how code works.
        if api_cancel_success or reason == "超時自動取消":
            await self.bot.send_message(
                text=f"⏰ **PVP 挑戰已取消**\n\n"
                     f"**發起者**: {escape_markdown(username, 2)}\n"
                     f"**金額**: {escape_markdown(str(amount), 2)} 點\n"
                     f"**原因**: {escape_markdown(reason, 2)}",
                chat_id=chat_id,
                parse_mode=ParseMode.MARKDOWN_V2
            )

            logger.info(f"Challenge {challenge_id} is canceled: {reason}")

            # 編輯原始挑戰訊息，移除按鈕並顯示已取消狀態
            await self.edit_challenge_message(
                challenge_id,
                f"❌ **PVP 挑戰已取消**\n\n"
                f"**發起者**: {escape_markdown(username, 2)}\n"
                f"**金額**: {escape_markdown(str(amount), 2)} 點\n"
                f"**原因**: {escape_markdown(reason, 2)}\n\n"
                f"此挑戰已失效，無法再進行操作\\."
            )

            self._cleanup_challenge(challenge_id)
        else:
            logger.error(f"Cannot cancel challenge {challenge_id}, backend's fault!")

    def _cleanup_challenge(self, challenge_id: str):
        if challenge_id in self.active_challenges:
            challenge_info = self.active_challenges[challenge_id]
            user_id = challenge_info["user_id"]

            # 移除記錄
            del self.active_challenges[challenge_id]
            if user_id in self.user_challenges:
                del self.user_challenges[user_id]

            # 清理訊息記錄
            if challenge_id in self.challenge_messages:
                del self.challenge_messages[challenge_id]

            # 取消倒數計時任務
            if challenge_id in self.timeout_tasks:
                task = self.timeout_tasks[challenge_id]
                if not task.done():
                    task.cancel()
                del self.timeout_tasks[challenge_id]

    async def complete_challenge(self, challenge_id: str):
        logger.info(f"Challenge {challenge_id} is completed!")
        self._cleanup_challenge(challenge_id)

    def get_challenge_info(self, challenge_id: str) -> Optional[Dict]:
        return self.active_challenges.get(challenge_id)

    def update_challenge_status(self, challenge_id: str, status: str):
        if challenge_id in self.active_challenges:
            self.active_challenges[challenge_id]["status"] = status
            logger.info(f"Challenge {challenge_id} status updated to: {status}")

    def get_user_challenge(self, user_id: str) -> Optional[str]:
        return self.user_challenges.get(user_id)
    
    def store_challenge_message(self, challenge_id: str, message_id: int):
        """儲存挑戰訊息的ID，用於後續編輯或刪除"""
        if challenge_id in self.active_challenges:
            chat_id = self.active_challenges[challenge_id]["chat_id"]
            self.challenge_messages[challenge_id] = {
                "chat_id": chat_id,
                "message_id": message_id
            }
            logger.info(f"Stored message {message_id} for challenge {challenge_id}")
    
    async def edit_challenge_message(self, challenge_id: str, new_text: str, reply_markup=None):
        """編輯挑戰訊息"""
        if challenge_id in self.challenge_messages:
            message_info = self.challenge_messages[challenge_id]
            try:
                await self.bot.edit_message_text(
                    text=new_text,
                    chat_id=message_info["chat_id"],
                    message_id=message_info["message_id"],
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=reply_markup
                )
                logger.info(f"Edited message for challenge {challenge_id}")
            except Exception as e:
                error_msg = str(e)
                if "Message is not modified" in error_msg:
                    logger.debug(f"Message for challenge {challenge_id} is already up to date")
                else:
                    logger.error(f"Failed to edit message for challenge {challenge_id}: {e}")


pvp_manager: Optional[PVPManager] = None


def get_pvp_manager() -> PVPManager:
    global pvp_manager
    if pvp_manager is None:
        raise RuntimeError("PVP Manager not initialized")
    return pvp_manager


def init_pvp_manager(bot: Bot):
    global pvp_manager
    pvp_manager = PVPManager(bot)
    logger.info("Initialized PVP Manager")
