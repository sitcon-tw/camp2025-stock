from os import environ
from typing import Annotated

from fastapi import APIRouter, status, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from telegram.constants import ParseMode

from bot.instance import bot
from utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)
BROADCAST_CHANNELS = environ.get("BROADCAST_CHANNELS").split(",")
BACKEND_TOKEN = environ.get("BACKEND_TOKEN")

class Broadcast(BaseModel):
    title: str
    message: str

@router.post("/bot/broadcast/")
async def broadcast(request: Broadcast, token: Annotated[str | None, Header()] = None):
    if not token:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={
            "ok": False,
            "message": "token is not provided"
        })

    if not token == BACKEND_TOKEN:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={
            "ok": False,
            "message": "token is incorrect :D"
        })

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