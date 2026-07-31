import asyncio
import os
from datetime import date, timedelta
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

ASK_NAME, ASK_DATE = range(2)


def next_wednesdays(n=4) -> list[str]:
    today = date.today()
    days_until_wed = (2 - today.weekday()) % 7
    if days_until_wed == 0:
        days_until_wed = 7
    result = []
    for i in range(n):
        d = today + timedelta(days=days_until_wed + i * 7)
        result.append(d.strftime("%d.%m (%a)").replace("Wed", "ср").replace("Mon", "пн")
                       .replace("Tue", "вт").replace("Thu", "чт").replace("Fri", "пт")
                       .replace("Sat", "сб").replace("Sun", "вс"))
    return result


def format_wednesdays() -> list[str]:
    today = date.today()
    days_until_wed = (2 - today.weekday()) % 7
    if days_until_wed == 0:
        days_until_wed = 7
    months_ru = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля",
        5: "мая", 6: "июня", 7: "июля", 8: "августа",
        9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
    }
    result = []
    for i in range(3):
        d = today + timedelta(days=days_until_wed + i * 7)
        label = f"{d.day} {months_ru[d.month]}"
        if i == 0:
            label += " (эта среда)"
        result.append(label)
    return result


RUN_INFO = """🏃 Информация о пробежке:

📍 Место сбора: кофейня AMO, Мичуринский проспект, 56
🕖 Сбор: 19:00 | Старт: 19:30
🗺 Маршрут: Парк Событие, ~5 км
💸 Участие: бесплатно

Темп — комфортный, без требований к подготовке.
С нами бегает фотограф — снимки пришлём после.
После финиша можно выпить кофе в AMO 🫶

До встречи на старте! 💪

А пока можешь посмотреть фото с прошлых пробежек!
https://disk.360.yandex.ru/d/qyGbYXCGzV7u1A"""

RUN_INFO_SATURDAY = """🏃 Информация о пробежке:

📍 Место сбора: кофейня AMO, Мичуринский проспект, 56
🕙 Сбор: 10:00 | Старт: 10:30
🗺 Маршрут: Парк Событие, ~5 км
💸 Участие: бесплатно

Темп — комфортный, без требований к подготовке.
С нами бегает фотограф — снимки пришлём после.
После финиша можно выпить кофе в AMO 🫶

До встречи на старте! 💪

А пока можешь посмотреть фото с прошлых пробежек!
https://disk.360.yandex.ru/d/qyGbYXCGzV7u1A"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    args = context.args
    if args and args[0] == "saturday":
        context.user_data["fixed_date"] = "1 августа (суббота)"
        await update.message.reply_text(
            "Привет! 👋\n\nВы регистрируетесь на дополнительную пробежку в субботу, 2 августа.\n\nКак Вас зовут?",
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        context.user_data.pop("fixed_date", None)
        await update.message.reply_text(
            "Привет! 👋\n\nДобро пожаловать в Sky Runners Club.\n\nКак Вас зовут?",
            reply_markup=ReplyKeyboardRemove(),
        )
    return ASK_NAME


async def received_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text.strip()

    if context.user_data.get("fixed_date"):
        return await confirm_registration(update, context, context.user_data["fixed_date"])

    dates = format_wednesdays()
    keyboard = [[d] for d in dates]
    await update.message.reply_text(
        "На какую среду записываетесь?",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return ASK_DATE


async def confirm_registration(update: Update, context: ContextTypes.DEFAULT_TYPE, chosen_date: str) -> int:
    name = context.user_data.get("name", "")
    user = update.effective_user
    info = RUN_INFO_SATURDAY if context.user_data.get("fixed_date") else RUN_INFO

    photo_path = os.path.join(os.path.dirname(__file__), "photo.jpg")
    with open(photo_path, "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption=f"Отлично, {name}! ✅\n\nВы зарегистрированы на пробежку {chosen_date}.\n\n{info}",
            reply_markup=ReplyKeyboardRemove(),
        )

    users_file = os.path.join(os.path.dirname(__file__), "users.txt")
    with open(users_file, "a") as f:
        f.write(f"{user.id}\n")

    await context.bot.send_message(
        chat_id=OWNER_ID,
        text=(
            f"🆕 Новая регистрация!\n\n"
            f"Имя: {name}\n"
            f"Дата: {chosen_date}\n"
            f"Telegram: @{user.username or '—'}\n"
            f"ID: {user.id}"
        ),
    )
    return ConversationHandler.END


async def received_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chosen_date = update.message.text.strip()
    return await confirm_registration(update, context, chosen_date)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Окей, до встречи! 👋", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_name)],
            ASK_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_date)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
        allow_reentry=True,
    )

    app.add_handler(conv)

    async with app:
        await app.start()
        await app.updater.start_polling()
        await asyncio.Event().wait()
        await app.updater.stop()
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
