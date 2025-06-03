from telegram.ext import ApplicationBuilder
from os import getenv
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = getenv("TELEGRAM_BOT_TOKEN")

bot = ApplicationBuilder().token(BOT_TOKEN).build()
