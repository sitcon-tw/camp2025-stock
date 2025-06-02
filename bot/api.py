from os import environ
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from telegram import Update
from telegram.constants import ParseMode
from contextlib import asynccontextmanager
from bot import bot, initialize
from utils.logger import setup_logger
from ipaddress import ip_address, ip_network
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List

load_dotenv()
BROADCAST_CHANNELS = environ.get("BROADCAST_CHANNELS").split(",")
WEBHOOK_SECRET = environ.get("WEBHOOK_SECRET")

logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Server started.")
    await initialize()
    if not WEBHOOK_SECRET:
        logger.warning("WEBHOOK_SECRET was not set!")
    yield
    logger.info("Server stopped.")

app = FastAPI(lifespan=lifespan)

@app.get("/bot/webhook", status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
async def webhook_get(request: Request):
    return JSONResponse(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        content={"ok": False, "message": "Method not allowed."}
    )

@app.post("/bot/webhook")
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
        return JSONResponse(
            content={"ok": True, "message": "success"}
        )
    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"ok": False, "message": "Error processing update."}
        )

class Broadcast(BaseModel):
    title: str
    message: str

class BroadcastSelective(Broadcast):
    channel: List[int]

@app.post("/bot/broadcast/")
async def broadcast(request: BroadcastSelective):
    logger.info("[FastAPI] Selective broadcast endpoint hit.")
    for channel in request.channel:
        try:
            await bot.bot.send_message(channel, f"""
            📢 *{request.title}*
            
            {request.message}
            """, parse_mode=ParseMode.MARKDOWN_V2)
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")
    return {"ok": True}

@app.post("/bot/broadcast/all")
async def broadcast_all(request: Broadcast):
    logger.info("[FastAPI] Broadcast endpoint hit.")
    for channel in BROADCAST_CHANNELS:
        try:
            await bot.bot.send_message(channel, f"""
            📢 *{request.title}*
            
            {request.message}
            """, parse_mode=ParseMode.MARKDOWN_V2)
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")
    return {"ok": True}

@app.get("/healthz")
async def healthz():
    try:
        await bot.bot.get_me()
        logger.info("Healthz endpoint checked successfully.")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"ok": True}
        )
    except Exception as e:
        logger.error(f"Error checking healthz: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"ok": False}
        )
