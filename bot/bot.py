from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import os
from dotenv import load_dotenv
from utils.logger import setup_logger

logger = setup_logger(__name__)

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logger.info("Bot token: %s", BOT_TOKEN)

bot = ApplicationBuilder().token(BOT_TOKEN).build()
logger.info("Bot initialized.")

# Telegram command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username
    logger.info(f"[bot] /start triggered by {username}")
    await update.message.reply_text(f"Hello {username}, hello there!")

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username
    if not context.args:
        logger.warning(f"[bot] /register called without args by {username}")
        await update.message.reply_text("You forgot to provide a key, dummy 😾")
        return
    key = context.args[0]
    logger.info(f"[bot] /register triggered by {username}, key: {key}")
    await update.message.reply_text(f"Hello {username}, your key is {key}, hello there!")

bot.add_handler(CommandHandler("start", start))
bot.add_handler(CommandHandler("register", register))

__all__ = ["bot"]
