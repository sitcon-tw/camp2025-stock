from os import environ
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel
from telegram.constants import ParseMode

from bot.instance import bot
from utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)
BROADCAST_CHANNELS = environ.get("BROADCAST_CHANNELS").split(",")

class Broadcast(BaseModel):
    title: str
    message: str

class BroadcastSelective(Broadcast):
    channel: List[int]

@router.post("/bot/broadcast/")
async def broadcast(request: BroadcastSelective):
    logger.info("[FastAPI] Selective broadcast endpoint hit.")
    for channel in BROADCAST_CHANNELS:
        try:
            await bot.bot.send_message(f"-{channel}", f"""
📢 *{request.title}*

{request.message}
""", parse_mode=ParseMode.MARKDOWN_V2)
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")
    return {"ok": True}