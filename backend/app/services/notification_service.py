from __future__ import annotations
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database, Collections
from app.core.config_refactored import config
from app.services.pending_notification_service import get_pending_notification_service
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
            if not config.external_services.telegram_bot_api_url or not config.security.internal_api_key:
                logger.warning("Telegram Bot API 設定不完整，跳過通知傳送")
                return
            
            # 構建通知請求
            notification_url = f"{config.external_services.telegram_bot_api_url.rstrip('/')}/bot/notification/trade"
            
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
                "token": config.security.internal_api_key
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
                await self._store_failed_notification(user_telegram_id, action, quantity, price, total_amount, order_id)
                
        except requests.exceptions.Timeout:
            logger.warning(f"傳送交易通知超時，使用者: {user_telegram_id}")
            await self._store_failed_notification(user_telegram_id, action, quantity, price, total_amount, order_id)
        except requests.exceptions.RequestException as e:
            logger.warning(f"傳送交易通知網路錯誤: {e}")
            await self._store_failed_notification(user_telegram_id, action, quantity, price, total_amount, order_id)
        except Exception as e:
            logger.error(f"傳送交易通知發生未預期錯誤: {e}")
            await self._store_failed_notification(user_telegram_id, action, quantity, price, total_amount, order_id)

    async def send_cancellation_notification(self, user_id: str, order_id: str, 
                                           order_type: str, side: str, quantity: int,
                                           price: float, reason: str):
        """發送取消訂單通知"""
        try:
            if not config.external_services.telegram_bot_api_url or not config.security.internal_api_key:
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
            
            notification_url = f"{config.external_services.telegram_bot_api_url.rstrip('/')}/bot/direct/send"
            
            payload = {
                "user_id": user["telegram_id"],
                "message": message,
                "parse_mode": "MarkdownV2"
            }
            
            headers = {
                "Content-Type": "application/json",
                "token": config.security.internal_api_key
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
    
    async def _store_failed_notification(self, user_telegram_id: int, action: str, quantity: int, 
                                       price: float, total_amount: float, order_id: str):
        """儲存失敗的通知到資料庫"""
        try:
            # 從 telegram_id 獲取使用者 ID
            user = await self.db[Collections.USERS].find_one({"telegram_id": user_telegram_id})
            if not user:
                logger.warning(f"找不到 telegram_id {user_telegram_id} 對應的使用者")
                return
            
            action_text = "買入" if action == "buy" else "賣出"
            title = f"🔔 {action_text}交易通知"
            message = f"您的 SITC {action_text}交易已完成！\n• 訂單號碼：{order_id}\n• 數量：{quantity}\n• 價格：{price:.2f}\n• 總金額：{total_amount:.2f}"
            
            await get_pending_notification_service().add_notification(
                user_id=user["_id"],
                notification_type="trade",
                title=title,
                message=message,
                data={
                    "action": action,
                    "quantity": quantity,
                    "price": price,
                    "total_amount": total_amount,
                    "order_id": order_id,
                    "telegram_id": user_telegram_id
                }
            )
            
            logger.info(f"已儲存失敗的 {action} 交易通知給使用者 {user['_id']}")
            
        except Exception as e:
            logger.error(f"儲存失敗通知時發生錯誤: {e}")
    
    async def send_transfer_notification(self, user_id: str, transfer_type: str, amount: float, 
                                       other_user_name: str, transfer_id: str = None):
        """發送轉帳通知"""
        try:
            if not config.external_services.telegram_bot_api_url or not config.security.internal_api_key:
                logger.warning("Telegram Bot API 設定不完整，跳過轉帳通知傳送")
                return
            
            # 獲取使用者的 Telegram ID
            user = await self.db[Collections.USERS].find_one({"_id": user_id})
            if not user or not user.get("telegram_id"):
                logger.warning(f"無法傳送轉帳通知：使用者 {user_id} 未設定 telegram_id")
                return
            
            # 構建轉帳通知
            notification_url = f"{config.external_services.telegram_bot_api_url.rstrip('/')}/bot/notification/transfer"
            
            payload = {
                "user_id": user["telegram_id"],
                "transfer_type": transfer_type,
                "amount": amount,
                "other_user": other_user_name,
                "transfer_id": transfer_id
            }
            
            headers = {
                "Content-Type": "application/json",
                "token": config.security.internal_api_key
            }
            
            response = requests.post(
                notification_url,
                json=payload,
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"成功傳送轉帳通知給使用者 {user['telegram_id']}")
            else:
                logger.warning(f"傳送轉帳通知失敗: HTTP {response.status_code} - {response.text}")
                await self._store_failed_transfer_notification(user_id, transfer_type, amount, other_user_name, transfer_id)
                
        except requests.exceptions.Timeout:
            logger.warning(f"傳送轉帳通知超時，使用者: {user_id}")
            await self._store_failed_transfer_notification(user_id, transfer_type, amount, other_user_name, transfer_id)
        except requests.exceptions.RequestException as e:
            logger.warning(f"傳送轉帳通知網路錯誤: {e}")
            await self._store_failed_transfer_notification(user_id, transfer_type, amount, other_user_name, transfer_id)
        except Exception as e:
            logger.error(f"傳送轉帳通知發生錯誤: {e}")
            await self._store_failed_transfer_notification(user_id, transfer_type, amount, other_user_name, transfer_id)
    
    async def _store_failed_transfer_notification(self, user_id: str, transfer_type: str, amount: float, 
                                                other_user_name: str, transfer_id: str = None):
        """儲存失敗的轉帳通知到資料庫"""
        try:
            transfer_text = "收到" if transfer_type == "received" else "發送"
            title = f"💰 轉帳通知"
            message = f"您{transfer_text}了一筆轉帳！\n• 金額：{amount:.2f}\n• 對方：{other_user_name}"
            if transfer_id:
                message += f"\n• 轉帳ID：{transfer_id}"
            
            await get_pending_notification_service().add_notification(
                user_id=user_id,
                notification_type="transfer",
                title=title,
                message=message,
                data={
                    "transfer_type": transfer_type,
                    "amount": amount,
                    "other_user": other_user_name,
                    "transfer_id": transfer_id
                }
            )
            
            logger.info(f"已儲存失敗的轉帳通知給使用者 {user_id}")
            
        except Exception as e:
            logger.error(f"儲存失敗轉帳通知時發生錯誤: {e}")