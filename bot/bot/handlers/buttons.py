import asyncio
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

    # 檢查市場狀態
    try:
        market_status = api_helper.get("/api/status")
        if not market_status or not market_status.get("isOpen", False):
            await query.answer("🚫 目前交易已經關閉，無法進行 PVP 挑戰！", show_alert=True)
            return
    except Exception as e:
        logger.warning(f"Failed to check market status: {e}")
        await query.answer("⚠️ 無法確認市場狀態，請稍後再試", show_alert=True)
        return

    from bot.pvp_manager import get_pvp_manager
    pvp_manager = get_pvp_manager()

    if data[1] == "cancel":
        original_user_id = data[2]
        if str(update.effective_user.id) != original_user_id:
            await query.answer("❌ 你不能取消別人的 PVP 挑戰！", show_alert=True)
            return

        # 使用 PVP Manager 取消挑戰
        success = await pvp_manager.cancel_existing_challenge(original_user_id)
        if success:
            await query.answer("✅ 已取消 PVP 挑戰", show_alert=True)
        else:
            await query.answer("❌ 取消挑戰失敗或挑戰不存在", show_alert=True)
            
    elif data[1] == "force_cancel":
        # 強制取消現有挑戰（用於解決衝突）
        user_id = data[2]
        if str(update.effective_user.id) != user_id:
            await query.answer("❌ 你不能取消別人的 PVP 挑戰！", show_alert=True)
            return
            
        success = await pvp_manager.cancel_existing_challenge(user_id)
        if success:
            await query.answer("✅ 已取消現有挑戰，你現在可以建立新挑戰了！", show_alert=True)
            await query.edit_message_text("❌ 原 PVP 挑戰已被取消")
        else:
            await query.answer("❌ 取消挑戰失敗", show_alert=True)
            
    elif data[1] == "accept":
        challenge_id = data[2]
        
        logger.info(f"PVP accept button clicked: user {update.effective_user.id}, challenge {challenge_id}")

        # 調用新的簡單 PVP API
        try:
            logger.info(f"Calling API: /api/bot/pvp/simple-accept with user {update.effective_user.id}")
            response = api_helper.post("/api/bot/pvp/simple-accept", protected_route=True, json={
                "from_user": str(update.effective_user.id),
                "challenge_id": challenge_id
            })
            
            logger.info(f"API response: {response}")
            
            if response.get("success"):
                # 遊戲成功完成
                message = response.get("message", "PVP 挑戰完成！")
                await query.answer("🎮 PVP 挑戰完成！", show_alert=False)
                
                # 更新訊息顯示結果，移除所有按鈕
                await safe_edit_message(
                    query, 
                    message,
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=None  # 移除所有按鈕
                )
                
                # 通知 PVP Manager 挑戰完成
                await pvp_manager.complete_challenge(challenge_id)
                
            else:
                # 遊戲失敗
                error_message = response.get("message", "接受挑戰失敗")
                await query.answer(f"❌ {error_message}", show_alert=True)
                
                # 如果是點數不足等錯誤，保持挑戰活躍
                if "點數不足" in error_message or "餘額" in error_message:
                    return
                
                # 其他錯誤則取消挑戰
                await pvp_manager.complete_challenge(challenge_id)
                await safe_edit_message(query, f"❌ 挑戰失敗：{error_message}", reply_markup=None)
                
        except Exception as e:
            logger.error(f"Error accepting PVP challenge: {e}")
            await query.answer("❌ 接受挑戰時發生錯誤，請稍後再試", show_alert=True)


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
