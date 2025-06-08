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
    """PVP 挑戰管理器，處理倒數計時和衝突"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.active_challenges: Dict[str, Dict] = {}  # challenge_id -> challenge_info
        self.user_challenges: Dict[str, str] = {}  # user_id -> challenge_id
        self.timeout_tasks: Dict[str, asyncio.Task] = {}  # challenge_id -> timeout_task
        
    async def create_challenge(self, user_id: str, username: str, amount: int, chat_id: str) -> Dict:
        """建立新的 PVP 挑戰，處理衝突情況"""
        
        # 檢查用戶是否已有進行中的挑戰
        existing_challenge_id = self.user_challenges.get(user_id)
        if existing_challenge_id and existing_challenge_id in self.active_challenges:
            existing_challenge = self.active_challenges[existing_challenge_id]
            
            # 計算剩餘時間
            elapsed = datetime.now() - existing_challenge['created_at']
            remaining = timedelta(minutes=3) - elapsed
            
            if remaining.total_seconds() > 0:
                # 有衝突，返回衝突資訊
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
                "status": "waiting_creator"
            }
            
            self.active_challenges[challenge_id] = challenge_info
            self.user_challenges[user_id] = challenge_id
            
            # 啟動 3 分鐘倒數計時
            timeout_task = asyncio.create_task(self._timeout_challenge(challenge_id))
            self.timeout_tasks[challenge_id] = timeout_task
            
            logger.info(f"⏰ PVP 挑戰 {challenge_id} 已建立，將在 3 分鐘後超時")
            
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
        """取消用戶現有的挑戰"""
        existing_challenge_id = self.user_challenges.get(user_id)
        if existing_challenge_id:
            await self._cancel_challenge(existing_challenge_id, "用戶主動取消")
            return True
        return False
    
    async def _timeout_challenge(self, challenge_id: str):
        """3 分鐘倒數計時，時間到自動取消挑戰"""
        try:
            # 等待 3 分鐘
            await asyncio.sleep(180)  # 3 minutes = 180 seconds
            
            # 檢查挑戰是否仍然存在
            if challenge_id in self.active_challenges:
                await self._cancel_challenge(challenge_id, "超時自動取消")
                
        except asyncio.CancelledError:
            # 任務被取消（挑戰被手動取消或完成）
            logger.info(f"⏰ PVP 挑戰 {challenge_id} 倒數計時被取消")
        except Exception as e:
            logger.error(f"❌ PVP 挑戰 {challenge_id} 倒數計時出錯: {e}")
    
    async def _cancel_challenge(self, challenge_id: str, reason: str):
        """取消挑戰並清理資源"""
        if challenge_id not in self.active_challenges:
            return
            
        challenge_info = self.active_challenges[challenge_id]
        user_id = challenge_info["user_id"]
        username = challenge_info["username"]
        chat_id = challenge_info["chat_id"]
        amount = challenge_info["amount"]
        
        try:
            # 嘗試調用後端 API 取消挑戰
            try:
                cancel_response = api_helper.post("/api/bot/pvp/cancel", protected_route=True, json={
                    "challenge_id": challenge_id,
                    "user_id": user_id
                })
                
                if not cancel_response.get("success"):
                    logger.warning(f"⚠️ 後端取消 PVP 挑戰失敗: {cancel_response.get('message', 'Unknown error')}")
                    
            except Exception as api_error:
                logger.warning(f"⚠️ 無法調用後端取消 API: {api_error}")
            
            # 發送取消訊息到群組
            cancel_message = (
                f"⏰ **PVP 挑戰已取消**\n\n"
                f"**發起者**: {escape_markdown(username, 2)}\n"
                f"**金額**: {amount} 點\n"
                f"**原因**: {escape_markdown(reason, 2)}"
            )
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=cancel_message,
                parse_mode=ParseMode.MARKDOWN_V2
            )
            
            logger.info(f"🚫 PVP 挑戰 {challenge_id} 已取消: {reason}")
            
        except Exception as e:
            logger.error(f"❌ 取消 PVP 挑戰 {challenge_id} 時出錯: {e}")
        
        finally:
            # 清理資源
            self._cleanup_challenge(challenge_id)
    
    def _cleanup_challenge(self, challenge_id: str):
        """清理挑戰相關資源"""
        if challenge_id in self.active_challenges:
            challenge_info = self.active_challenges[challenge_id]
            user_id = challenge_info["user_id"]
            
            # 移除記錄
            del self.active_challenges[challenge_id]
            if user_id in self.user_challenges:
                del self.user_challenges[user_id]
            
            # 取消倒數計時任務
            if challenge_id in self.timeout_tasks:
                task = self.timeout_tasks[challenge_id]
                if not task.done():
                    task.cancel()
                del self.timeout_tasks[challenge_id]
    
    async def complete_challenge(self, challenge_id: str):
        """標記挑戰為完成並清理資源"""
        logger.info(f"✅ PVP 挑戰 {challenge_id} 已完成")
        self._cleanup_challenge(challenge_id)
    
    def get_challenge_info(self, challenge_id: str) -> Optional[Dict]:
        """獲取挑戰資訊"""
        return self.active_challenges.get(challenge_id)
    
    def get_user_challenge(self, user_id: str) -> Optional[str]:
        """獲取用戶當前的挑戰 ID"""
        return self.user_challenges.get(user_id)

# 全域 PVP 管理器實例
pvp_manager: Optional[PVPManager] = None

def get_pvp_manager() -> PVPManager:
    """獲取 PVP 管理器實例"""
    global pvp_manager
    if pvp_manager is None:
        raise RuntimeError("PVP Manager not initialized")
    return pvp_manager

def init_pvp_manager(bot: Bot):
    """初始化 PVP 管理器"""
    global pvp_manager
    pvp_manager = PVPManager(bot)
    logger.info("🎯 PVP 管理器已初始化")