import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

BOT_TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = int(os.environ["OWNER_ID"])

ASK_NAME = 0

RUN_INFO = """🏃 Информация о пробежке:

📅 Дата: воскресенье, 29 июня
⏰ Время: 09:00
📍 Место: Парк Горького, главный вход (метро Октябрьская)
👟 Дистанция: 5 км (темп свободный)
🌤 Одевайтесь по погоде, возьмите воду

До встречи на старте! 💪"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Привет! 👋\n\nДобро пожаловать в Sky Runners Club.\n\nКак вас зовут?",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ASK_NAME


async def received_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    user = update.effective_user

    await update.message.reply_text(
        f"Отлично, {name}! ✅\n\nВы зарегистрированы на пробежку.\n\n{RUN_INFO}",
        reply_markup=ReplyKeyboardRemove(),
    )

    await context.bot.send_message(
        chat_id=OWNER_ID,
        text=f"🆕 Новая регистрация!\n\nИмя: {name}\nTelegram: @{user.username or '—'}\nID: {user.id}",
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Окей, до встречи! 👋")
    return ConversationHandler.END


def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_name)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    app.run_polling()


if __name__ == "__main__":
    main()
