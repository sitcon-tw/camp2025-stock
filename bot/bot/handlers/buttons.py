from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from utils import api_helper
from bot.helper.existing_user import verify_existing_user


async def handle_zombie_clicks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("⚠️ 此按鈕無效，請重新輸入指令來開始新的操作", show_alert=True)


async def handle_pvp_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 PVP 挑戰接受按鈕點擊"""
    query = update.callback_query
    await query.answer()
    
    # 解析 callback_data: pvp_accept_{challenge_id}_{choice}
    try:
        parts = query.data.split('_')
        if len(parts) != 4 or parts[0] != 'pvp' or parts[1] != 'accept':
            await query.edit_message_text("❌ 無效的挑戰！")
            return
            
        challenge_id = parts[2]
        choice = parts[3]
        
        # 調用後端 API 接受挑戰
        response = api_helper.post("/api/bot/pvp/accept", protected_route=True, json={
            "from_user": str(query.from_user.id),
            "challenge_id": challenge_id,
            "choice": choice
        })
        
        if response and isinstance(response, dict):
            if response.get("success"):
                # 遊戲完成，顯示結果
                message_text = escape_markdown(response.get("message"), 2)
                await query.edit_message_text(
                    message_text,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            else:
                # 接受挑戰失敗
                error_message = escape_markdown(response.get("message", "接受挑戰失敗"), 2)
                await query.answer(error_message, show_alert=True)
        else:
            # 用戶不存在或其他 API 錯誤
            if await verify_existing_user(response, update):
                return
            await query.answer("接受挑戰失敗，請稍後再試", show_alert=True)
            
    except Exception as e:
        await query.answer("處理挑戰時發生錯誤", show_alert=True)
