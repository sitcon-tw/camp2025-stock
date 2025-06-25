from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class NotificationSender:
    """
    Telegram Bot DM 通知傳送器
    用於傳送私人訊息給特定使用者的通知功能
    """
    
    def __init__(self, bot: Bot):
        """
        初始化通知傳送器
        
        Args:
            bot: Telegram Bot 實例
        """
        self.bot = bot
    
    async def send_dm(
        self, 
        user_id: int, 
        message: str, 
        parse_mode: Optional[str] = ParseMode.MARKDOWN_V2,
        disable_web_page_preview: bool = True
    ) -> bool:
        """
        傳送私人訊息給指定使用者
        
        Args:
            user_id: Telegram 使用者 ID
            message: 要傳送的訊息內容
            parse_mode: 訊息格式化模式 (默認為 MARKDOWN_V2)
            disable_web_page_preview: 是否停用網頁預覽
            
        Returns:
            bool: 傳送成功返回 True，失敗返回 False
        """
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview
            )
            logger.info(f"DM notification sent successfully to user {user_id}")
            return True
            
        except TelegramError as e:
            logger.error(f"Failed to send DM to user {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending DM to user {user_id}: {e}")
            return False
    
    async def send_bulk_dm(
        self, 
        user_ids: List[int], 
        message: str,
        parse_mode: Optional[str] = ParseMode.MARKDOWN_V2,
        delay_seconds: float = 0.1
    ) -> Dict[str, List[int]]:
        """
        批量傳送私人訊息給多個使用者
        
        Args:
            user_ids: Telegram 使用者 ID 列表
            message: 要傳送的訊息內容
            parse_mode: 訊息格式化模式
            delay_seconds: 傳送間隔時間 (避免速率限制)
            
        Returns:
            Dict: 包含成功和失敗的使用者 ID 列表
        """
        success_users = []
        failed_users = []
        
        for user_id in user_ids:
            success = await self.send_dm(user_id, message, parse_mode)
            
            if success:
                success_users.append(user_id)
            else:
                failed_users.append(user_id)
            
            # 避免觸發 Telegram API 速率限制
            if delay_seconds > 0:
                await asyncio.sleep(delay_seconds)
        
        logger.info(f"Bulk DM completed: {len(success_users)} success, {len(failed_users)} failed")
        
        return {
            "success": success_users,
            "failed": failed_users
        }
    
    async def send_notification(
        self,
        user_id: int,
        notification_type: str,
        title: str,
        content: str,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        傳送格式化的通知訊息
        
        Args:
            user_id: Telegram 使用者 ID
            notification_type: 通知類型 (如: "trade", "transfer", "system")
            title: 通知標題
            content: 通知內容
            additional_data: 額外的通知數據
            
        Returns:
            bool: 傳送成功返回 True，失敗返回 False
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 構建通知訊息
        message_parts = [
            f"🔔 *{title}*",
            f"",
            f"{content}",
            f"",
            f"📅 時間: `{timestamp}`",
            f"🏷️ 類型: `{notification_type}`"
        ]
        
        # 添加額外數據
        if additional_data:
            message_parts.append("")
            message_parts.append("📋 *詳細資訊:*")
            for key, value in additional_data.items():
                message_parts.append(f"• {key}: `{value}`")
        
        message = "\n".join(message_parts)
        
        return await self.send_dm(user_id, message)
    
    async def send_trade_notification(
        self,
        user_id: int,
        action: str,  # "buy" or "sell"
        stock_symbol: str,
        quantity: int,
        price: float,
        total_amount: float,
        order_id: Optional[str] = None
    ) -> bool:
        """
        傳送交易通知
        
        Args:
            user_id: 使用者 ID
            action: 交易動作 ("buy" 或 "sell")
            stock_symbol: 股票代號
            quantity: 交易數量
            price: 交易價格
            total_amount: 交易總金額
            order_id: 訂單 ID
            
        Returns:
            bool: 傳送成功返回 True
        """
        action_text = "買入" if action == "buy" else "賣出"
        emoji = "📈" if action == "buy" else "📉"
        
        additional_data = {
            "股票代號": stock_symbol,
            "數量": f"{quantity} 股",
            "價格": f"${price:.2f}",
            "總金額": f"${total_amount:.2f}"
        }
        
        if order_id:
            additional_data["訂單編號"] = order_id
        
        return await self.send_notification(
            user_id=user_id,
            notification_type="trade",
            title=f"{emoji} 交易通知 - {action_text}",
            content=f"您的{action_text}訂單已完成",
            additional_data=additional_data
        )
    
    async def send_transfer_notification(
        self,
        user_id: int,
        transfer_type: str,  # "sent" or "received"
        amount: float,
        other_user: str,
        transfer_id: Optional[str] = None
    ) -> bool:
        """
        傳送轉帳通知
        
        Args:
            user_id: 使用者 ID
            transfer_type: 轉帳類型 ("sent" 或 "received")
            amount: 轉帳金額
            other_user: 對方使用者名稱
            transfer_id: 轉帳 ID
            
        Returns:
            bool: 傳送成功返回 True
        """
        if transfer_type == "sent":
            title = "💸 轉帳通知 - 已傳送"
            content = f"您已成功轉帳給 {other_user}"
        else:
            title = "💰 轉帳通知 - 已接收"
            content = f"您收到來自 {other_user} 的轉帳"
        
        additional_data = {
            "金額": f"${amount:.2f}",
            "對方": other_user
        }
        
        if transfer_id:
            additional_data["轉帳編號"] = transfer_id
        
        return await self.send_notification(
            user_id=user_id,
            notification_type="transfer",
            title=title,
            content=content,
            additional_data=additional_data
        )
    
    async def send_system_notification(
        self,
        user_id: int,
        title: str,
        content: str,
        priority: str = "normal"  # "low", "normal", "high", "urgent"
    ) -> bool:
        """
        傳送系統通知
        
        Args:
            user_id: 使用者 ID
            title: 通知標題
            content: 通知內容
            priority: 優先級
            
        Returns:
            bool: 傳送成功返回 True
        """
        priority_emojis = {
            "low": "ℹ️",
            "normal": "📢",
            "high": "⚠️",
            "urgent": "🚨"
        }
        
        emoji = priority_emojis.get(priority, "📢")
        
        return await self.send_notification(
            user_id=user_id,
            notification_type="system",
            title=f"{emoji} 系統通知 - {title}",
            content=content,
            additional_data={"優先級": priority.upper()}
        )