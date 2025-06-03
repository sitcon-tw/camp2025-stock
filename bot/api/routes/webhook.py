from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from os import environ
from telegram import Update
from bot.instance import bot
from utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)
WEBHOOK_SECRET = environ.get("WEBHOOK_SECRET")

@router.get("/bot/webhook", status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
async def webhook_get(request: Request):
    return JSONResponse(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        content={"ok": False, "message": "Method not allowed."}
    )

@router.post("/bot/webhook")
async def webhook_post(request: Request):
    if not request.headers.get("X-Telegram-Bot-Api-Secret-Token") == WEBHOOK_SECRET:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"ok": False, "message": "Forbidden"}
        )
    try:
        update_data = await request.json()
        update = Update.de_json(update_data, bot.bot)
        await bot.process_update(update)
        logger.info("Received and processed Telegram update.")
        return {"ok": True, "message": "success"}
    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"ok": False, "message": "Error processing update."}
        )
