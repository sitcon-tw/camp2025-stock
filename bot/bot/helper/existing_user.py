from telegram import Update
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

async def verify_existing_user(response: dict, update: Update) -> bool:
    if response.get("detail") == "noexist":
        await update.message.reply_text(f"""😺 *早安 {escape_markdown(update.effective_user.full_name, 2)}*

你還沒完成註冊程序，請輸入 /register 來看看怎麼註冊！
""", parse_mode=ParseMode.MARKDOWN_V2)
        return True
    return False
