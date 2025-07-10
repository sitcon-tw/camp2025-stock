import asyncio
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from telegram.error import BadRequest
from datetime import datetime, timedelta

from utils import api_helper
from utils.logger import setup_logger
from bot.helper.existing_user import verify_existing_user

logger = setup_logger(__name__)


async def safe_edit_message(query, text, parse_mode=None, reply_markup=None):
    """安全地編輯訊息，處理 'Message is not modified' 警告"""
    try:
        await query.edit_message_text(
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )
    except Exception as e:
        error_msg = str(e)
        if "Message is not modified" in error_msg:
            logger.debug("Message is already up to date, skipping edit")
        else:
            logger.error(f"Failed to edit message: {e}")
            raise


async def handle_zombie_clicks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        callback_data = update.callback_query.data

        context.user_data["in_transfer_convo"] = False
        context.user_data["in_stock_convo"] = False
        await update.callback_query.answer("⚠️ 此按鈕無效，請重新輸入指令來開始新的操作", show_alert=True)
    except BadRequest as e:
        if "too old" in str(e) or "expired" in str(e) or "invalid" in str(e):
            logger.warning(f"Callback query expired or invalid: {e}")
        else:
            logger.error(f"BadRequest in handle_zombie_clicks: {e}")
    except Exception as e:
        logger.error(f"Error in handle_zombie_clicks: {e}")

async def handle_pvp_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.split(":")

    market_status = api_helper.get("/api/status")
    if not market_status.isOpen:
        await update.message.reply_text(
            "🚫 目前交易已經關閉，請稍後再來！",
        )
        return

    if data[1] == "cancel":
        original_user_id = int(data[2])
        if update.effective_user.id != original_user_id:
            await query.answer("❌ 你不能取消別人的 PVP 挑戰！", show_alert=True)
            return

        await query.answer("✅ 已取消 PVP 挑戰", show_alert=True)
        await query.edit_message_text("️⚠️ PVP 挑戰已取消")
        context.chat_data.pop(f"pvp:{original_user_id}", None)
    elif data[1] == "confirm":
        if update.effective_user.id == int(data[2]):
            await query.answer("❌ 不能點自己的 PVP 挑戰！", show_alert=True)
            return

        if not context.chat_data.get(f"pvp:{update.effective_user.id}"):
            await query.answer("⚠️ PVP 挑戰已經失效ㄌ", show_alert=True)
            try:
                await query.edit_message_text("️⚠️ PVP 挑戰已經失效，請重新發起挑戰！")
            except Exception as e:
                logger.error(f"Error in handle_pvp_click, editing stale message: {e}")
            return
        challenge_data = context.chat_data[f"pvp:{update.effective_user.id}"]

        if challenge_data["challenger_id"] != data[3]:
            await query.answer("⚠️ PVP 挑戰已經失效ㄌ", show_alert=True)
            try:
                await query.edit_message_text("️⚠️ PVP 挑戰已經失效，請重新發起挑戰！")
            except Exception as e:
                logger.error(f"Error in handle_pvp_click, editing stale message: {e}")
            return

        did_clicker_win = bool(random.getrandbits(1)) # If true, who clicked the button get the points
        await query.answer("🤑 等下，新版 PVP 還在測試")
        return
        # comment above line to continue dev
        win_text = f"🎉 恭喜 {"點按鈕的人"} 贏了 PVP 挑戰！" if did_clicker_win else f"😿 很遺憾，{"點按鈕的人"} 輸了 PVP 挑戰！"

        await update.effective_message.edit_text(
            f"{win_text}\n🤑 這個挑戰值 {challenge_data['reward']} 點"
        )

        # API calling part here
        # Who started the PVP challenge will be int(data[2])
        # Who clicked the button will be update.effective_user.id
        # amount is in challenge_data['reward']


async def handle_orders_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理訂單清單的分頁按鈕"""
    query = update.callback_query
    await query.answer()
    
    try:
        # 動態導入以避免循環導入
        from bot.handlers.commands import show_orders_page
        
        callback_data = query.data
        user_id = str(query.from_user.id)
        
        if callback_data == "orders_refresh":
            # 重新整理目前頁面 - 預設第1頁
            await show_orders_page(query, user_id, 1, edit_message=True)
        elif callback_data.startswith("orders_page_"):
            # 切換到指定頁面
            try:
                page = int(callback_data.split("_")[-1])
                await show_orders_page(query, user_id, page, edit_message=True)
            except (ValueError, IndexError):
                await query.answer("無效的頁面", show_alert=True)
        else:
            await query.answer("未知的操作", show_alert=True)
            
    except Exception as e:
        await query.answer("操作失敗，請稍後再試", show_alert=True)
