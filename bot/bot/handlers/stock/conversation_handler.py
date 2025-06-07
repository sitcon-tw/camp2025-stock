from warnings import filterwarnings

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters, \
    CommandHandler
from telegram.warnings import PTBUserWarning

from bot.helper.existing_user import verify_existing_user
from utils import api_helper

(
    CHOOSE_ACTION,
    INPUT_AMOUNT,
    CHOOSE_ORDER_TYPE,
    INPUT_LIMIT_PRICE,
    CONFIRM_ORDER,
) = range(5)

async def start_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = api_helper.post("/api/bot/portfolio", protected_route=True, json={
        "from_user": str(update.effective_user.id)
    })

    if await verify_existing_user(response, update):
        return ConversationHandler.END

    if context.user_data.get("in_stock_convo"):
        await update.message.reply_text("你已經有一個進行中的操作了！請先完成那個或是執行 /cancel 來取消 💢")
        return ConversationHandler.END

    context.user_data["in_stock_convo"] = True

    keyboard = [
        [
            InlineKeyboardButton("💸 買", callback_data="stock:buy"),
            InlineKeyboardButton("🤑 賣", callback_data="stock:sell")
        ],
        [InlineKeyboardButton("❌ 取消操作", callback_data="cancel")]
    ]
    await update.message.reply_text(
        "😺 你想要*買*還是*賣*股票？",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return CHOOSE_ACTION

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action = query.data.split(":")[1]
    context.user_data["action"] = action
    await query.edit_message_text(f"請輸入你要{"買" if action == "buy" else "賣"}的數量（1 ~ 30）：")
    return INPUT_AMOUNT

async def input_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if not text.isdigit():
        await update.message.reply_text("請輸入數字啦喂 💢")
        return INPUT_AMOUNT

    amount = int(text)
    if amount < 1 or amount > 30:
        await update.message.reply_text("數量不可以小於 1 或大於 30 ❌")
        return INPUT_AMOUNT

    context.user_data["amount"] = amount

    keyboard = [
        [InlineKeyboardButton("市價單", callback_data="order:market"),
         InlineKeyboardButton("限價單", callback_data="order:limit")]
    ]
    await update.message.reply_text(
        "請選擇下單方式 🧾",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSE_ORDER_TYPE

async def choose_order_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_type = query.data.split(":")[1]
    context.user_data["order_type"] = order_type

    if order_type == "limit":
        await query.edit_message_text("請輸入限價價格（1~1000）💰：")
        return INPUT_LIMIT_PRICE
    else:
        await confirm_order(update, context)
        return CONFIRM_ORDER

async def input_limit_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if not text.isdigit():
        await update.message.reply_text("😾 不要亂打數字！請輸入一個正確的數字")
        return INPUT_LIMIT_PRICE

    price = int(text)
    if price < 1 or price > 1000:
        await update.message.reply_text("❗ 限價價格要在 1 ~ 1000 之間")
        return INPUT_LIMIT_PRICE

    context.user_data["price"] = price
    await confirm_order(update, context)
    return CONFIRM_ORDER

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data
    action = "買" if data["action"] == "buy" else "賣"
    amount = data["amount"]
    order_type = "市價單" if data["order_type"] == "market" else "限價單"
    price = data.get("price")

    msg = (f"😺 請確認以下訂單\n"
           f"\n"
           f"你想要**{action}** `{amount}` 張 SITC\n"
           f"訂單是{order_type}")
    if price:
        msg += f"，{action}入價格為 `{price}` 點"

    keyboard = [[
        InlineKeyboardButton("✅ 確認送出", callback_data="confirm:yes"),
        InlineKeyboardButton("❌ 取消", callback_data="confirm:no")
    ]]

    if isinstance(update, Update) and update.callback_query:
        await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN_V2)

    return CONFIRM_ORDER

async def final_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = context.user_data

    if query.data == "confirm:yes":
        request_body = {
            "from_user": str(update.effective_user.id),
            "order_type": data["order_type"],
            "side": data["action"],
            "quantity": int(data["amount"]),
        }

        if data.get("price"):
            request_body["price"] = int(data["price"]),

        response = api_helper.post("/api/bot/stock/order", protected_route=True, json=request_body)

        if response.get("success"):
            await query.edit_message_text(
                f"✅ 單號 `{response.get("order_id")}`：{response.get("message")}", parse_mode=ParseMode.MARKDOWN_V2
            )
        else:
            print(response)
            await query.edit_message_text(
                f"❌ {response.get("message")}"
            )

        context.user_data["in_stock_convo"] = False
    else:
        await query.edit_message_text("訂單已取消。喵～ 👋")
        context.user_data["in_stock_convo"] = False

    return ConversationHandler.END

async def cancel_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("操作已取消。喵～ 👋")

    context.user_data["in_stock_convo"] = False
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("操作已取消。喵～ 👋")

    context.user_data["in_stock_convo"] = False
    return ConversationHandler.END

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

stock_conversation = ConversationHandler(
    entry_points=[CommandHandler("stock", start_stock)],
    states={
        CHOOSE_ACTION: [
            CallbackQueryHandler(choose_action, pattern="^stock:(buy|sell)$"),
            CallbackQueryHandler(cancel_button_handler, pattern="^cancel$")
        ],
        INPUT_AMOUNT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, input_amount),
            CallbackQueryHandler(cancel_button_handler, pattern="^cancel$")
        ],
        CHOOSE_ORDER_TYPE: [
            CallbackQueryHandler(choose_order_type, pattern="^order:(market|limit)$"),
            CallbackQueryHandler(cancel_button_handler, pattern="^cancel$")
        ],
        INPUT_LIMIT_PRICE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, input_limit_price),
            CallbackQueryHandler(cancel_button_handler, pattern="^cancel$")
        ],
        CONFIRM_ORDER: [
            CallbackQueryHandler(final_confirmation, pattern="^confirm:(yes|no)$"),
            CallbackQueryHandler(cancel_button_handler, pattern="^cancel$")
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    allow_reentry=True
)
