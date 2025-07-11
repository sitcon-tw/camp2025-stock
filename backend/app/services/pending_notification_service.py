from datetime import datetime
from typing import List, Optional, Dict, Any
from app.core.database import get_database, Collections
from app.core.config_refactored import config
import logging

logger = logging.getLogger(__name__)


class PendingNotificationService:
    """管理待發送通知的服務"""
    
    def __init__(self):
        self.database = get_database()
        self.collection = self.database[Collections.PENDING_NOTIFICATIONS]
    
    async def add_notification(
        self,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> str:
        """新增待發送通知"""
        try:
            notification_doc = {
                "user_id": user_id,
                "notification_type": notification_type,
                "title": title,
                "message": message,
                "data": data or {},
                "created_at": datetime.now(),
                "retry_count": 0
            }
            
            result = await self.collection.insert_one(notification_doc)
            logger.info(f"Added pending notification for user {user_id}: {notification_type}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to add pending notification: {e}")
            raise
    
    async def get_user_notifications(self, user_id: int) -> List[Dict[str, Any]]:
        """取得使用者的待發送通知"""
        try:
            cursor = self.collection.find({"user_id": user_id})
            notifications = []
            
            async for doc in cursor:
                notifications.append({
                    "id": str(doc["_id"]),
                    "notification_type": doc["notification_type"],
                    "title": doc["title"],
                    "message": doc["message"],
                    "data": doc.get("data", {}),
                    "created_at": doc["created_at"].isoformat(),
                    "retry_count": doc.get("retry_count", 0)
                })
            
            return notifications
            
        except Exception as e:
            logger.error(f"Failed to get user notifications: {e}")
            raise
    
    async def mark_notification_sent(self, notification_id: str) -> bool:
        """標記通知已發送並刪除"""
        try:
            from bson import ObjectId
            
            result = await self.collection.delete_one({"_id": ObjectId(notification_id)})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted sent notification: {notification_id}")
                return True
            else:
                logger.warning(f"Notification not found for deletion: {notification_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to mark notification as sent: {e}")
            raise
    
    async def increment_retry_count(self, notification_id: str) -> bool:
        """增加重試次數"""
        try:
            from bson import ObjectId
            
            result = await self.collection.update_one(
                {"_id": ObjectId(notification_id)},
                {"$inc": {"retry_count": 1}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to increment retry count: {e}")
            raise
    
    async def cleanup_old_notifications(self, days_old: int = 7) -> int:
        """清理舊通知"""
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            result = await self.collection.delete_many({
                "created_at": {"$lt": cutoff_date}
            })
            
            logger.info(f"Cleaned up {result.deleted_count} old notifications")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old notifications: {e}")
            raise
    
    async def get_notification_stats(self) -> Dict[str, Any]:
        """取得通知統計"""
        try:
            total_count = await self.collection.count_documents({})
            
            # 按類型統計
            pipeline = [
                {"$group": {"_id": "$notification_type", "count": {"$sum": 1}}}
            ]
            
            type_stats = {}
            async for doc in self.collection.aggregate(pipeline):
                type_stats[doc["_id"]] = doc["count"]
            
            return {
                "total_pending": total_count,
                "by_type": type_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get notification stats: {e}")
            raise


# 全域實例
pending_notification_service = PendingNotificationService()