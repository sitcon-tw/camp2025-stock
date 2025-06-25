import logging

from fastapi import APIRouter, HTTPException, Depends
from telegram.constants import ParseMode
from telegram.error import TelegramError

from api.depends.auth import verify_backend_token
from api.schemas.notifications import DMRequest, BulkDMRequest, NotificationRequest, TradeNotificationRequest, \
    TransferNotificationRequest, SystemNotificationRequest
from bot.instance import bot

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/bot/direct/send")
async def send_dm(request: DMRequest, token: str = Depends(verify_backend_token)):
    try:
        await bot.bot.send_message(chat_id=request.user_id, text=request.message, parse_mode=request.parse_mode)
    except TelegramError as e:
        logger.error(f"Telegram error when sending direct to {request.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Telegram server error")
    except Exception as e:
        logger.error(f"Unexpected error when sending direct to {request.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return {"ok": True}


@router.post("/bot/direct/bulk")
async def send_bulk_dm(request: BulkDMRequest, token: str = Depends(verify_backend_token)):
    """
    批量傳送私人訊息給多個使用者
    """
    sent_users = []
    failed_users = []

    # TODO: delay_seconds is discarded right now cuz library should have a feature to work around this
    for user_id in request.user_ids:
        try:
            await bot.bot.send_message(chat_id=user_id, text=request.message, parse_mode=request.parse_mode)
        except TelegramError as e:
            logger.error(f"Telegram error when sending bulk direct to {user_id}: {e}")
            failed_users.append(user_id)
            continue
        except Exception as e:
            logger.error(f"Unexpected error when sending bulk direct to {user_id}: {e}")
            failed_users.append(user_id)
            continue
        sent_users.append(user_id)

    return {
        "ok": True,
        "total_users": len(request.user_ids),
        "success_count": len(sent_users),
        "failed_count": len(failed_users),
        "success_users": sent_users,
        "failed_users": failed_users
    }


# Do we really need this endpoint?
# Uncomment if you really need this
#
# @router.post("/bot/notification/send")
# async def send_notification(request: NotificationRequest, token: str = Depends(verify_backend_token)):
#     """
#     傳送格式化的通知訊息
#     """
#     message_parts = [
#         f"🔔 *{request.title}*",
#         f"",
#         f"{request.content}",
#         f"",
#         f"📅 時間: `{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}`",
#         f"🏷️ 類型: `{request.notification_type}`"
#     ]
#
#     if request.additional_data:
#         message_parts.append("")
#         message_parts.append("📋 *詳細資訊:*")
#         for key, value in request.additional_data.items():
#             message_parts.append(f"• {key}: `{value}`")
#
#     message = "\n".join(message_parts)
#
#     try:
#         await bot.bot.send_message(chat_id=request.user_id, text=message, parse_mode=ParseMode.MARKDOWN_V2)
#     except TelegramError as e:
#         logger.error(f"Telegram error when sending notification to {request.user_id}: {e}")
#         raise HTTPException(status_code=500, detail="Telegram server error")
#     except Exception as e:
#         logger.error(f"Unexpected error when sending notification to {request.user_id}: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/bot/notification/trade")
async def send_trade_notification(request: TradeNotificationRequest, token: str = Depends(verify_backend_token)):
    """
    傳送交易通知
    """
    message_parts = [
        f"🔔 *您的 SITC {"買入" if request.action == "buy" else "賣出"}交易已完成！*",
        f"",
        *([f"• 訂單號碼：`{request.order_id}`"] if request.order_id else []),
        f"• 數量：{request.quantity}",
        f"• 價格：{request.price:.2f}",
        f"• 總金額：{request.total_amount:.2f}"
    ]

    try:
        await bot.bot.send_message(chat_id=request.user_id, text="\n".join(message_parts), parse_mode=ParseMode.MARKDOWN_V2)
    except TelegramError as e:
        logger.error(f"Telegram error when sending trade notification: {e}")
        raise HTTPException(status_code=500, detail="Telegram server error")
    except Exception as e:
        logger.error(f"Unexpected error when sending trade notification: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/bot/notification/transfer")
async def send_transfer_notification(request: TransferNotificationRequest, token: str = Depends(verify_backend_token)):
    """
    傳送轉帳通知
    """
    message_parts = [
        f"🔔 *成功{f"轉帳至 {request.other_user}" if request.transfer_type == "sent" else f"接受來自 {request.other_user} 的轉帳"}！*",
        f"",
        *([f"• 交易號碼：`{request.transfer_id}`"] if request.transfer_id else []),
        f"• 轉帳總金額：{request.total_amount:.2f}"
    ]

    try:
        await bot.bot.send_message(chat_id=request.user_id, text="\n".join(message_parts), parse_mode=ParseMode.MARKDOWN_V2)
    except TelegramError as e:
        logger.error(f"Telegram error when sending transfer notification: {e}")
        raise HTTPException(status_code=500, detail="Telegram server error")
    except Exception as e:
        logger.error(f"Unexpected error when sending transfer notification: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/bot/notification/system")
async def send_system_notification(request: SystemNotificationRequest, token: str = Depends(verify_backend_token)):
    """
    傳送系統通知
    """
    priority_emojis = {
        "low": "ℹ️",
        "normal": "📢",
        "high": "⚠️",
        "urgent": "🚨"
    }
    emoji = priority_emojis.get(request.priority, "ℹ️")

    message_parts = [
        f"{emoji} *{request.title}*",
        f"",
        request.content
    ]

    try:
        await bot.bot.send_message(chat_id=request.user_id, text="\n".join(message_parts), parse_mode=ParseMode.MARKDOWN_V2)
    except TelegramError as e:
        logger.error(f"Telegram error when sending transfer notification: {e}")
        raise HTTPException(status_code=500, detail="Telegram server error")
    except Exception as e:
        logger.error(f"Unexpected error when sending transfer notification: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
