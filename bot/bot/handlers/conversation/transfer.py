from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (CommandHandler, CallbackQueryHandler, ConversationHandler,
                          MessageHandler, filters, ContextTypes)
from telegram.helpers import escape_markdown

from bot.helper.existing_user import verify_existing_user
from utils import api_helper

INPUT_AMOUNT, CHOOSE_TEAM, CHOOSE_PERSON, CONFIRM_TRANSFER = range(4)


async def start_transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = api_helper.post("/api/bot/portfolio", protected_route=True, json={
        "from_user": str(update.effective_user.id),
    })

    if await verify_existing_user(response, update):
        return ConversationHandler.END

    if context.user_data.get("in_transfer_convo"):
        cancel_button = [[InlineKeyboardButton("❌ 取消現有轉帳", callback_data="transfer:cancel")]]
        await update.message.reply_text(
            "😿 你已經有一個正在執行的 /transfer 指令了！請先完成那個動作或是按取消按鈕來取消",
            reply_markup=InlineKeyboardMarkup(cancel_button)
        )
        return None

    if context.user_data.get("in_stock_convo"):
        cancel_button = [[InlineKeyboardButton("❌ 取消現有交易", callback_data="stock:cancel")]]
        await update.message.reply_text(
            "😿 你已經有一個正在執行的 /stock 指令了！請先完成那個動作或是按取消按鈕來取消",
            reply_markup=InlineKeyboardMarkup(cancel_button)
        )
        return None

    context.user_data["in_transfer_convo"] = True
    buttons = [[
        InlineKeyboardButton("❌ 我不要轉帳了！", callback_data="transfer:cancel")
    ]]

    await update.message.reply_text("😺 請輸入你要轉帳的點數️", reply_markup=InlineKeyboardMarkup(buttons))
    return INPUT_AMOUNT


async def input_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit():
        await update.message.reply_text("😾 請輸入一個正確的金額")
        return INPUT_AMOUNT

    amount = int(update.message.text)
    transfer_fee = max(1, int(amount * 0.5))
    total_fee = amount + transfer_fee

    context.user_data["amount"] = amount
    context.user_data["fee"] = transfer_fee
    context.user_data["total"] = total_fee

    response = api_helper.post("/api/bot/portfolio", protected_route=True, json={
        "from_user": str(update.effective_user.id),
    })

    if amount > response.get("points"):
        await update.message.reply_text(
            f"你只有 {response.get('points')} 點，總共需要 {total_fee} 點，*無法轉帳* 😾",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return ConversationHandler.END

    teams = ["第一組", "第二組", "第三組", "第四組", "第五組", "第六組", "第七組", "第八組", "第九組", "第十組"]
    buttons = [[InlineKeyboardButton(text=team, callback_data=f"transfer:team:{team}")] for team in teams]
    buttons.append([InlineKeyboardButton("❌ 我不要轉帳了！", callback_data="transfer:cancel")])

    await update.message.reply_text("😺 請選擇隊伍：", reply_markup=InlineKeyboardMarkup(buttons))
    return CHOOSE_TEAM


async def choose_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    team = query.data.split(":")[2]
    context.user_data["team"] = team

    student_list = api_helper.get("/api/bot/students", protected_route=True)
    filtered_list = [p for p in student_list if p["team"] == team]

    buttons = []
    for person in filtered_list:
        telegram_id = person.get("telegram_id") or "invalid"
        nickname = person.get("telegram_nickname") or person.get("name")
        prefix = "⚠️ " if telegram_id == "invalid" else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"{prefix}{nickname}",
                callback_data=f"transfer:person:{telegram_id}"
            )
        ])
    buttons.append([InlineKeyboardButton("❌ 我不要轉帳了！", callback_data="transfer:cancel")])

    await query.edit_message_text(
        f"😺 請選擇要轉到*{team}*裡面的哪個人：",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return CHOOSE_PERSON


async def choose_person(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    telegram_id = query.data.split(":")[2]

    if telegram_id == "invalid":
        await query.answer("⚠️ 該學員未綁定 Telegram 帳號", show_alert=True)
        return CHOOSE_PERSON

    if telegram_id == str(update.effective_user.id):
        await query.answer("❌ 不能轉給自己！", show_alert=True)
        return CHOOSE_PERSON

    context.user_data["to_user"] = telegram_id

    target_user = api_helper.post("/api/bot/profile", protected_route=True, json={"from_user": telegram_id})
    nickname = escape_markdown(target_user.get("telegram_nickname"), 2)
    amount = context.user_data["amount"]

    buttons = [[
        InlineKeyboardButton("✅ 確認送出", callback_data="transfer:confirm"),
        InlineKeyboardButton("❌ 我不要轉帳了！", callback_data="transfer:cancel")
    ]]

    await query.edit_message_text(
        f"😺 確認轉帳 {amount} 點給 {nickname} 嗎？",
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return CONFIRM_TRANSFER


async def confirm_transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    result = api_helper.post("/api/bot/transfer", protected_route=True, json={
        "from_user": str(update.effective_user.id),
        "to_username": context.user_data["to_user"],
        "amount": context.user_data["amount"]
    })

    if result.get("success"):
        await query.edit_message_text(
            f"✅ 單號 `{result.get('transaction_id')}`：{result.get('message')}，轉了 {context.user_data["amount"]} 點，手續費 {result.get('fee')} 點",
            parse_mode=ParseMode.MARKDOWN_V2
        )
    else:
        await query.edit_message_text(f"❌ {result.get('message')}")

    context.user_data["in_transfer_convo"] = False
    return ConversationHandler.END


async def cancel_transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("轉帳取消ㄌ 👋")
    else:
        await update.message.reply_text("轉帳取消ㄌ 👋")

    context.user_data["in_transfer_convo"] = False
    return ConversationHandler.END


transfer_conversation = ConversationHandler(
    entry_points=[CommandHandler("transfer", start_transfer)],
    states={
        INPUT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_amount)],
        CHOOSE_TEAM: [CallbackQueryHandler(choose_team, pattern="^transfer:team:.*")],
        CHOOSE_PERSON: [CallbackQueryHandler(choose_person, pattern="^transfer:person:.*")],
        CONFIRM_TRANSFER: [CallbackQueryHandler(confirm_transfer, pattern="^transfer:confirm")],
    },
    fallbacks=[CallbackQueryHandler(cancel_transfer, pattern="^transfer:cancel")],
    allow_reentry=True
)
