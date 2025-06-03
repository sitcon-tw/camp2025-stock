from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, Application, ContextTypes, CommandHandler, ChatMemberHandler
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
    logger.info(f"/register triggered by {update.effective_chat.username}, key: {key}")

    # TODO: Fetch user's information here

    buttons = [
        [InlineKeyboardButton(text="📈 開啟喵喵喵券機系統", url="https://w.wolf-yuan.dev/youtube")]
    ]

    await update.message.reply_text(
        f"""
        😸 喵嗚，{update.effective_chat.username}，原來你就是 *王小明* 啊！

很高興可以在 *SITCON Camp 2025* 看到你，希望你可以在這裡交到好多好多好朋友 😺
我叫做喵券機，顧名思義就是拿來買股票券的機器人，你可以跟我買股票喵！

*想現在就試試看嗎？*點一下底下的按鈕，開啟_*喵券機股票交易頁面吧！*_
        """, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=InlineKeyboardMarkup(buttons))

async def point(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # TODO: Data fetching

    await update.message.reply_text(
        f"""
        👥 小隊 _*3*_ 隊員們目前的點數

• 王小明 *13 點*
• 王大明 *1044 點*
• 王聰明 *0 點*
• *王有錢* *1555 點*

🤑 小隊目前共：*好多* 點
        """, parse_mode=ParseMode.MARKDOWN_V2)

async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            f"""
            🐱 你想要做什麼事情呢？

- `/stock buy 數量` 買入 `數量` 張三幣指數股
- `/stock sell 數量` 賣出 `數量` 張三幣指數股
- `/stock list` 查看持有股票與現價
            """, parse_mode=ParseMode.MARKDOWN_V2)
        return

    if (context.args[0] == "buy" or context.args[0] == "sell") and not context.args[1]:
        is_sell_command = context.args[0] == "sell"

        await update.message.reply_text(
            f"""
            ❓ 你要 {is_sell_command and "賣出" or "買入"} 多少張三幣指數股？
            """)
        return

    match context.args[0]:
        case "buy":
            await update.message.reply_text(
                f"""
                ✅ 成果買入 {context.args[1]} 張三幣指數股，你現在有 *好多張* 三幣指數股
                """, parse_mode=ParseMode.MARKDOWN_V2)
            return
        case "sell":
            await update.message.reply_text(
                f"""
                ✅ 成果賣出 {context.args[1]} 張三幣指數股，你現在有 *好少張* 三幣指數股
                """, parse_mode=ParseMode.MARKDOWN_V2)
            return
        case "list":
            await update.message.reply_text(
                f"""
                🏦 三幣指數股目前股價：

📈 上漲：+10%
💰 目前股價：$100
                """, parse_mode=ParseMode.MARKDOWN_V2)
            return
        case _:
            await update.message.reply_text(
                f"""
                😿 什麼指令是 `{context.args[1]}`？
                """)
            return

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

bot = ApplicationBuilder().token(BOT_TOKEN).build()

bot.add_handler(ChatMemberHandler(welcome_member, ChatMemberHandler.CHAT_MEMBER))
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
