"""
Notification Service Implementations
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import logging
from enum import Enum

from ...application.common.interfaces import NotificationService
from ...domain.common.exceptions import BusinessRuleException

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """通知渠道"""
    TELEGRAM = "telegram"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBSOCKET = "websocket"
    WEBHOOK = "webhook"


class NotificationType(Enum):
    """通知類型"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    URGENT = "urgent"


class NotificationMessage:
    """通知消息"""
    
    def __init__(
        self,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        channel: NotificationChannel = NotificationChannel.TELEGRAM,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.notification_type = notification_type
        self.channel = channel
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.message_id = self._generate_message_id()
    
    def _generate_message_id(self) -> str:
        """生成消息ID"""
        from bson import ObjectId
        return str(ObjectId())
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "message_id": self.message_id,
            "message": self.message,
            "notification_type": self.notification_type.value,
            "channel": self.channel.value,
            "metadata": self.metadata,
            "created_at": self.created_at
        }


class NotificationProvider(ABC):
    """通知提供者接口"""
    
    @abstractmethod
    async def send_notification(self, user_id: str, message: NotificationMessage) -> bool:
        """發送通知"""
        pass
    
    @abstractmethod
    async def send_bulk_notification(self, user_ids: List[str], message: NotificationMessage) -> Dict[str, bool]:
        """批量發送通知"""
        pass
    
    @abstractmethod
    def get_channel(self) -> NotificationChannel:
        """獲取通知渠道"""
        pass


class TelegramNotificationProvider(NotificationProvider):
    """Telegram 通知提供者"""
    
    def __init__(self, bot_token: str, base_url: str = "https://api.telegram.org/bot"):
        self.bot_token = bot_token
        self.base_url = base_url
        self.session = None
    
    async def _get_session(self):
        """獲取 HTTP 會話"""
        if not self.session:
            import aiohttp
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def send_notification(self, user_id: str, message: NotificationMessage) -> bool:
        """發送 Telegram 通知"""
        try:
            # 這裡需要將 user_id 轉換為 telegram_id
            telegram_id = await self._get_telegram_id(user_id)
            if not telegram_id:
                logger.warning(f"No telegram ID found for user {user_id}")
                return False
            
            session = await self._get_session()
            url = f"{self.base_url}{self.bot_token}/sendMessage"
            
            # 格式化消息
            formatted_message = self._format_message(message)
            
            data = {
                "chat_id": telegram_id,
                "text": formatted_message,
                "parse_mode": "HTML"
            }
            
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    logger.info(f"Telegram notification sent to user {user_id}")
                    return True
                else:
                    logger.error(f"Failed to send Telegram notification: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")
            return False
    
    async def send_bulk_notification(self, user_ids: List[str], message: NotificationMessage) -> Dict[str, bool]:
        """批量發送 Telegram 通知"""
        results = {}
        
        # 並行發送通知
        tasks = []
        for user_id in user_ids:
            task = asyncio.create_task(self.send_notification(user_id, message))
            tasks.append((user_id, task))
        
        # 等待所有任務完成
        for user_id, task in tasks:
            try:
                result = await task
                results[user_id] = result
            except Exception as e:
                logger.error(f"Error in bulk notification for user {user_id}: {e}")
                results[user_id] = False
        
        return results
    
    def get_channel(self) -> NotificationChannel:
        """獲取通知渠道"""
        return NotificationChannel.TELEGRAM
    
    def _format_message(self, message: NotificationMessage) -> str:
        """格式化消息"""
        type_emoji = {
            NotificationType.INFO: "ℹ️",
            NotificationType.WARNING: "⚠️",
            NotificationType.ERROR: "❌",
            NotificationType.SUCCESS: "✅",
            NotificationType.URGENT: "🚨"
        }
        
        emoji = type_emoji.get(message.notification_type, "ℹ️")
        return f"{emoji} {message.message}"
    
    async def _get_telegram_id(self, user_id: str) -> Optional[int]:
        """獲取用戶的 Telegram ID"""
        # 這裡需要從數據庫獲取用戶的 Telegram ID
        # 暫時返回 None，實際實現需要查詢數據庫
        return None
    
    async def close(self):
        """關閉會話"""
        if self.session:
            await self.session.close()


