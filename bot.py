import asyncio
import os
from datetime import date, timedelta
from telegram import (
    Update, ReplyKeyboardMarkup, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, CallbackQueryHandler,
    filters, ContextTypes,
)

BOT_TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = int(os.environ["OWNER_ID"])
BASE_DIR = "/opt/srcbot"
COMMUNITY_LINK = "https://t.me/+OaXspSht2cM2MzU6"

ASK_NAME, ASK_DATE = range(2)

MAIN_MENU = ReplyKeyboardMarkup(
    [["🏃 Записаться на пробежку", "💬 Наш чат"]],
    resize_keyboard=True,
)

MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
}


def format_next_dates(n=3) -> list[str]:
    today = date.today()
    candidates = []
    for weekday in (2, 5):
        days_until = (weekday - today.weekday()) % 7
        if days_until == 0:
            days_until = 7
        for i in range(n):
            candidates.append(today + timedelta(days=days_until + i * 7))
    candidates.sort()
    result = []
    for d in candidates[:n]:
        label = f"{d.day} {MONTHS_RU[d.month]}"
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


def save_registration(user_id: int, name: str, chosen_date: str):
    remove_registration(user_id)
    with open(os.path.join(BASE_DIR, "registrations.txt"), "a") as f:
        f.write(f"{user_id}|{name}|{chosen_date}\n")
    with open(os.path.join(BASE_DIR, "users.txt"), "a") as f:
        f.write(f"{user_id}\n")


def remove_registration(user_id: int) -> list | None:
    reg_file = os.path.join(BASE_DIR, "registrations.txt")
    if not os.path.exists(reg_file):
        return None
    lines = open(reg_file).readlines()
    found = None
    remaining = []
    for line in lines:
        parts = line.strip().split("|")
        if parts[0] == str(user_id):
            found = parts
        else:
            remaining.append(line)
    with open(reg_file, "w") as f:
        f.writelines(remaining)
    return found


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    args = context.args
    if args and args[0] == "saturday":
        today = date.today()
        days_until_sat = (5 - today.weekday()) % 7
        if days_until_sat == 0:
            days_until_sat = 7
        next_sat = today + timedelta(days=days_until_sat)
        sat_label = f"{next_sat.day} {MONTHS_RU[next_sat.month]} (суббота)"
        context.user_data["fixed_date"] = sat_label
        await update.message.reply_text(
            f"Привет! 👋\n\nТы регистрируешься на пробежку в субботу, {next_sat.day} {MONTHS_RU[next_sat.month]}.\n\nКак тебя зовут?",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ASK_NAME

    context.user_data.pop("fixed_date", None)
    await update.message.reply_text(
        "Привет! 👋\n\nДобро пожаловать в Sky Runners Club.\nВыбери что хочешь сделать:",
        reply_markup=MAIN_MENU,
    )
    return ConversationHandler.END


async def community_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Присоединяйся к нашему чату! 💬\n\n{COMMUNITY_LINK}",
        reply_markup=MAIN_MENU,
    )


async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("fixed_date", None)
    await update.message.reply_text(
        "Как тебя зовут?",
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

    save_registration(user.id, name, chosen_date)

    cancel_btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Отменить регистрацию", callback_data="cancel_reg")]
    ])
    photo_path = os.path.join(BASE_DIR, "photo.jpg")
    with open(photo_path, "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption=f"Отлично, {name}! ✅\n\nТы зарегистрирован на пробежку {chosen_date}.\n\n{info}",
            reply_markup=cancel_btn,
        )

    await update.message.reply_text(
        "Если планы изменятся — нажми кнопку выше 👆",
        reply_markup=MAIN_MENU,
    )

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
    return await confirm_registration(update, context, update.message.text.strip())


async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    reg = remove_registration(user.id)
    if reg:
        name = reg[1] if len(reg) > 1 else "—"
        reg_date = reg[2] if len(reg) > 2 else "—"
        await query.edit_message_caption(caption="Регистрация отменена ✅\n\nДо встречи в следующий раз! 👋")
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"❌ Отмена регистрации!\n\nИмя: {name}\nДата: {reg_date}\nTelegram: @{user.username or '—'}\nID: {user.id}",
        )
        await context.bot.send_message(chat_id=user.id, text="Выбери что хочешь сделать:", reply_markup=MAIN_MENU)
    else:
        await query.edit_message_caption(caption="Активная регистрация не найдена.")


async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Окей, до встречи! 👋", reply_markup=MAIN_MENU)
    return ConversationHandler.END


async def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^🏃 Записаться на пробежку$"), register_start),
        ],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_name)],
            ASK_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_date)],
        },
        fallbacks=[CommandHandler("cancel", cancel_cmd), CommandHandler("start", start)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.Regex("^💬 Наш чат$"), community_handler))
    app.add_handler(CallbackQueryHandler(cancel_callback, pattern="^cancel_reg$"))

    async with app:
        await app.start()
        await app.updater.start_polling()
        await asyncio.Event().wait()
        await app.updater.stop()
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
