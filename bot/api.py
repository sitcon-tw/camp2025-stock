from fastapi import FastAPI, Request, status
from telegram import Update
from contextlib import asynccontextmanager
from bot import bot
from utils.logger import setup_logger

logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Server started.")
    yield
    logger.info("Server stopped.")

app = FastAPI(lifespan=lifespan)

@app.get("/bot/webhook", status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
async def webhook_get(request: Request):
    return {"ok": False, "message": "Method not allowed."}

@app.post("/bot/webhook")
async def webhook_post(request: Request):
    try:
        update_data = await request.json()
        update = Update.de_json(update_data)
        await bot.process_update(update)
        logger.info("[FastAPI] Received and processed Telegram update.")
        return {"ok": True, "message": "success"}
    except Exception as e:
        logger.error(f"[FastAPI] Error processing update: {e}")
        return {"ok": False, "message": "Error processing update."}

@app.post("/bot/broadcast/all")
async def broadcast_all(request: Request):
    logger.info("[FastAPI] Broadcast endpoint hit.")
    return {"message": "Broadcast not implemented yet 😾"}
