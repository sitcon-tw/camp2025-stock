from datetime import datetime
from os import environ

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
        f"😺 *早安 {escape_markdown(update.effective_user.full_name, 2)}*\n\n"
        f"🤑┃目前點數 *{response.get("points")}*\n"
        f"🏛️┃目前持有股票股數 *{response.get("stocks")}*，要不要來點新鮮的股票？\n"
        f"💵┃總資產共 {response.get("totalValue")}",
        parse_mode=ParseMode.MARKDOWN_V2, reply_markup=InlineKeyboardMarkup(buttons))


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    portfolio_response = api_helper.post("/api/bot/portfolio", protected_route=True, json={
        "from_user": str(update.effective_user.id)
    })

    if not portfolio_response.get("detail") == "noexist":
        await update.message.reply_text(
            f"😸 喵嗚，{escape_markdown(update.effective_user.full_name)}，*你已經註冊過了！*",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    if not context.args:
        logger.info(f"/register triggered by {update.effective_user.id} without key")
        buttons = [
            [InlineKeyboardButton(text="複製註冊指令", copy_text=CopyTextButton("/register "))],
        ]

        await update.message.reply_text(
            "😿 *你沒有給本喵專屬於你的註冊碼*\n\n"
            ">你可以在你的 email 裡面找到那個註冊碼，然後把註冊碼加在 `/register` 後面\n"
            ">例如說，你的註冊碼是 `12345678`，你應該要輸入 `/register 12345678\n`",
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
            f"😸 喵嗚，{escape_markdown(update.effective_user.full_name)}，原來你就是 *{name}* 啊！\n\n"
            f"很高興可以在 *SITCON Camp 2025* 看到你，希望你可以在這裡交到好多好多好朋友\n"
            f"我叫做喵券機，顧名思義就是拿來買股票券的機器人，你可以跟我買股票喵！"
            , parse_mode=ParseMode.MARKDOWN_V2)
    else:
        message = response.get("message")

        match message:
            case "noexist":
                await update.message.reply_text(
                    f"🙀 你輸入的註冊碼 `{escape_markdown(key, 2)}` 好像不存在",
                    parse_mode=ParseMode.MARKDOWN_V2)
            case "already_activated":
                await update.message.reply_text(
                    f"🙀 註冊碼 `{escape_markdown(key, 2)}` 已經被註冊過了",
                    parse_mode=ParseMode.MARKDOWN_V2)
            case "error":
                await update.message.reply_text("🤯 後端爆炸了，請敲工作人員！")
            case _:
                await update.message.reply_text("🙀 好像有什麼東西炸掉了")
                logger.error(f"Executing register got {message}")


async def point(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # TODO: Team to chat ID mapping
    response = api_helper.get("/api/bot/teams", protected_route=True)

    result = next((item for item in response if item["name"] == "第一組"), None)

    await update.message.reply_text(
        f"👥 小隊 __*3*__ 目前的點數共：*{result.get("total_points")}* 點", parse_mode=ParseMode.MARKDOWN_V2)


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
        f"😺 *{escape_markdown(update.effective_user.full_name)} 的點數紀錄*\n"
        f"{"\n".join(lines)}",
        parse_mode=ParseMode.MARKDOWN_V2)


async def pvp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """PVP 猜拳挑戰"""
    logger.info(f"/pvp triggered by {update.effective_user.id}")
    
    # 檢查是否在群組中
    if update.message.chat.type == 'private':
        await update.message.reply_text(
            "🚫 PVP 挑戰只能在群組中使用！",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return
    
    # 檢查是否提供了金額參數
    if not context.args:
        await update.message.reply_text(
            "🎯 使用方法：`/pvp <金額>`\n例如：`/pvp 100`",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    try:
        amount = int(context.args[0])
        if amount <= 0:
            await update.message.reply_text(
                "💰 金額必須大於 0！",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return
        if amount > 10000:
            await update.message.reply_text(
                "💰 金額不能超過 10000 點！",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return
    except ValueError:
        await update.message.reply_text(
            "🔢 請輸入有效的數字！",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    # 調用後端 API 建立 PVP 挑戰
    response = api_helper.post("/api/bot/pvp/create", protected_route=True, json={
        "from_user": str(update.effective_user.id),
        "amount": amount,
        "chat_id": str(update.message.chat.id)
    })

    if await verify_existing_user(response, update):
        return

    if response.get("success"):
        challenge_id = response.get("challenge_id")
        message_text = escape_markdown(response.get("message"), 2)
        
        # 建立內聯鍵盤
        keyboard = [
            [
                InlineKeyboardButton("🪨 石頭", callback_data=f"pvp_accept_{challenge_id}_rock"),
                InlineKeyboardButton("📄 布", callback_data=f"pvp_accept_{challenge_id}_paper"),
                InlineKeyboardButton("✂️ 剪刀", callback_data=f"pvp_accept_{challenge_id}_scissors")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message_text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            escape_markdown(response.get("message", "建立挑戰失敗"), 2),
            parse_mode=ParseMode.MARKDOWN_V2
        )


async def orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """查看自己的掛單清單"""
    logger.info(f"/orders triggered by {update.effective_user.id}")

    # 調用後端 API 獲取用戶的股票訂單
    response = api_helper.post("/api/bot/stock/orders", protected_route=True, json={
        "from_user": str(update.effective_user.id),
        "limit": 20  # 顯示最近 20 筆訂單
    })

    if await verify_existing_user(response, update):
        return

    if not response:
        await update.message.reply_text(
            "📋 你目前沒有任何股票訂單記錄",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    # 分別處理進行中和已完成的訂單
    pending_orders = []
    completed_orders = []
    
    for order in response:
        status = order.get('status', 'unknown')
        side_emoji = "🟢" if order.get('side') == 'buy' else "🔴"
        side_text = "買入" if order.get('side') == 'buy' else "賣出"
        
        quantity = order.get('quantity', 0)
        price = order.get('price', 0)
        order_info = f"{side_emoji} {side_text} {quantity} 股 @ {price} 元"
        
        if status in ['pending', 'partial', 'pending_limit']:
            # 進行中的訂單
            status_text = {
                'pending': '等待成交',
                'partial': '部分成交',
                'pending_limit': '等待(超出限制)'
            }.get(status, status)
            
            filled_qty = order.get('filled_quantity', 0)
            if filled_qty > 0:
                order_info += f" (已成交: {filled_qty})"
            
            pending_orders.append(f"• {escape_markdown(order_info, 2)} \\- {escape_markdown(status_text, 2)}")
            
        elif status in ['filled', 'cancelled']:
            # 已完成的訂單
            status_text = "已成交" if status == 'filled' else "已取消"
            filled_price = order.get('filled_price')
            if filled_price:
                order_info += f" → 成交價: {filled_price} 元"
            
            # 添加時間
            if order.get('created_at'):
                try:
                    time = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00')).strftime("%m-%d %H:%M")
                    order_info += f" ({time})"
                except:
                    pass
            
            completed_orders.append(f"• {escape_markdown(order_info, 2)} \\- {escape_markdown(status_text, 2)}")

    # 構建回復訊息
    lines = []
    
    if pending_orders:
        lines.append("🔄 *進行中的訂單：*")
        lines.extend(pending_orders[:10])  # 最多顯示 10 筆進行中訂單
        if len(pending_orders) > 10:
            lines.append(f"\\.\\.\\. 還有 {len(pending_orders) - 10} 筆訂單")
    
    if completed_orders:
        if lines:  # 如果已有進行中訂單，添加分隔
            lines.append("")
        lines.append("✅ *最近完成的訂單：*")
        lines.extend(completed_orders[:5])  # 最多顯示 5 筆已完成訂單
        if len(completed_orders) > 5:
            lines.append(f"\\.\\.\\. 還有 {len(completed_orders) - 5} 筆歷史訂單")

    if not lines:
        lines.append("📋 目前沒有訂單記錄")

    message_text = f"📊 *{escape_markdown(update.effective_user.full_name)} 的股票訂單*\n\n" + "\n".join(lines)
    
    await update.message.reply_text(
        message_text,
        parse_mode=ParseMode.MARKDOWN_V2
    )
