import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

# MongoDB setup
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["my_bot_db"]
users_collection = db["users"]

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

# Main
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("whoami", whoami))

    print("Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
