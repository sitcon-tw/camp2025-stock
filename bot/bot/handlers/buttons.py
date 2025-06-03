from telegram import Update
from telegram.ext import ContextTypes
from utils.logger import setup_logger

logger = setup_logger(__name__)

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.callback_query:
        return

    args = update.callback_query.data.split(":")

    if not args[0] == "cb":
        return

    if not args[-1] == str(update.effective_user.id):
        await update.callback_query.answer(text="這個不是你的按鈕！")
        return

    match args[1]:
        case "stock":
            match args[2]:
                case "buy":
                    if args[3] == "proceed":
                        # TODO: Buy it, waiting for API
                        await update.callback_query.message.edit_text(
                            f"""
                            ✅ 成功購買 {args[4]} 張股票
                            """
                        )
                        await update.callback_query.answer()
                    else:
                        await update.callback_query.message.edit_text(
                            f"""
                            ❌ 取消ㄌ，什麼都沒發生
                            """
                        )
                        await update.callback_query.answer()
                case "sell":
                    if args[3] == "proceed":
                        # TODO: Sell it, waiting for API
                        await update.callback_query.message.edit_text(
                            f"""
                            ✅ 成功賣掉 {args[4]} 張股票
                            """
                        )
                        await update.callback_query.answer()
                    else:
                        await update.callback_query.message.edit_text(
                            f"""
                            ❌ 取消ㄌ，什麼都沒發生
                            """
                        )
                        await update.callback_query.answer()