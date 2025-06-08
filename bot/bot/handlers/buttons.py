from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from utils import api_helper
from bot.helper.existing_user import verify_existing_user


async def handle_zombie_clicks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("⚠️ 此按鈕無效，請重新輸入指令來開始新的操作", show_alert=True)


async def handle_pvp_creator_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 PVP 發起人選擇猜拳"""
    query = update.callback_query
    await query.answer()
    
    # 解析 callback_data: pvp_creator_{challenge_id}_{choice}
    try:
        parts = query.data.split('_')
        if len(parts) != 4 or parts[0] != 'pvp' or parts[1] != 'creator':
            await query.edit_message_text("❌ 無效的操作！")
            return
            
        challenge_id = parts[2]
        creator_choice = parts[3]
        
        # 調用後端 API 設定發起人選擇
        response = api_helper.post("/api/bot/pvp/creator-choice", protected_route=True, json={
            "from_user": str(query.from_user.id),
            "challenge_id": challenge_id,
            "choice": creator_choice
        })
        
        if response and isinstance(response, dict):
            if response.get("success"):
                # 發起人已選擇，現在顯示給其他人接受挑戰的按鈕
                challenge_message = escape_markdown(response.get("message"), 2)
                
                # 建立挑戰者選擇的內聯鍵盤
                keyboard = [
                    [
                        InlineKeyboardButton("🪨 石頭", callback_data=f"pvp_accept_{challenge_id}_rock"),
                        InlineKeyboardButton("📄 布", callback_data=f"pvp_accept_{challenge_id}_paper"),
                        InlineKeyboardButton("✂️ 剪刀", callback_data=f"pvp_accept_{challenge_id}_scissors")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    challenge_message,
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=reply_markup
                )
            else:
                # 設定選擇失敗
                error_message = escape_markdown(response.get("message", "設定選擇失敗"), 2)
                await query.answer(error_message, show_alert=True)
        else:
            # 使用者不存在或其他 API 錯誤
            if await verify_existing_user(response, update):
                return
            await query.answer("設定選擇失敗，請稍後再試", show_alert=True)
            
    except Exception as e:
        await query.answer("處理選擇時發生錯誤", show_alert=True)


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
            # 使用者不存在或其他 API 錯誤
            if await verify_existing_user(response, update):
                return
            await query.answer("接受挑戰失敗，請稍後再試", show_alert=True)
            
    except Exception as e:
        await query.answer("處理挑戰時發生錯誤", show_alert=True)


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
            # 重新整理當前頁面 - 預設第1頁
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
