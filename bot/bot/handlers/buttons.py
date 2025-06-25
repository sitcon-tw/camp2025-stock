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


async def handle_zombie_clicks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        callback_data = update.callback_query.data
        
        # 排除PVP相關的按鈕，這些應該由專門的handler處理，待觀察
        if (callback_data.startswith("pvp_creator_") or 
            callback_data.startswith("pvp_accept_") or 
            callback_data.startswith("pvp_conflict_") or
            callback_data.startswith("orders_")):
            logger.warning(f"Zombie handler caught valid callback: {callback_data}")
            return
            
        await update.callback_query.answer("⚠️ 此按鈕無效，請重新輸入指令來開始新的操作", show_alert=True)
    except BadRequest as e:
        if "too old" in str(e) or "expired" in str(e) or "invalid" in str(e):
            logger.warning(f"Callback query expired or invalid: {e}")
        else:
            logger.error(f"BadRequest in handle_zombie_clicks: {e}")
    except Exception as e:
        logger.error(f"Error in handle_zombie_clicks: {e}")


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
                # 發起人已選擇，更新 PVP 管理器中的狀態
                try:
                    from bot.pvp_manager import get_pvp_manager
                    pvp_manager = get_pvp_manager()
                    pvp_manager.update_challenge_status(challenge_id, "waiting_accepter")
                except Exception as e:
                    logger.error(f"❌ 更新 PVP 挑戰狀態失敗: {e}")
                
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
                
                # 通知 PVP 管理器挑戰已完成
                try:
                    from bot.pvp_manager import get_pvp_manager
                    pvp_manager = get_pvp_manager()
                    await pvp_manager.complete_challenge(challenge_id)
                except Exception as e:
                    logger.error(f"❌ 清理 PVP 挑戰資源失敗: {e}")
                    
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


