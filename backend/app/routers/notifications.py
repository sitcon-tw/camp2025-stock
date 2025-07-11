from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from app.services.pending_notification_service import pending_notification_service
from app.core.rbac import get_current_user_id
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/pending", response_model=List[Dict[str, Any]])
async def get_pending_notifications(
    user_id: int = Depends(get_current_user_id)
) -> List[Dict[str, Any]]:
    """取得使用者的待發送通知"""
    try:
        notifications = await pending_notification_service.get_user_notifications(user_id)
        return notifications
    except Exception as e:
        logger.error(f"Failed to get pending notifications for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pending notifications")


@router.post("/mark-sent/{notification_id}")
async def mark_notification_sent(
    notification_id: str,
    user_id: int = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """標記通知已發送"""
    try:
        success = await pending_notification_service.mark_notification_sent(notification_id)
        
        if success:
            return {"success": True, "message": "Notification marked as sent"}
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark notification as sent: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark notification as sent")


@router.get("/stats")
async def get_notification_stats(
    user_id: int = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """取得通知統計（管理員用）"""
    try:
        stats = await pending_notification_service.get_notification_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get notification stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notification stats")


@router.delete("/cleanup")
async def cleanup_old_notifications(
    days_old: int = 7,
    user_id: int = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """清理舊通知（管理員用）"""
    try:
        deleted_count = await pending_notification_service.cleanup_old_notifications(days_old)
        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Cleaned up {deleted_count} old notifications"
        }
    except Exception as e:
        logger.error(f"Failed to cleanup old notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup old notifications")