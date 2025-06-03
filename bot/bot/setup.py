from telegram.ext import CommandHandler, ChatMemberHandler, CallbackQueryHandler, ContextTypes
from bot.handlers import commands, welcome, buttons
from bot.instance import bot
from utils.logger import setup_logger

logger = setup_logger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Exception while handling an update: {context.error}")

async def initialize():
    bot.add_handler(CommandHandler("start", commands.start))
    bot.add_handler(CommandHandler("register", commands.register))
    bot.add_handler(CommandHandler("point", commands.point))
    bot.add_handler(CommandHandler("stock", commands.stock))
    bot.add_handler(CallbackQueryHandler(buttons.callback))
    bot.add_handler(ChatMemberHandler(welcome.welcome_member, ChatMemberHandler.CHAT_MEMBER))
    bot.add_error_handler(error_handler)

    await bot.initialize()
    await bot.bot.set_my_commands([
        ("start", "喵喵喵喵"),
        ("register", "註冊你自己！"),
        ("point", "查看小隊們與自己的點數"),
        ("stock", "買賣點數")
    ])
