from os import environ
from traceback import format_exception
from typing import Optional

from dotenv import load_dotenv
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ChatMemberHandler, CallbackQueryHandler, CallbackContext
from telegram.helpers import escape_markdown

from bot.handlers import commands, welcome, buttons
from bot.handlers.stock.conversation_handler import stock_conversation
from bot.instance import bot
from utils.logger import setup_logger

logger = setup_logger(__name__)
load_dotenv()

ERROR_CHANNEL = environ.get("ERROR_CHANNEL")

async def error_handler(update: Optional[object], context: CallbackContext) -> None:
    crashed_message = getattr(update, "message", None)

    if context.error:
        trace = format_exception(type(context.error), context.error, context.error.__traceback__)

        logger.error(f"An exception occurred: {trace[-1].replace("\n", "")}", exc_info=(type(context.error), context.error, context.error))

        # Bot API uses group ID with a negative sign
        await context.bot.send_message(f"-{ERROR_CHANNEL}",
                                       f"🙀 *世界崩塌了，喵喵大人跑出了錯誤！*\n"
                                       f"```\n"
                                       f"{"".join(trace)}\n"
                                       f"```", parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await context.bot.send_message(f"-{ERROR_CHANNEL}", "🙀 *世界崩塌了，喵喵大人跑出了錯誤！* 但是沒有 traceback 可以看")

    if crashed_message:
        is_group = bool(getattr(crashed_message, "chat", "chat 為空").title)
        chat_name = escape_markdown(getattr(getattr(crashed_message, "chat", "chat 為空"), "title", "群組無名稱") or
                                    getattr(getattr(crashed_message, "chat", "chat 為空"), "first_name", "無使用者名稱"), 2)

        await context.bot.send_message(f"-{ERROR_CHANNEL}",
                                       f"*觸發{"群組" if is_group else "__私訊__"}*: {chat_name}\n"
                                       f"*觸發使用者首名*: {escape_markdown(getattr(getattr(crashed_message, "from_user", "from_user 為空"), "first_name", "使用者無名稱"), 2)}\n"
                                       f"*觸發使用者名稱*: {escape_markdown(getattr(getattr(crashed_message, "from_user", "from_user 為空"), "username", "使用者無使用者名稱"), 2)}\n"
                                       f"*觸發使用者 ID*: {getattr(getattr(crashed_message, "from_user", "from_user 為空"), "id", "使用者無 ID")}\n"
                                       f"*觸發指令*: {escape_markdown(getattr(crashed_message, "text", "未知指令"), 2)}\n"
                                          , parse_mode=ParseMode.MARKDOWN_V2)

        await context.bot.send_message(crashed_message.chat.id, "😿 你的指令爆炸了，問題已經自動回報給資訊組，請等待支援！" ,reply_to_message_id=crashed_message.message_id)
    else:
        await context.bot.send_message(ERROR_CHANNEL, f"無可回報之 message object")

async def initialize():
    bot.add_handler(stock_conversation)
    bot.add_handler(CommandHandler("start", commands.start))
    bot.add_handler(CommandHandler("register", commands.register))
    bot.add_handler(CommandHandler("point", commands.point))
    bot.add_handler(CommandHandler("log", commands.log))
    bot.add_handler(CommandHandler("cancel", commands.cancel))
    bot.add_handler(CallbackQueryHandler(buttons.handle_zombie_clicks))
    bot.add_handler(ChatMemberHandler(welcome.welcome_member, ChatMemberHandler.CHAT_MEMBER))
    bot.add_error_handler(error_handler)

    await bot.initialize()
    await bot.bot.set_my_commands([
        ("start", "顯示你的個人資訊，喵喵"),
        ("register", "註冊你的 Telegram 帳號"),
        ("point", "查看小隊們與自己的點數"),
        ("stock", "買賣點數"),
        ("log", "查看自己的點數交易紀錄"),
        ("cancel", "取消購買操作")
    ])
