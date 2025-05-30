from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, Application, ContextTypes, CommandHandler
from telegram.constants import ParseMode
from dotenv import load_dotenv
from utils.logger import setup_logger
from os import getenv

logger = setup_logger(__name__)

load_dotenv()
BOT_TOKEN = getenv("TELEGRAM_BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.username
    logger.info(f"/start triggered by {username}")

    buttons = [
        [InlineKeyboardButton(text="📈 開啟喵券機系統", url="https://w.wolf-yuan.dev/youtube")]
    ]

    await update.message.reply_text(
        f"""
        😺 *早安 {username}*

🤑┃目前餘額 *0 元*，你窮死了
🏛️┃目前持有股票張數 *0 張*，要不要來點新鮮的股票？
""",
        parse_mode=ParseMode.MARKDOWN_V2, reply_markup=InlineKeyboardMarkup(buttons))


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.username
    if not context.args:
        await update.message.reply_text(
            """
            😿 *你沒有給本喵專屬於你的註冊碼*

>你可以在你的 email 裡面找到那個註冊碼，然後把註冊碼加在 `/register` 後面
>例如說，你的註冊碼是 `12345678`，你應該要輸入 `/register 12345678`
            """,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return
    key = context.args[0]
    logger.info(f"/register triggered by {username}, key: {key}")

    # TODO: Fetch user's information here

    buttons = [
        [InlineKeyboardButton(text="📈 開啟喵喵喵券機系統", url="https://w.wolf-yuan.dev/youtube")]
    ]

    await update.message.reply_text(
        f"""
        😸 喵嗚，{username}，原來你就是 *王小明* 啊！
        
很高興可以在 *SITCON Camp 2025* 看到你，希望你可以在這裡交到好多好多好朋友 😺
我叫做喵券機，顧名思義就是拿來買股票券的機器人，你可以跟我買股票喵！

*想現在就試試看嗎？*點一下底下的按鈕，開啟_*喵券機股票交易頁面吧！*_
        """, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=InlineKeyboardMarkup(buttons))

bot = ApplicationBuilder().token(BOT_TOKEN).build()

bot.add_handler(CommandHandler("start", start))
bot.add_handler(CommandHandler("register", register))

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)

bot.add_error_handler(error_handler)

async def initialize():
    await bot.initialize()
    await bot.bot.set_my_commands([
        ("start", "喵喵喵喵"),
        ("register", "註冊你自己！")
    ])

__all__ = ["bot", "initialize"]
