from telegram import Update, ChatMember
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from utils.logger import setup_logger

logger = setup_logger(__name__)

async def welcome_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_member_update = update.chat_member

    old_member_status = chat_member_update.old_chat_member.status if chat_member_update.old_chat_member else None
    new_member_status = chat_member_update.new_chat_member.status if chat_member_update.new_chat_member else None

    if (old_member_status not in [ChatMember.MEMBER, ChatMember.OWNER, ChatMember.ADMINISTRATOR] and
            new_member_status in [ChatMember.MEMBER, ChatMember.OWNER, ChatMember.ADMINISTRATOR]):

        new_member = chat_member_update.new_chat_member.user
        chat = update.effective_chat

        if new_member and chat:
            await context.bot.send_message(
                chat_id=chat.id,
                text=f"""
                👋 你好 *{new_member.full_name}* ！
歡迎加入 SITCON Camp 的小隊群組！我是喵券機，你在這個營隊中一直會看到我哦！

這個群組是小隊 _*3*_ 的，請不要走錯地方囉
如果你是這個小隊的，請在你的 email 裡面找一找一個 *註冊碼*，並在這個聊天室輸入 `/register 註冊碼` 來註冊
>例如你的註冊碼是 `1234567890`，就要在這個小隊的頻道裡面輸入 `/register 1234567890`
                """,
                parse_mode=ParseMode.MARKDOWN_V2
            )
            logger.info(f"{new_member.username} joined chat {chat.id}")