async def handle_pvp_conflict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 PVP 衝突選擇按鈕"""
    query = update.callback_query
    await query.answer()
    
    try:
        from bot.pvp_manager import get_pvp_manager
        
        callback_data = query.data
        user_id = str(query.from_user.id)
        
        logger.info(f"PVP conflict button pressed: {callback_data} by user {user_id}")
        
        if callback_data.startswith("pvp_conflict_new_"):
            # 使用者選擇取消舊的，開始新的
            # 格式：pvp_conflict_new_{amount}_{chat_id}
            prefix = "pvp_conflict_new_"
            data_part = callback_data[len(prefix):]
            parts = data_part.split("_", 1)  # 只分割一次，避免負數chat_id問題
            if len(parts) >= 2:
                amount = None
                chat_id = None
                try:
                    amount = int(parts[0])
                    chat_id = parts[1]
                    
                    logger.info(f"Parsed data - Amount: {amount} (type: {type(amount)}), Chat ID: {chat_id} (type: {type(chat_id)})")
                    
                    pvp_manager = get_pvp_manager()
                    
                    # 驗證使用者是否有現有挑戰
                    existing_challenge_id = pvp_manager.get_user_challenge(user_id)
                    if not existing_challenge_id:
                        await query.edit_message_text("❌ 沒有找到現有挑戰")
                        return
                    
                    # 取消現有挑戰
                    cancelled = await pvp_manager.cancel_existing_challenge(user_id)
                    
                    if cancelled:
                        # 建立新挑戰
                        logger.info(f"About to create challenge with: user_id={user_id}, amount={amount}, chat_id='{chat_id}' (type: {type(chat_id)})")
                        result = await pvp_manager.create_challenge(
                            user_id=user_id,
                            username=query.from_user.full_name or "未知使用者",
                            amount=amount,
                            chat_id=str(chat_id)  
                        )
                        logger.info(f"Create challenge result: {result}")
                        
                        if not result.get("conflict") and not result.get("error"):
                            challenge_id = result["challenge_id"]
                            
                            # 顯示新挑戰的選擇按鈕
                            message_text = (
                                f"🔄 **已取消舊挑戰，建立新挑戰！**\n\n"
                                f"🎯 你發起了 {amount} 點的 PVP 挑戰！\n"
                                f"⏰ 如果 3 小時沒有回應，系統會自動取消\n\n"
                                f"請先選擇你的猜拳："
                            )
                            
                            keyboard = [
                                [
                                    InlineKeyboardButton("🪨 石頭", callback_data=f"pvp_creator_{challenge_id}_rock"),
                                    InlineKeyboardButton("📄 布", callback_data=f"pvp_creator_{challenge_id}_paper"),
                                    InlineKeyboardButton("✂️ 剪刀", callback_data=f"pvp_creator_{challenge_id}_scissors")
                                ]
                            ]
                            reply_markup = InlineKeyboardMarkup(keyboard)
                            
                            await query.edit_message_text(
                                message_text,
                                parse_mode=ParseMode.MARKDOWN_V2,
                                reply_markup=reply_markup
                            )
                        else:
                            # 安全處理錯誤訊息
                            response = result.get("response", {})
                            if isinstance(response, dict):
                                error_msg = str(response.get("message", "建立新挑戰失敗"))
                            else:
                                error_msg = "建立新挑戰失敗"
                            await query.edit_message_text(f"❌ {error_msg}")
                    else:
                        await query.edit_message_text("❌ 取消舊挑戰失敗，請稍後再試")
                        
                except ValueError:
                    await query.edit_message_text("❌ 無效的金額格式")
                    return
                except Exception as e:
                    logger.error(f"Error processing pvp_conflict_new: {e}")
                    logger.error(f"Callback data: {callback_data}, Amount: {amount}, Chat ID: '{chat_id}' (type: {type(chat_id)})")
                    await query.edit_message_text("❌ 處理請求時發生錯誤")
                    return
            else:
                await query.edit_message_text("❌ 無效的callback數據格式")
        
        elif callback_data.startswith("pvp_conflict_continue_"):
            # 使用者選擇繼續舊的挑戰
            challenge_id = callback_data.replace("pvp_conflict_continue_", "")
            
            pvp_manager = get_pvp_manager()
            challenge_info = pvp_manager.get_challenge_info(challenge_id)
            
            # 驗證使用者是否為挑戰的創建者
            if challenge_info and challenge_info.get("user_id") != user_id:
                await query.edit_message_text("❌ 你不是這個挑戰的創建者")
                return
            
            if challenge_info:
                amount = challenge_info["amount"]
                status = challenge_info.get("status", "waiting_creator")
                
                if status == "waiting_creator":
                    # 發起人還沒選擇猜拳，顯示選擇按鈕
                    message_text = (
                        f"📋 **繼續現有挑戰**\n\n"
                        f"🎯 你的 {amount} 點 PVP 挑戰！\n"
                        f"請選擇你的猜拳："
                    )
                    
                    keyboard = [
                        [
                            InlineKeyboardButton("🪨 石頭", callback_data=f"pvp_creator_{challenge_id}_rock"),
                            InlineKeyboardButton("📄 布", callback_data=f"pvp_creator_{challenge_id}_paper"),
                            InlineKeyboardButton("✂️ 剪刀", callback_data=f"pvp_creator_{challenge_id}_scissors")
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(
                        message_text,
                        parse_mode=ParseMode.MARKDOWN_V2,
                        reply_markup=reply_markup
                    )
                    
                elif status == "waiting_accepter":
                    # 發起人已選擇，等待其他人接受
                    # 計算剩餘時間
                    try:
                        created_at = challenge_info.get('created_at')
                        if created_at and isinstance(created_at, datetime):
                            elapsed = datetime.now() - created_at
                            remaining = timedelta(hours=3) - elapsed
                            
                            if remaining.total_seconds() > 0:
                                minutes = int(remaining.total_seconds()) // 60
                                seconds = int(remaining.total_seconds()) % 60
                                time_str = f"{minutes}分{seconds}秒" if minutes > 0 else f"{seconds}秒"
                                
                                # 轉義Markdown V2特殊字元
                                escaped_time = escape_markdown(time_str, 2)
                                
                                message_text = (
                                    f"📋 **繼續現有挑戰**\n\n"
                                    f"🎯 你的 {amount} 點 PVP 挑戰正在進行中！\n"
                                    f"⏰ 剩餘時間：{escaped_time}\n\n"
                                    f"✅ 你已經選擇好猜拳了\n"
                                    f"🔄 等待其他玩家接受挑戰\\.\\.\\."
                                )
                                
                                await query.edit_message_text(
                                    message_text,
                                    parse_mode=ParseMode.MARKDOWN_V2
                                )
                            else:
                                await query.edit_message_text("❌ 挑戰已超時")
                        else:
                            # 如果無法計算時間，直接顯示狀態
                            message_text = (
                                f"📋 **繼續現有挑戰**\n\n"
                                f"🎯 你的 {amount} 點 PVP 挑戰正在進行中！\n\n"
                                f"✅ 你已經選擇好猜拳了\n"
                                f"🔄 等待其他玩家接受挑戰\\.\\.\\."
                            )
                            
                            await query.edit_message_text(
                                message_text,
                                parse_mode=ParseMode.MARKDOWN_V2
                            )
                    except Exception as time_error:
                        logger.error(f"Error calculating remaining time: {time_error}")
                        # 發生錯誤時，顯示簡化的訊息
                        message_text = (
                            f"📋 **繼續現有挑戰**\n\n"
                            f"🎯 你的 {amount} 點 PVP 挑戰正在進行中！\n\n"
                            f"✅ 你已經選擇好猜拳了\n"
                            f"🔄 等待其他玩家接受挑戰\\.\\.\\."
                        )
                        
                        await query.edit_message_text(
                            message_text,
                            parse_mode=ParseMode.MARKDOWN_V2
                        )
                else:
                    await query.edit_message_text("❌ 挑戰狀態異常")
            else:
                await query.edit_message_text("❌ 找不到該挑戰，可能已超時或被取消")
        
    except Exception as e:
        logger.error(f"Error in handle_pvp_conflict: {e}")
        try:
            await query.edit_message_text("❌ 處理衝突選擇時發生錯誤，請重試")
        except:
            await query.answer("處理衝突選擇時發生錯誤", show_alert=True)


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
