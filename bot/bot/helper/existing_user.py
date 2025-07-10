from telegram import Update
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown


async def verify_existing_user(response, update: Update, is_callback: bool = False) -> bool:
    if not type(response) == dict:
        return False

    # Check for old style "noexist" detail response
    if response.get("detail") == "noexist":
        message_text = (
            f"😺 *早安 {escape_markdown(update.effective_user.full_name, 2)}*\n"
            f"你還沒完成註冊程序，請輸入 /register 來看看怎麼註冊！"
        )
        
        if is_callback:
            # 對於 callback query，使用 answer 顯示彈出訊息
            await update.answer("你還沒完成註冊程序，請輸入 /register 來註冊！", show_alert=True)
        else:
            # 對於普通訊息，回覆文字訊息
            await update.message.reply_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN_V2
            )
        return True
    
    # Check for new style PVP response with user not found message
    if (response.get("success") == False and 
        response.get("message") == "使用者不存在，請先註冊"):
        message_text = (
            f"😺 *早安 {escape_markdown(update.effective_user.full_name, 2)}*\n"
            f"你還沒完成註冊程序，請輸入 /register 來看看怎麼註冊！"
        )
        
        if is_callback:
            # 對於 callback query，使用 answer 顯示彈出訊息
            await update.answer("你還沒完成註冊程序，請輸入 /register 來註冊！", show_alert=True)
        else:
            # 對於普通訊息，回覆文字訊息
            await update.message.reply_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN_V2
            )
        return True
    
    # Check for backend portfolio API user not found response
    if (response.get("detail") and 
        response.get("detail").startswith("使用者不存在")):
        message_text = (
            f"😺 *早安 {escape_markdown(update.effective_user.full_name, 2)}*\n"
            f"你還沒完成註冊程序，請輸入 /register 來看看怎麼註冊！"
        )
        
        if is_callback:
            # 對於 callback query，使用 answer 顯示彈出訊息
            await update.answer("你還沒完成註冊程序，請輸入 /register <code> 來註冊！", show_alert=True)
        else:
            # 對於普通訊息，回覆文字訊息
            await update.message.reply_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN_V2
            )
        return True
    
    # Check for API error responses (404, connection errors, etc.)
    if (response.get("detail") == "error" and 
        response.get("status_code") in [404, 500, 503]):
        message_text = (
            f"😺 *早安 {escape_markdown(update.effective_user.full_name, 2)}*\n"
            f"系統目前無法連接到後端服務，請稍後再試或聯繫管理員！"
        )
        
        if is_callback:
            # 對於 callback query，使用 answer 顯示彈出訊息
            await update.answer("系統目前無法連接，請稍後再試！", show_alert=True)
        else:
            # 對於普通訊息，回覆文字訊息
            await update.message.reply_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN_V2
            )
        return True
    
    return False


async def verify_user_can_trade(response, update: Update, is_callback: bool = False) -> bool:
    """
    檢查用戶是否可以進行交易（包括欠款和凍結檢查）
    
    Args:
        response: API 回應
        update: Telegram 更新
        is_callback: 是否為回調查詢
        
    Returns:
        bool: True 表示有問題需要處理，False 表示可以繼續
    """
    if not isinstance(response, dict):
        return False
    
    # 檢查是否有用戶數據
    user_data = response.get('user') or response.get('data')
    if not user_data:
        return False
    
    # 檢查帳戶凍結狀態
    if user_data.get('frozen', False):
        message_text = (
            f"❄️ *帳戶已凍結*\n\n"
            f"你的帳戶已被凍結，無法進行交易或轉帳。\n"
            f"請聯繫管理員了解詳情。"
        )
        
        if is_callback:
            await update.answer("帳戶已凍結，無法進行交易！", show_alert=True)
        else:
            await update.message.reply_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN_V2
            )
        return True
    
    # 檢查欠款狀態
    owed_points = user_data.get('owed_points', 0)
    if owed_points > 0:
        current_points = user_data.get('points', 0)
        message_text = (
            f"💳 *帳戶有欠款*\n\n"
            f"你的帳戶有欠款 *{owed_points}* 點\n"
            f"目前餘額：*{current_points}* 點\n"
            f"實際可用：*{current_points - owed_points}* 點\n\n"
            f"請先償還欠款後才能進行交易。\n"
            f"如需協助，請聯繫管理員。"
        )
        
        if is_callback:
            await update.answer(f"帳戶有欠款 {owed_points} 點，請先償還！", show_alert=True)
        else:
            await update.message.reply_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN_V2
            )
        return True
    
    # 檢查帳戶是否未啟用
    if not user_data.get('enabled', True):
        message_text = (
            f"⚠️ *帳戶未啟用*\n\n"
            f"你的帳戶尚未啟用，無法進行交易。\n"
            f"請聯繫管理員啟用帳戶。"
        )
        
        if is_callback:
            await update.answer("帳戶未啟用，無法進行交易！", show_alert=True)
        else:
            await update.message.reply_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN_V2
            )
        return True
    
    # 所有檢查都通過
    return False
