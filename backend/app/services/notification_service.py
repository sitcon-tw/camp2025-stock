from __future__ import annotations
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database, Collections
from app.config import settings
from typing import Optional
import logging
import requests

logger = logging.getLogger(__name__)

def get_notification_service() -> NotificationService:
    """NotificationService 的依賴注入函數"""
    return NotificationService()

class NotificationService:
    """通知服務 - 負責處理所有通知相關的功能"""
    
    def __init__(self, db: AsyncIOMotorDatabase = None):
        if db is None:
            self.db = get_database()
        else:
            self.db = db
    
    async def send_trade_notifications(self, buy_order: dict, sell_order: dict, trade_quantity: int, 
                                     trade_price: float, trade_amount: float, is_system_sale: bool, session=None):
        """傳送交易通知給買方和賣方"""
        try:
            # 獲取買方使用者資訊
            buy_user = await self.db[Collections.USERS].find_one({"_id": buy_order["user_id"]}, session=session)
            if not buy_user or not buy_user.get("telegram_id"):
                logger.warning(f"無法傳送買方通知：使用者 {buy_order['user_id']} 未設定 telegram_id")
            else:
                await self._send_single_trade_notification(
                    user_telegram_id=buy_user["telegram_id"],
                    action="buy",
                    quantity=trade_quantity,
                    price=trade_price,
                    total_amount=trade_amount,
                    order_id=str(buy_order["_id"])
                )
            
            # 獲取賣方使用者資訊（如果不是系統 IPO 交易）
            if not is_system_sale and sell_order:
                sell_user = await self.db[Collections.USERS].find_one({"_id": sell_order["user_id"]}, session=session)
                if not sell_user or not sell_user.get("telegram_id"):
                    logger.warning(f"無法傳送賣方通知：使用者 {sell_order['user_id']} 未設定 telegram_id")
                else:
                    await self._send_single_trade_notification(
                        user_telegram_id=sell_user["telegram_id"],
                        action="sell",
                        quantity=trade_quantity,
                        price=trade_price,
                        total_amount=trade_amount,
                        order_id=str(sell_order["_id"])
                    )
                    
        except Exception as e:
            # 通知傳送失敗不應該影響交易本身
            logger.error(f"傳送交易通知時發生錯誤: {e}")

    async def _send_single_trade_notification(self, user_telegram_id: int, action: str, quantity: int, 
                                            price: float, total_amount: float, order_id: str):
        """傳送單一交易通知"""
        try:
            if not settings.CAMP_TELEGRAM_BOT_API_URL or not settings.CAMP_INTERNAL_API_KEY:
                logger.warning("Telegram Bot API 設定不完整，跳過通知傳送")
                return
            
            # 構建通知請求
            notification_url = f"{settings.CAMP_TELEGRAM_BOT_API_URL.rstrip('/')}/bot/notification/trade"
            
            payload = {
                "user_id": user_telegram_id,
                "action": action,
                "quantity": quantity,
                "price": price,
                "total_amount": total_amount,
                "order_id": order_id
            }
            
            headers = {
                "Content-Type": "application/json",
                "token": settings.CAMP_INTERNAL_API_KEY
            }
            
            # 傳送通知（設定短超時避免阻塞交易）
            response = requests.post(
                notification_url,
                json=payload,
                headers=headers,
                timeout=5  # 5秒超時
            )
            
            if response.status_code == 200:
                logger.info(f"成功傳送 {action} 交易通知給使用者 {user_telegram_id}")
            else:
                logger.warning(f"傳送交易通知失敗: HTTP {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            logger.warning(f"傳送交易通知超時，使用者: {user_telegram_id}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"傳送交易通知網路錯誤: {e}")
        except Exception as e:
            logger.error(f"傳送交易通知發生未預期錯誤: {e}")

    async def send_cancellation_notification(self, user_id: str, order_id: str, 
                                           order_type: str, side: str, quantity: int,
                                           price: float, reason: str):
        """發送取消訂單通知"""
        try:
            if not settings.CAMP_TELEGRAM_BOT_API_URL or not settings.CAMP_INTERNAL_API_KEY:
                logger.warning("Telegram Bot API 設定不完整，跳過取消通知傳送")
                return
            
            # 獲取使用者的 Telegram ID
            user = await self.db[Collections.USERS].find_one({"_id": user_id})
            if not user or not user.get("telegram_id"):
                logger.warning(f"無法傳送取消通知：使用者 {user_id} 未設定 telegram_id")
                return
            
            # 構建取消通知
            action_text = "買入" if side == "buy" else "賣出"
            type_text = "市價單" if order_type == "market" else "限價單"
            
            message = f"🚫 您的訂單已取消\n\n• 訂單號碼：{order_id}\n• 類型：{type_text}\n• 操作：{action_text}\n• 數量：{quantity}\n• 價格：{price:.2f}\n• 取消原因：{reason}"
            
            notification_url = f"{settings.CAMP_TELEGRAM_BOT_API_URL.rstrip('/')}/bot/direct/send"
            
            payload = {
                "user_id": user["telegram_id"],
                "message": message,
                "parse_mode": "MarkdownV2"
            }
            
            headers = {
                "Content-Type": "application/json",
                "token": settings.CAMP_INTERNAL_API_KEY
            }
            
            response = requests.post(
                notification_url,
                json=payload,
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"成功傳送取消通知給使用者 {user['telegram_id']}")
            else:
                logger.warning(f"傳送取消通知失敗: HTTP {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"傳送取消通知發生錯誤: {e}")