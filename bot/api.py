from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from telegram import Update
from contextlib import asynccontextmanager
from bot import bot, initialize
from utils.logger import setup_logger
from ipaddress import ip_address, ip_network

logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Server started.")
    await initialize()
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
    forward_for_header = request.headers.get("X-Forwarded-For")

    if forward_for_header:
        forward_for_header = forward_for_header.split(",")[0].strip()
    else:
        forward_for_header = request.client.host

    logger.info(f"Forwarded header: {forward_for_header}")

    if (ip_address(forward_for_header) not in ip_network("149.154.160.0/20")) and (ip_address(forward_for_header) not in ip_network("91.108.4.0/22")):
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

@app.post("/bot/broadcast/all")
async def broadcast_all(request: Request):
    logger.info("[FastAPI] Broadcast endpoint hit.")
    return {"message": "Broadcast not implemented yet 😾"}

@app.get("/healthz")
async def healthz():
    try:
        await bot.bot.get_me()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"ok": True}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"ok": False}
        )
