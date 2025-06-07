from os import environ
from datetime import datetime

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CopyTextButton
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from bot.helper.existing_user import verify_existing_user
from utils import api_helper
from utils.logger import setup_logger

logger = setup_logger(__name__)
load_dotenv()

BACKEND_URL = environ.get("BACKEND_URL")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"/start triggered by {update.effective_user.id}")

    response = api_helper.post("/api/bot/portfolio", protected_route=True, json={
        "from_user": str(update.effective_user.id)
    })

    if await verify_existing_user(response, update):
        return

    buttons = [
        [InlineKeyboardButton(text="📈 開啟喵券機系統", url="https://w.wolf-yuan.dev/youtube")]
    ]

    await update.message.reply_text(
        f"""
        😺 *早安 {escape_markdown(update.effective_user.full_name, 2)}*

🤑┃目前點數 *{response.get("points")}*
🏛️┃目前持有股票張數 *{response.get("stocks")}*，要不要來點新鮮的股票？

💵┃總資產共 {response.get("totalValue")}
""",
        parse_mode=ParseMode.MARKDOWN_V2, reply_markup=InlineKeyboardMarkup(buttons))


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    portfolio_response = api_helper.post("/api/bot/portfolio", protected_route=True, json={
        "from_user": str(update.effective_user.id)
    })

    if not portfolio_response.get("detail") == "noexist":
        await update.message.reply_text(
            f"""
            😸 喵嗚，{escape_markdown(update.effective_user.full_name)}，*你已經註冊過了！*
        """, parse_mode=ParseMode.MARKDOWN_V2)
        return

    if not context.args:
        logger.info(f"/register triggered by {update.effective_user.id} without key")
        buttons = [
            [InlineKeyboardButton(text="複製註冊指令", copy_text=CopyTextButton("/register "))],
        ]

        await update.message.reply_text(
            """
            😿 *你沒有給本喵專屬於你的註冊碼*

>你可以在你的 email 裡面找到那個註冊碼，然後把註冊碼加在 `/register` 後面
>例如說，你的註冊碼是 `12345678`，你應該要輸入 `/register 12345678`
            """,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return
    key = context.args[0]
    logger.info(f"/register triggered by {update.effective_user.id}, key: {key}")

    response = api_helper.post("/api/system/users/activate", protected_route=True, json={
        "id": key,
        "telegram_id": str(update.effective_user.id),
        "telegram_nickname": update.effective_user.full_name
    })

    if response.get("ok"):
        name = response.get("message").split(":")[1]
        await update.message.reply_text(
            f"""
            😸 喵嗚，{escape_markdown(update.effective_user.full_name)}，原來你就是 *{name}* 啊！

很高興可以在 *SITCON Camp 2025* 看到你，希望你可以在這裡交到好多好多好朋友
我叫做喵券機，顧名思義就是拿來買股票券的機器人，你可以跟我買股票喵！
        """, parse_mode=ParseMode.MARKDOWN_V2)
    else:
        message = response.get("message")

        match message:
            case "noexist":
                await update.message.reply_text(f"🙀 你輸入的註冊碼 `{escape_markdown(key, 2)}` 好像不存在", parse_mode=ParseMode.MARKDOWN_V2)
            case "already_activated":
                await update.message.reply_text(f"🙀 註冊碼 `{escape_markdown(key, 2)}` 已經被註冊過了", parse_mode=ParseMode.MARKDOWN_V2)
            case "error":
                await update.message.reply_text(f"🤯 後端爆炸了，請敲工作人員！")
            case _:
                await update.message.reply_text(f"🙀 好像有什麼東西炸掉了")
                logger.error(f"Executing register got {message}")

async def point(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # TODO: Team to chat ID mapping
    response = api_helper.get("/api/bot/teams", protected_route=True)

    result = next((item for item in response if item["name"] == "第六組"), None)

    await update.message.reply_text(
        f"""
        👥 小隊 __*3*__ 目前的點數共：*{result.get("total_points")}* 點
        """, parse_mode=ParseMode.MARKDOWN_V2)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get("active_stock_convo"):
        await update.message.reply_text("❌ 指令似乎出錯了，已解鎖 /stock 指令")
        context.user_data["active_stock_convo"] = False
    else:
        await update.message.reply_text("❌ 沒有正在操作的指令")

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"/start triggered by {update.effective_user.id}")

    response = api_helper.post("/api/bot/points/history", protected_route=True, json={
        "from_user": str(update.effective_user.id),
        "limit": 10
    })

    if await verify_existing_user(response, update):
        return

    lines = []
    for item in response:
        time = datetime.fromisoformat(item['created_at']).strftime("%Y-%m-%d %H:%M")

        line = f"`{escape_markdown(time, 2)}`： *{escape_markdown(item['note'], 2)}* {escape_markdown(str(item['amount']), 2)} 點，餘額 *{escape_markdown(str(item['balance_after']), 2)}* 點".strip()
        lines.append(line)

    print(lines)

    await update.message.reply_text(
        f"""
        😺 *{escape_markdown(update.effective_user.full_name)} 的點數紀錄*
        
{"\n".join(lines)}
        """, parse_mode=ParseMode.MARKDOWN_V2)

async def pvp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            f"""
            🐱 你得標一個人來 PVP！
            """
        )
        return

    target_username = context.args[0]