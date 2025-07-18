from datetime import datetime
from os import environ
from zoneinfo import ZoneInfo
from uuid import uuid4

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CopyTextButton
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from bot.helper.chat_ids import MAIN_GROUP, STUDENT_GROUPS
from bot.helper.existing_user import verify_existing_user
from utils import api_helper
from utils.logger import setup_logger

logger = setup_logger(__name__)
load_dotenv()

BACKEND_URL = environ.get("BACKEND_URL")
# 讀取 DEBUG 環境變數
DEBUG = environ.get("DEBUG", "False").lower() == "true"

if DEBUG:
    logger.info("🐛 DEBUG 模式已啟用 - 將忽略群組 ID 限制")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"🚀 使用者 {update.effective_user.full_name} ({update.effective_user.id}) 啟動 BOT")

    response = api_helper.post("/api/bot/portfolio", protected_route=True, json={
        "from_user": str(update.effective_user.id)
    })

    # 除錯：記錄 API 回應內容
    logger.info(f"📊 Portfolio API 回應內容: {response}")

    if await verify_existing_user(response, update):
        return

    buttons = [
        [InlineKeyboardButton(text="📈 開啟喵券機系統", url="https://camp.sitcon.party/")]
    ]

    # 處理可能為 None 的值，提供預設值
    points = response.get("points") if response.get("points") is not None else 0
    stocks = response.get("stocks") if response.get("stocks") is not None else 0
    total_value = response.get("totalValue") if response.get("totalValue") is not None else 0

    await update.message.reply_text(
        f"😺 *早安 {escape_markdown(update.effective_user.full_name, 2)}*\n\n"
        f"🤑┃目前點數 *{escape_markdown(str(points), 2)}*\n"
        f"🏛️┃目前持有股票股數 *{escape_markdown(str(stocks), 2)}*，要不要來點新鮮的股票？\n"
        f"💵┃總資產共 {escape_markdown(str(total_value), 2)}",
        parse_mode=ParseMode.MARKDOWN_V2, reply_markup=InlineKeyboardMarkup(buttons))


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    if not DEBUG and update.message.chat_id == MAIN_GROUP:
        await update.message.reply_text("🚫 請在小隊群裡面註冊！")
        return
    
    portfolio_response = api_helper.post("/api/bot/portfolio", protected_route=True, json={
        "from_user": str(update.effective_user.id)
    })

    # Check if user doesn't exist (either old format or new format)
    detail = portfolio_response.get("detail", "")
    logger.info(f"📊 Portfolio API 回應: {detail}")

    user_not_exists = (
            detail == "noexist" or
            detail.startswith("使用者不存在") or
            (detail == "error" and portfolio_response.get("status_code") == 404)
    )

    logger.info(f"👤 使用者狀態檢查: {'使用者不存在' if user_not_exists else '使用者已存在'}")

    if not user_not_exists:
        await update.message.reply_text(
            f"😸 喵嗚，{escape_markdown(update.effective_user.full_name, 2)}，*你已經註冊過了！*",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        logger.info(f"✋ 使用者 {update.effective_user.full_name} ({update.effective_user.id}) 已經註冊過了")
        return

    if not context.args:
        logger.info(f"📝 使用者 {update.effective_user.full_name} 嘗試註冊但未提供註冊碼")
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
    logger.info(f"📝 使用者 {update.effective_user.full_name} 開始註冊流程，註冊碼: {key}")

    response = api_helper.post("/api/system/users/activate", protected_route=True, json={
        "id": key,
        "telegram_id": str(update.effective_user.id),
        "telegram_nickname": update.effective_user.full_name
    })

    if response.get("ok"):
        name = response.get("message").split(":")[1]
        await update.message.reply_text(
            f"😸 喵嗚，{escape_markdown(update.effective_user.full_name, 2)}，原來你就是 *{escape_markdown(name, 2)}* 啊！\n\n"
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
    if not update.message.chat_id in STUDENT_GROUPS.values():
        await update.message.reply_text("🚫 只能在小隊群組裡面查詢該小隊的點數")
        return

    response = api_helper.get("/api/bot/teams", protected_route=True)

    team_name = list(STUDENT_GROUPS.keys())[list(STUDENT_GROUPS.values()).index(update.message.chat_id)]
    result = next((item for item in response if item["name"] == team_name), None)

    await update.message.reply_text(
        f"👥{team_name} 目前的點數共：*{result.get("total_points")}* 點", parse_mode=ParseMode.MARKDOWN_V2)


async def log(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"/start triggered by {update.effective_user.id}")

    response = api_helper.post("/api/bot/points/history", protected_route=True, json={
        "from_user": str(update.effective_user.id),
        "limit": 10
    })

    if await verify_existing_user(response, update):
        return

    lines = []
    for item in response:
        time = datetime.fromisoformat(item['created_at']).replace(tzinfo=ZoneInfo("UTC")).astimezone(
            ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d %H:%M")

        line = f"`{escape_markdown(time, 2)}`： *{escape_markdown(item['note'], 2)}* {escape_markdown(str(item['amount']), 2)} 點，餘額 *{escape_markdown(str(item['balance_after']), 2)}* 點".strip()
        lines.append(line)

    await update.message.reply_text(
        f"😺 *{escape_markdown(update.effective_user.full_name, 2)} 的點數紀錄*\n"
        f"{"\n".join(lines)}",
        parse_mode=ParseMode.MARKDOWN_V2)


async def pvp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"User {update.effective_user.id} started a PVP request")

    # 檢查是否在群組中
    if update.message.chat.type == "private":
        await update.message.reply_text("🚫 PVP 挑戰只能在群組中使用！")
        return
    
    # 在 DEBUG 模式下忽略群組 ID 限制
    if not DEBUG and update.message.chat_id != MAIN_GROUP:
        await update.message.reply_text("🚫 PVP 挑戰只能在 Camp 大群中使用！")
        return
    
    # DEBUG 模式日誌
    if DEBUG and update.message.chat_id != MAIN_GROUP:
        logger.info(f"🐛 DEBUG 模式：允許在非主群組 {update.message.chat_id} 中使用 PVP")

    # 檢查是否在交易時間內
    try:
        market_response = api_helper.get("/api/status")
        
        # 檢查 API 是否正常回應
        if not market_response or market_response.get("detail") == "error":
            logger.warning("Unable to get market status from backend")
            await update.message.reply_text("⚠️ 無法確認市場狀態，請稍後再試")
            return
        
        # 檢查市場是否開放
        if not market_response.get("isOpen", False):
            await update.message.reply_text("⏰ PVP 挑戰只能在交易時間內進行！")
            return
            
    except Exception as e:
        logger.warning(f"Failed to check market status: {e}")
        await update.message.reply_text("⚠️ 無法確認市場狀態，請稍後再試")
        return

    # 檢查是否提供了金額參數
    if not context.args:
        await update.message.reply_text(
            f"🎯 使用方法：`/pvp <金額>`\n"
            f"例如：`/pvp 100`",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    if not context.args[0].isdigit():
        await update.message.reply_text("🔢 請輸入有效的數字！")
        return

    amount = int(context.args[0])
    if amount <= 0:
        await update.message.reply_text("💰 金額必須大於 0！")
        return
    if amount > 10000:
        await update.message.reply_text("💰 金額不能超過 10000 點！")
        return

    # 使用 PVP Manager 建立挑戰
    from bot.pvp_manager import get_pvp_manager
    pvp_manager = get_pvp_manager()
    
    # 先取消任何現有的挑戰
    await pvp_manager.cancel_existing_challenge(str(update.effective_user.id))
    
    # 建立新挑戰
    result = await pvp_manager.create_challenge(
        user_id=str(update.effective_user.id),
        username=update.effective_user.full_name,
        amount=amount,
        chat_id=str(update.message.chat_id)
    )
    
    if result.get("error"):
        error_message = result['response'].get('message', '未知錯誤')
        
        # 檢查是否是「已有挑戰」的錯誤，如果是則提供取消按鈕
        if "你已經有一個等待接受的挑戰" in error_message or "你已經有一個進行中的挑戰" in error_message:
            buttons = [
                [InlineKeyboardButton("❌ 取消現有挑戰", callback_data=f"pvp:force_cancel:{update.effective_user.id}")]
            ]
            
            await update.message.reply_text(
                f"❌ 建立挑戰失敗：{error_message}",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            await update.message.reply_text(
                f"❌ 建立挑戰失敗：{error_message}"
            )
        return
    
    if result.get("conflict"):
        # 有衝突的挑戰
        existing = result["existing_challenge"]
        remaining_time = result["remaining_time"]
        hours = remaining_time // 3600
        minutes = (remaining_time % 3600) // 60
        
        time_str = f"{hours}小時{minutes}分鐘" if hours > 0 else f"{minutes}分鐘"
        
        buttons = [
            [InlineKeyboardButton("❌ 取消現有挑戰", callback_data=f"pvp:force_cancel:{update.effective_user.id}")]
        ]
        
        await update.message.reply_text(
            f"⚠️ 你已經有一個進行中的 PVP 挑戰！\n"
            f"💰 金額：{existing['amount']} 點\n"
            f"⏰ 剩餘時間：{time_str}\n\n"
            f"請等待挑戰完成或取消後再建立新挑戰。",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return
    
    challenge_id = result["challenge_id"]
    
    # 建立按鈕
    buttons = [
        [InlineKeyboardButton("🤑 我接受 PVP 挑戰！", callback_data=f"pvp:accept:{challenge_id}")],
        [InlineKeyboardButton("❌ 取消 PVP 挑戰", callback_data=f"pvp:cancel:{update.effective_user.id}")]
    ]
    
    # 傳送挑戰訊息
    message = await update.message.reply_text(
        f"😺 *{escape_markdown(update.effective_user.full_name, 2)}* 發起了一個 PVP 挑戰！\n\n"
        f"💰 金額：{amount} 點\n"
        f"🎯 挑戰者：{escape_markdown(update.effective_user.full_name, 2)}\n"
        f"⏰ 挑戰將在 3 小時後過期\n\n"
        f"請其他人點選下面的按鈕來接受挑戰！",
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    
    # 儲存訊息 ID 供後續編輯
    pvp_manager.store_challenge_message(challenge_id, message.message_id)


async def orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """查看自己的掛單清單 - 支援分頁顯示"""
    logger.info(f"📋 使用者 {update.effective_user.full_name} 查看訂單清單")

    # 獲取頁碼參數，預設為第1頁
    page = 1
    if context.args and context.args[0].isdigit():
        page = max(1, int(context.args[0]))

    await show_orders_page(update, str(update.effective_user.id), page)


async def show_orders_page(update_or_query, user_id: str, page: int = 1, edit_message: bool = False):
    """顯示指定頁面的訂單清單"""
    ORDERS_PER_PAGE = 8  # 每頁顯示的訂單數量

    # 調用後端 API 獲取使用者的所有股票訂單
    response = api_helper.post("/api/bot/stock/orders", protected_route=True, json={
        "from_user": user_id,
        "limit": 100  # 獲取更多訂單用於分頁
    })

    if hasattr(update_or_query, 'data'):
        # 來自 callback query（CallbackQuery 對象）
        query = update_or_query
        user_name = query.from_user.full_name

        # 建立一個模擬的 Update 對象來檢查使用者狀態
        class MockUpdate:
            def __init__(self, query):
                self.effective_user = query.from_user
                self.answer = query.answer

        mock_update = MockUpdate(query)
        if await verify_existing_user(response, mock_update, is_callback=True):
            return
    else:
        # 來自普通訊息（Update 對象）
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

        # 新增時間資訊
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
                if filled_qty > 0:
                    filled_price = order.get('filled_price', price)
                    remaining_qty = quantity - filled_qty
                    status_text = f"部分成交 ({filled_qty}/{quantity} 股已成交@{filled_price}元，剩餘{remaining_qty}股等待)"
                else:
                    status_text = '等待成交'
            elif status == 'pending':
                if filled_qty > 0:
                    filled_price = order.get('filled_price', price)
                    remaining_qty = quantity - filled_qty
                    status_text = f"部分成交 ({filled_qty}/{quantity} 股已成交@{filled_price}元，剩餘{remaining_qty}股等待)"
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

    # 獲取目前頁的訂單
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
                if lines:  # 如果不是第一個區段，新增空行
                    lines.append("")

                if order_type == 'pending':
                    lines.append("*🔄 進行中的訂單：*")
                else:
                    lines.append("*📈 歷史訂單：*")
                current_section = order_type

            lines.append(order_text)

    # 頁面資訊
    page_info = f"第 {page}/{total_pages} 頁 (共 {total_orders} 筆訂單)"
    message_text = f"📊 *{escape_markdown(user_name, 2)} 的股票訂單*\n\n" + "\n".join(
        lines) + f"\n\n{escape_markdown(page_info, 2)}"

    # 建立分頁按鈕
    keyboard = []

    # 只有在多於一頁時才顯示導航按鈕
    if total_pages > 1:
        nav_buttons = []

        if page > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️ 上一頁", callback_data=f"orders_page_{page - 1}"))

        nav_buttons.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="orders_refresh"))

        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton("➡️ 下一頁", callback_data=f"orders_page_{page + 1}"))

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

    # 傳送或編輯訊息
    if edit_message and hasattr(update_or_query, 'edit_message_text'):
        try:
            await update_or_query.edit_message_text(
                message_text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.warning(f"Failed to edit message: {e}")
            # 如果編輯失敗，傳送新訊息
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
