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
BASE_DIR = "/opt/srcbot"

ASK_NAME, ASK_DATE = range(2)


def format_next_dates(n=3) -> list[str]:
    today = date.today()
    months_ru = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля",
        5: "мая", 6: "июня", 7: "июля", 8: "августа",
        9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
    }
    candidates = []
    for weekday in (2, 5):  # среда=2, суббота=5
        days_until = (weekday - today.weekday()) % 7
        if days_until == 0:
            days_until = 7
        for i in range(n):
            candidates.append(today + timedelta(days=days_until + i * 7))
    candidates.sort()
    result = []
    for d in candidates[:n]:
        label = f"{d.day} {months_ru[d.month]}"
        if (d - today).days <= 7:
            day_name = "среда" if d.weekday() == 2 else "суббота"
            label += f" (эта {day_name})"
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
        months_ru = {
            1: "января", 2: "февраля", 3: "марта", 4: "апреля",
            5: "мая", 6: "июня", 7: "июля", 8: "августа",
            9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
        }
        today = date.today()
        days_until_sat = (5 - today.weekday()) % 7
        if days_until_sat == 0:
            days_until_sat = 7
        next_sat = today + timedelta(days=days_until_sat)
        sat_label = f"{next_sat.day} {months_ru[next_sat.month]} (суббота)"
        context.user_data["fixed_date"] = sat_label
        await update.message.reply_text(
            f"Привет! 👋\n\nТы регистрируешься на пробежку в субботу, {next_sat.day} {months_ru[next_sat.month]}.\n\nКак тебя зовут?",
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        context.user_data.pop("fixed_date", None)
        await update.message.reply_text(
            "Привет! 👋\n\nДобро пожаловать в Sky Runners Club.\n\nКак тебя зовут?",
            reply_markup=ReplyKeyboardRemove(),
        )
    return ASK_NAME


async def received_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text.strip()

    if context.user_data.get("fixed_date"):
        return await confirm_registration(update, context, context.user_data["fixed_date"])

    dates = format_next_dates()
    keyboard = [[d] for d in dates]
    await update.message.reply_text(
        "На какую дату записываешься?",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return ASK_DATE


async def confirm_registration(update: Update, context: ContextTypes.DEFAULT_TYPE, chosen_date: str) -> int:
    name = context.user_data.get("name", "")
    user = update.effective_user
    is_saturday = context.user_data.get("fixed_date") or "суббота" in chosen_date
    info = RUN_INFO_SATURDAY if is_saturday else RUN_INFO

    photo_path = os.path.join(BASE_DIR, "photo.jpg")
    with open(photo_path, "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption=f"Отлично, {name}! ✅\n\nТы зарегистрирован на пробежку {chosen_date}.\n\n{info}",
            reply_markup=ReplyKeyboardRemove(),
        )

    users_file = os.path.join(BASE_DIR, "users.txt")
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
