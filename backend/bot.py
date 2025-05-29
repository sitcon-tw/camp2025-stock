from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from dotenv import load_dotenv
import os
from fastapi import FastAPI, Request, status
from contextlib import asynccontextmanager

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBOOK_SECRET = os.getenv("WEBOOK_SECRET")

bot = ApplicationBuilder().token(BOT_TOKEN).build()

print("[main] Bot initialized.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[FastAPI] Server started.")
    yield
    print("[FastAPI] Server stopped.")

app = FastAPI(lifespan=lifespan)

@app.get("/bot/webhook", status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
async def webhook_get(request: Request):
    return {"success": False, "message": "Method not allowed."}

@app.post("/bot/webhook")
async def webhook_post(request: Request):
    update = Update.de_json(await request.json())
    await bot.process_update(update)
    print("[FastAPI] Server received update.")

    return {"success": True, "message": "success"}

@app.post("/bot/broadcast/all")
async def broadcast_all(request: Request):


# Telegram command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Hello {update.effective_user.username}, hello there!")

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Hello {update.effective_user.username}, your key is {context.args[0]}, hello there!")

bot.add_handler(CommandHandler("start", start))
bot.add_handler(CommandHandler("register", register))
