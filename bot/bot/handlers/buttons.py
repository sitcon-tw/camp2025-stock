from telegram import Update
from telegram.ext import ContextTypes

async def handle_zombie_clicks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("⚠️ 此按鈕無效，請重新輸入 /stock 開始新的操作", show_alert=True)
