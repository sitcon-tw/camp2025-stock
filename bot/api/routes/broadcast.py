from os import environ

from fastapi import APIRouter, status, Depends
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode

from api.depends.auth import verify_backend_token
from api.schemas.broadcast import Broadcast
from bot.instance import bot
from utils.logger import setup_logger
from bot.helper.chat_ids import STUDENT_GROUPS, MAIN_GROUP

router = APIRouter()
logger = setup_logger(__name__)
BACKEND_TOKEN = environ.get("BACKEND_TOKEN")


@router.post("/bot/broadcast/")
async def broadcast(request: Broadcast, token: str = Depends(verify_backend_token)):
    logger.info("[FastAPI] Selective broadcast endpoint hit.")
    logger.info(f"Request title: {request.title}")
    logger.info(f"Request message: {request.message}")
    logger.info(f"Token verified: {token[:10]}..." if token else "No token")
    
    groups = list(STUDENT_GROUPS.values())
    groups.append(MAIN_GROUP)
    logger.info(f"Broadcasting to {len(groups)} groups: {groups}")

    successful_sends = 0
    failed_sends = 0

    for channel in groups:
        try:
            # 先嘗試發送簡單的文本消息，避免 Markdown 解析問題
            message_text = f"📢 {request.title}\n\n{request.message}"
            logger.info(f"Sending message to channel {channel}: {message_text[:50]}...")
            
            # 檢查 bot 實例是否可用
            if not bot.bot:
                logger.error("Bot instance is not available")
                failed_sends += 1
                continue
                
            await bot.bot.send_message(
                channel,  # 直接使用 channel ID，不要添加 '-'
                message_text
            )
            logger.info(f"Message successfully sent to channel {channel}")
            successful_sends += 1
        except Exception as e:
            logger.error(f"Error broadcasting message to channel {channel}: {e}")
            logger.error(f"Exception type: {type(e)}")
            failed_sends += 1
            # 嘗試發送不帶格式的消息
            try:
                simple_message = f"📢 {request.title}\n\n{request.message}"
                await bot.bot.send_message(channel, simple_message)
                logger.info(f"Fallback message sent to channel {channel}")
                successful_sends += 1
                failed_sends -= 1  # 修正計數
            except Exception as fallback_e:
                logger.error(f"Fallback message also failed for channel {channel}: {fallback_e}")
                logger.error(f"Fallback exception type: {type(fallback_e)}")
    
    logger.info(f"Broadcast completed: {successful_sends} successful, {failed_sends} failed")
    return {"ok": True, "successful_sends": successful_sends, "failed_sends": failed_sends}
