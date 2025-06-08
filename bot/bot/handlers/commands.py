from datetime import datetime
from os import environ
from zoneinfo import ZoneInfo

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
        [InlineKeyboardButton(text="📈 開啟喵券機系統", url="https://camp.sitcon.party/")]
    ]

    await update.message.reply_text(
        f"😺 *早安 {escape_markdown(update.effective_user.full_name, 2)}*\n\n"
        f"🤑┃目前點數 *{escape_markdown(str(response.get("points")), 2)}*\n"
        f"🏛️┃目前持有股票股數 *{escape_markdown(str(response.get("stocks")), 2)}*，要不要來點新鮮的股票？\n"
        f"💵┃總資產共 {escape_markdown(str(response.get("totalValue")), 2)}",
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
            f"😸 喵嗚，{escape_markdown(update.effective_user.full_name)}，原來你就是 *{escape_markdown(name)}* 啊！\n\n"
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
        time = datetime.fromisoformat(item['created_at']).replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d %H:%M")

        line = f"`{escape_markdown(time, 2)}`： *{escape_markdown(item['note'], 2)}* {escape_markdown(str(item['amount']), 2)} 點，餘額 *{escape_markdown(str(item['balance_after']), 2)}* 點".strip()
        lines.append(line)

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
        
        # 發起人先選擇猜拳
        message_text = f"🎯 你發起了 {amount} 點的 PVP 挑戰！\n\n請先選擇你的猜拳："
        
        # 建立發起人選擇的內聯鍵盤
        keyboard = [
            [
                InlineKeyboardButton("🪨 石頭", callback_data=f"pvp_creator_{challenge_id}_rock"),
                InlineKeyboardButton("📄 布", callback_data=f"pvp_creator_{challenge_id}_paper"),
                InlineKeyboardButton("✂️ 剪刀", callback_data=f"pvp_creator_{challenge_id}_scissors")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            escape_markdown(message_text, 2),
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            escape_markdown(response.get("message", "建立挑戰失敗"), 2),
            parse_mode=ParseMode.MARKDOWN_V2
        )


async def orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """查看自己的掛單清單 - 支援分頁顯示"""
    logger.info(f"/orders triggered by {update.effective_user.id}")
    
    # 獲取頁碼參數，預設為第1頁
    page = 1
    if context.args and context.args[0].isdigit():
        page = max(1, int(context.args[0]))
    
    await show_orders_page(update, str(update.effective_user.id), page)


async def show_orders_page(update_or_query, user_id: str, page: int = 1, edit_message: bool = False):
    """顯示指定頁面的訂單清單"""
    ORDERS_PER_PAGE = 8  # 每頁顯示的訂單數量
    
    # 調用後端 API 獲取用戶的所有股票訂單
    response = api_helper.post("/api/bot/stock/orders", protected_route=True, json={
        "from_user": user_id,
        "limit": 100  # 獲取更多訂單用於分頁
    })

    if hasattr(update_or_query, 'message'):
        # 來自 callback query
        update = update_or_query
        user_name = update.from_user.full_name
        if await verify_existing_user(response, update, is_callback=True):
            return
    else:
        # 來自普通訊息
        update = update_or_query
        user_name = update.effective_user.full_name
        if await verify_existing_user(response, update):
            return

    if not response:
        message_text = "📋 你目前沒有任何股票訂單記錄"
        
        if edit_message and hasattr(update_or_query, 'edit_message_text'):
            await update_or_query.edit_message_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN_V2
            )
        else:
            if hasattr(update_or_query, 'message'):
                await update_or_query.message.reply_text(
                    message_text,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            else:
                await update_or_query.message.reply_text(
                    message_text,
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
        order_type = order.get('order_type', 'unknown')
        order_type_text = "市價" if order_type == 'market' else "限價"
        
        # 基本訂單資訊
        order_info = f"{side_emoji} {side_text} {quantity} 股"
        if order_type == 'limit' and price:
            order_info += f" @ {price} 元 ({order_type_text})"
        else:
            order_info += f" ({order_type_text})"
        
        # 添加時間資訊
        time_str = ""
        if order.get('created_at'):
            try:
                time = datetime.fromisoformat(order['created_at']).replace(
                    tzinfo=ZoneInfo("UTC")
                ).astimezone(ZoneInfo("Asia/Taipei")).strftime("%m/%d %H:%M")
                time_str = f" `{time}`"
            except:
                pass
        
        if status in ['pending', 'partial', 'pending_limit']:
            # 進行中的訂單
            filled_qty = order.get('filled_quantity', 0)
            
            if status == 'partial':
                filled_price = order.get('filled_price', price)
                status_text = f"部分成交 ({filled_qty}/{quantity}@{filled_price}元)"
            elif status == 'pending':
                if filled_qty > 0:
                    filled_price = order.get('filled_price', price)
                    status_text = f"等待中 (已成交{filled_qty}股@{filled_price}元)"
                else:
                    status_text = '等待成交'
            elif status == 'pending_limit':
                status_text = '等待中(限制)'
            else:
                status_text = status
            
            pending_orders.append({
                'text': f"• {escape_markdown(order_info, 2)}{escape_markdown(time_str, 2)}\n  *{escape_markdown(status_text, 2)}*",
                'created_at': order.get('created_at', '')
            })
            
        elif status in ['filled', 'cancelled']:
            # 已完成的訂單
            status_text = "✅ 已成交" if status == 'filled' else "❌ 已取消"
            filled_price = order.get('filled_price')
            if filled_price and status == 'filled':
                order_info += f" → {filled_price}元"
            
            completed_orders.append({
                'text': f"• {escape_markdown(order_info, 2)}{escape_markdown(time_str, 2)}\n  {escape_markdown(status_text, 2)}",
                'created_at': order.get('created_at', '')
            })

    # 合併所有訂單並按時間排序（最新的在前）
    all_orders = []
    
    # 進行中的訂單優先顯示
    for order in sorted(pending_orders, key=lambda x: x['created_at'], reverse=True):
        all_orders.append(('pending', order['text']))
    
    # 然後是已完成的訂單
    for order in sorted(completed_orders, key=lambda x: x['created_at'], reverse=True):
        all_orders.append(('completed', order['text']))

    # 計算分頁資訊
    total_orders = len(all_orders)
    total_pages = max(1, (total_orders + ORDERS_PER_PAGE - 1) // ORDERS_PER_PAGE)
    page = max(1, min(page, total_pages))
    
    # 獲取當前頁的訂單
    start_idx = (page - 1) * ORDERS_PER_PAGE
    end_idx = start_idx + ORDERS_PER_PAGE
    current_page_orders = all_orders[start_idx:end_idx]

    # 構建訊息內容
    if not current_page_orders:
        lines = ["📋 目前沒有訂單記錄"]
    else:
        lines = []
        current_section = None
        
        for order_type, order_text in current_page_orders:
            if order_type != current_section:
                if lines:  # 如果不是第一個區段，添加空行
                    lines.append("")
                
                if order_type == 'pending':
                    lines.append("*🔄 進行中的訂單：*")
                else:
                    lines.append("*📈 歷史訂單：*")
                current_section = order_type
            
            lines.append(order_text)

    # 頁面資訊
    page_info = f"第 {page}/{total_pages} 頁 \\(共 {total_orders} 筆訂單\\)"
    message_text = f"📊 *{escape_markdown(user_name)} 的股票訂單*\n\n" + "\n".join(lines) + f"\n\n{escape_markdown(page_info, 2)}"

    # 創建分頁按鈕
    keyboard = []
    nav_buttons = []
    
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ 上一頁", callback_data=f"orders_page_{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="orders_refresh"))
    
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("➡️ 下一頁", callback_data=f"orders_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # 功能按鈕
    function_buttons = []
    if total_pages > 1:
        function_buttons.append(InlineKeyboardButton("🔄 重新整理", callback_data="orders_refresh"))
    if page != 1:
        function_buttons.append(InlineKeyboardButton("📋 第一頁", callback_data="orders_page_1"))
    if page != total_pages and total_pages > 1:
        function_buttons.append(InlineKeyboardButton("📑 最後一頁", callback_data=f"orders_page_{total_pages}"))
    
    if function_buttons:
        # 將功能按鈕分成兩行
        if len(function_buttons) > 2:
            keyboard.append(function_buttons[:2])
            keyboard.append(function_buttons[2:])
        else:
            keyboard.append(function_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    # 發送或編輯訊息
    if edit_message and hasattr(update_or_query, 'edit_message_text'):
        try:
            await update_or_query.edit_message_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.warning(f"Failed to edit message: {e}")
            # 如果編輯失敗，發送新訊息
            await update_or_query.message.reply_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=reply_markup
            )
    else:
        if hasattr(update_or_query, 'message'):
            await update_or_query.message.reply_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=reply_markup
            )
        else:
            await update_or_query.message.reply_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=reply_markup
            )
