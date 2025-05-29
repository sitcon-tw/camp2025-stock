from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from dotenv import load_dotenv
import os
from fastapi import FastAPI, Request, status
from contextlib import asynccontextmanager

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = ApplicationBuilder().token(BOT_TOKEN).build()

print("[main] Bot initialized.")

app = FastAPI()

@asynccontextmanager
async def lifespan():
    print("[FastAPI] Server started.")
    yield
    print("[FastAPI] Server stopped.")

@app.get("/webhook", status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
async def webhook_get(request: Request):
    return {"success": False, "message": "Method not allowed."}

@app.post("/webhook")
async def webhook_post(request: Request):
    update = Update.de_json(await request.json())
    await bot.process_update(update)
    print("[FastAPI] Server received update.")

    return {"success": True, "message": "success"}

# Telegram command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = {
        "_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "chat_id": update.effective_chat.id,
    }

    existing_user = await users_collection.find_one({"_id": user.id})

    if existing_user:
        await update.message.reply_text(f"Welcome back, {user.first_name}!")
    else:
        await users_collection.insert_one(user_data)
        await update.message.reply_text(f"Hello {user.first_name}, you're now registered!")

async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    record = await users_collection.find_one({"_id": user.id})
    
    if record:
        await update.message.reply_text(f"You are {record['first_name']} (@{record['username']})")
    else:
        await update.message.reply_text("You are not registered yet.")

bot.add_handler(CommandHandler("start", start))
bot.add_handler(CommandHandler("whoami", whoami))