class EmailNotificationProvider(NotificationProvider):
    """電子郵件通知提供者"""
    
    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    async def send_notification(self, user_id: str, message: NotificationMessage) -> bool:
        """發送電子郵件通知"""
        try:
            # 獲取用戶郵箱
            email_address = await self._get_user_email(user_id)
            if not email_address:
                logger.warning(f"No email address found for user {user_id}")
                return False
            
            # 發送郵件
            return await self._send_email(email_address, message)
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False
    
    async def send_bulk_notification(self, user_ids: List[str], message: NotificationMessage) -> Dict[str, bool]:
        """批量發送電子郵件通知"""
        results = {}
        
        # 並行發送郵件
        tasks = []
        for user_id in user_ids:
            task = asyncio.create_task(self.send_notification(user_id, message))
            tasks.append((user_id, task))
        
        for user_id, task in tasks:
            try:
                result = await task
                results[user_id] = result
            except Exception as e:
                logger.error(f"Error in bulk email notification for user {user_id}: {e}")
                results[user_id] = False
        
        return results
    
    def get_channel(self) -> NotificationChannel:
        """獲取通知渠道"""
        return NotificationChannel.EMAIL
    
    async def _send_email(self, email_address: str, message: NotificationMessage) -> bool:
        """發送郵件"""
        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # 創建郵件
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = email_address
            msg['Subject'] = self._get_email_subject(message)
            
            # 郵件內容
            body = self._format_email_body(message)
            msg.attach(MIMEText(body, 'html'))
            
            # 發送郵件
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.username,
                password=self.password,
                use_tls=True
            )
            
            logger.info(f"Email sent to {email_address}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {email_address}: {e}")
            return False
    
    def _get_email_subject(self, message: NotificationMessage) -> str:
        """獲取郵件主題"""
        type_map = {
            NotificationType.INFO: "通知",
            NotificationType.WARNING: "警告",
            NotificationType.ERROR: "錯誤",
            NotificationType.SUCCESS: "成功",
            NotificationType.URGENT: "緊急通知"
        }
        
        prefix = type_map.get(message.notification_type, "通知")
        return f"[SITCON Camp 2025] {prefix}"
    
    def _format_email_body(self, message: NotificationMessage) -> str:
        """格式化郵件內容"""
        return f"""
        <html>
        <body>
            <h2>SITCON Camp 2025 點數系統通知</h2>
            <p>{message.message}</p>
            <hr>
            <p><small>發送時間: {message.created_at.strftime('%Y-%m-%d %H:%M:%S')}</small></p>
        </body>
        </html>
        """
    
    async def _get_user_email(self, user_id: str) -> Optional[str]:
        """獲取用戶郵箱"""
        # 這裡需要從數據庫獲取用戶郵箱
        # 暫時返回 None，實際實現需要查詢數據庫
        return None


class WebSocketNotificationProvider(NotificationProvider):
    """WebSocket 通知提供者"""
    
    def __init__(self):
        self.connections: Dict[str, Any] = {}
    
    async def send_notification(self, user_id: str, message: NotificationMessage) -> bool:
        """發送 WebSocket 通知"""
        try:
            if user_id not in self.connections:
                logger.warning(f"No WebSocket connection found for user {user_id}")
                return False
            
            connection = self.connections[user_id]
            
            # 格式化消息
            formatted_message = {
                "type": "notification",
                "data": message.to_dict()
            }
            
            # 發送消息
            await connection.send_json(formatted_message)
            logger.info(f"WebSocket notification sent to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending WebSocket notification: {e}")
            return False
    
    async def send_bulk_notification(self, user_ids: List[str], message: NotificationMessage) -> Dict[str, bool]:
        """批量發送 WebSocket 通知"""
        results = {}
        
        for user_id in user_ids:
            result = await self.send_notification(user_id, message)
            results[user_id] = result
        
        return results
    
    def get_channel(self) -> NotificationChannel:
        """獲取通知渠道"""
        return NotificationChannel.WEBSOCKET
    
    def add_connection(self, user_id: str, connection: Any):
        """添加連接"""
        self.connections[user_id] = connection
        logger.info(f"WebSocket connection added for user {user_id}")
    
    def remove_connection(self, user_id: str):
        """移除連接"""
        if user_id in self.connections:
            del self.connections[user_id]
            logger.info(f"WebSocket connection removed for user {user_id}")


