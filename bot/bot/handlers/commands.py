from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CopyTextButton
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from utils.logger import setup_logger

logger = setup_logger(__name__)

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
        buttons = [
            [InlineKeyboardButton(text="複製買入指令", copy_text=CopyTextButton("/stock buy "))],
            [InlineKeyboardButton(text="複製買出指令", copy_text=CopyTextButton("/stock buy "))],
            [InlineKeyboardButton(text="複製查看股價指令", copy_text=CopyTextButton("/stock list "))]
        ]

        await update.message.reply_text(
            f"""
            🐱 *三幣指數股交易系統*

*/stock buy 數量* 買入三幣指數股
*/stock sell 數量* 賣出三幣指數股
*/stock list* 查看持有股票與現價
            """, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=InlineKeyboardMarkup(buttons))
        return

    is_sell_command = context.args[0] == "sell"

    if (context.args[0] == "buy" or context.args[0] == "sell") and len(context.args) <= 1:
        await update.message.reply_text(
            f"""
            ❓ 你要{is_sell_command and "賣出" or "買入"}多少張三幣指數股？
請把要{is_sell_command and "賣出" or "買入"}的數量加在指令後面哦
            """)
        return

    if not (context.args[1]).isdigit():
        await update.message.reply_text("❓ 可以給我一個正常的數字嗎")
        return

    quantity = int(context.args[1])

    if quantity <= 0:
        await update.message.reply_text("❓ 幽默，想要買 0 張股票")
        return
    elif quantity > 30:
        await update.message.reply_text("😿 最多只能買 30 張股票")
        return

    buttons = [[
        InlineKeyboardButton(text="❌ 取消", callback_data=f"cb:stock:{is_sell_command and "sell" or "buy"}:cancel:{update.effective_user.id}"),
        InlineKeyboardButton(text="✅ 確定", callback_data=f"cb:stock:{is_sell_command and "sell" or "buy"}:proceed:{quantity}:{update.effective_user.id}")
    ]]

    match context.args[0]:
        case "buy":
            await update.message.reply_text(
                f"""
                🙀 是否真的要*購買 {context.args[1]} 張*三幣指數股？
                """, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=InlineKeyboardMarkup(buttons))
            return
        case "sell":
            await update.message.reply_text(
                f"""
                🙀 是否真的要*賣出 {context.args[1]} 張*三幣指數股？
                """, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=InlineKeyboardMarkup(buttons))
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
                😿 我沒有叫做 `{context.args[1]}` 的指令！
                """)
            return

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"""
        來財
        """, parse_mode=ParseMode.MARKDOWN_V2)