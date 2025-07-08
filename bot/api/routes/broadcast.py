from os import environ

from fastapi import APIRouter, status, Depends
from telegram.helpers import escape_markdown

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
    groups = list(STUDENT_GROUPS.values())
    groups.append(MAIN_GROUP)

    for channel in groups:
        try:
            await bot.bot.send_message(
                f"-{channel}",
                f"""📢 *{escape_markdown(request.title)}*"""
                f"""{escape_markdown(request.message)}"""
                f""", parse_mode=ParseMode.MARKDOWN_V2)"""
            )
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")
    return {"ok": True}
