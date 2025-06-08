from telegram import Update
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown


async def verify_existing_user(response, update: Update, is_callback: bool = False) -> bool:
    if not type(response) == dict:
        return False

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
    return False
