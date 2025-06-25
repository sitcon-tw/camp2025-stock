import logging

from api.auth import verify_backend_token
from bot.instance import bot
from bot.services.notification_sender import NotificationSender
from fastapi import APIRouter, HTTPException

from api.schemas.notifications import DMRequest, BulkDMRequest, NotificationRequest, TradeNotificationRequest, \
    TransferNotificationRequest, SystemNotificationRequest

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/dm/send")
async def send_dm(request: DMRequest, ):
    """
    傳送私人訊息給指定使用者
    """
    try:
        notification_sender = NotificationSender(bot)
        success = await notification_sender.send_dm(
            user_id=request.user_id,
            message=request.message,
            parse_mode=request.parse_mode
        )

        if success:
            return {"status": "success", "message": "DM sent successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to send DM")

    except Exception as e:
        logger.error(f"Error sending DM: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/dm/bulk")
async def send_bulk_dm(request: BulkDMRequest, ):
    """
    批量傳送私人訊息給多個使用者
    """
    try:
        notification_sender = NotificationSender(bot)
        result = await notification_sender.send_bulk_dm(
            user_ids=request.user_ids,
            message=request.message,
            parse_mode=request.parse_mode,
            delay_seconds=request.delay_seconds
        )

        return {
            "status": "completed",
            "total_users": len(request.user_ids),
            "success_count": len(result["success"]),
            "failed_count": len(result["failed"]),
            "success_users": result["success"],
            "failed_users": result["failed"]
        }

    except Exception as e:
        logger.error(f"Error sending bulk DM: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/notification/send")
async def send_notification(request: NotificationRequest, ):
    """
    傳送格式化的通知訊息
    """
    try:
        notification_sender = NotificationSender(bot)
        success = await notification_sender.send_notification(
            user_id=request.user_id,
            notification_type=request.notification_type,
            title=request.title,
            content=request.content,
            additional_data=request.additional_data
        )

        if success:
            return {"status": "success", "message": "Notification sent successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to send notification")

    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/notification/trade")
async def send_trade_notification(request: TradeNotificationRequest, ):
    """
    傳送交易通知
    """
    try:
        notification_sender = NotificationSender(bot)
        success = await notification_sender.send_trade_notification(
            user_id=request.user_id,
            action=request.action,
            stock_symbol=request.stock_symbol,
            quantity=request.quantity,
            price=request.price,
            total_amount=request.total_amount,
            order_id=request.order_id
        )

        if success:
            return {"status": "success", "message": "Trade notification sent successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to send trade notification")

    except Exception as e:
        logger.error(f"Error sending trade notification: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/notification/transfer")
async def send_transfer_notification(request: TransferNotificationRequest, ):
    """
    傳送轉帳通知
    """
    try:
        notification_sender = NotificationSender(bot)
        success = await notification_sender.send_transfer_notification(
            user_id=request.user_id,
            transfer_type=request.transfer_type,
            amount=request.amount,
            other_user=request.other_user,
            transfer_id=request.transfer_id
        )

        if success:
            return {"status": "success", "message": "Transfer notification sent successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to send transfer notification")

    except Exception as e:
        logger.error(f"Error sending transfer notification: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/notification/system")
async def send_system_notification(request: SystemNotificationRequest, ):
    """
    傳送系統通知
    """
    try:
        notification_sender = NotificationSender(bot)
        success = await notification_sender.send_system_notification(
            user_id=request.user_id,
            title=request.title,
            content=request.content,
            priority=request.priority
        )

        if success:
            return {"status": "success", "message": "System notification sent successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to send system notification")

    except Exception as e:
        logger.error(f"Error sending system notification: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def health_check():
    """
    健康檢查端點
    """
    return {"status": "healthy", "service": "notification_service"}