class CompositeNotificationService(NotificationService):
    """複合通知服務"""
    
    def __init__(self):
        self.providers: Dict[NotificationChannel, NotificationProvider] = {}
        self.default_channels = [NotificationChannel.TELEGRAM]
    
    def add_provider(self, provider: NotificationProvider):
        """添加通知提供者"""
        self.providers[provider.get_channel()] = provider
    
    def set_default_channels(self, channels: List[NotificationChannel]):
        """設置默認通知渠道"""
        self.default_channels = channels
    
    async def send_notification(self, user_id: str, message: str, type: str = "info") -> None:
        """發送通知"""
        try:
            notification_type = NotificationType(type)
        except ValueError:
            notification_type = NotificationType.INFO
        
        # 創建通知消息
        notification_message = NotificationMessage(
            message=message,
            notification_type=notification_type
        )
        
        # 通過所有默認渠道發送
        for channel in self.default_channels:
            if channel in self.providers:
                provider = self.providers[channel]
                try:
                    await provider.send_notification(user_id, notification_message)
                except Exception as e:
                    logger.error(f"Error sending notification via {channel.value}: {e}")
    
    async def send_bulk_notification(self, user_ids: List[str], message: str, type: str = "info") -> None:
        """批量發送通知"""
        try:
            notification_type = NotificationType(type)
        except ValueError:
            notification_type = NotificationType.INFO
        
        # 創建通知消息
        notification_message = NotificationMessage(
            message=message,
            notification_type=notification_type
        )
        
        # 通過所有默認渠道發送
        for channel in self.default_channels:
            if channel in self.providers:
                provider = self.providers[channel]
                try:
                    await provider.send_bulk_notification(user_ids, notification_message)
                except Exception as e:
                    logger.error(f"Error sending bulk notification via {channel.value}: {e}")
    
    async def send_notification_via_channel(
        self, 
        user_id: str, 
        message: str, 
        channel: NotificationChannel,
        type: str = "info"
    ) -> bool:
        """通過指定渠道發送通知"""
        if channel not in self.providers:
            logger.warning(f"No provider found for channel {channel.value}")
            return False
        
        try:
            notification_type = NotificationType(type)
        except ValueError:
            notification_type = NotificationType.INFO
        
        notification_message = NotificationMessage(
            message=message,
            notification_type=notification_type,
            channel=channel
        )
        
        provider = self.providers[channel]
        return await provider.send_notification(user_id, notification_message)
    
    async def send_urgent_notification(self, user_id: str, message: str) -> None:
        """發送緊急通知（通過所有可用渠道）"""
        notification_message = NotificationMessage(
            message=message,
            notification_type=NotificationType.URGENT
        )
        
        # 通過所有可用渠道發送
        for channel, provider in self.providers.items():
            try:
                await provider.send_notification(user_id, notification_message)
            except Exception as e:
                logger.error(f"Error sending urgent notification via {channel.value}: {e}")
    
    async def cleanup(self):
        """清理資源"""
        for provider in self.providers.values():
            if hasattr(provider, 'close'):
                await provider.close()


# 工廠函數
def create_notification_service(config: Dict[str, Any]) -> CompositeNotificationService:
    """創建通知服務"""
    service = CompositeNotificationService()
    
    # 添加 Telegram 提供者
    if config.get('telegram', {}).get('enabled', False):
        telegram_config = config['telegram']
        provider = TelegramNotificationProvider(
            bot_token=telegram_config['bot_token']
        )
        service.add_provider(provider)
    
    # 添加 Email 提供者
    if config.get('email', {}).get('enabled', False):
        email_config = config['email']
        provider = EmailNotificationProvider(
            smtp_host=email_config['smtp_host'],
            smtp_port=email_config['smtp_port'],
            username=email_config['username'],
            password=email_config['password']
        )
        service.add_provider(provider)
    
    # 添加 WebSocket 提供者
    if config.get('websocket', {}).get('enabled', False):
        provider = WebSocketNotificationProvider()
        service.add_provider(provider)
    
    # 設置默認渠道
    default_channels = []
    for channel_name in config.get('default_channels', ['telegram']):
        try:
            channel = NotificationChannel(channel_name)
            default_channels.append(channel)
        except ValueError:
            logger.warning(f"Invalid notification channel: {channel_name}")
    
    service.set_default_channels(default_channels)
    
    return service