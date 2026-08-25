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

ASK_NAME, ASK_DISTANCE, ASK_DATE = range(3)

MAIN_MENU = ReplyKeyboardMarkup(
    [["🏃 Записаться на пробежку", "💬 Наш чат"]],
    resize_keyboard=True,
)

MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
}

DISTANCE_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("🟢 5 км (стандарт)", callback_data="dist_5")],
    [InlineKeyboardButton("🔵 8–10 км (подальше)", callback_data="dist_long")],
    [InlineKeyboardButton("💬 Свой вариант / хочу обсудить", callback_data="dist_custom")],
])


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


RUN_INFO = """📍 Место сбора: кофейня AMO, Мичуринский проспект, 56
🕖 Сбор: 19:00 | Старт: 19:30
🗺 Маршрут: Парк Событие, ~5 км
💸 Участие: бесплатно

Темп — комфортный, без требований к подготовке.
С нами бегает фотограф — снимки пришлём после.
После финиша можно выпить кофе в AMO 🫶

До встречи на старте! 💪

А пока можешь посмотреть фото с прошлых пробежек!
https://disk.360.yandex.ru/d/qyGbYXCGzV7u1A"""

RUN_INFO_SATURDAY = """📍 Место сбора: кофейня AMO, Мичуринский проспект, 56
🕙 Сбор: 10:00 | Старт: 10:30
🗺 Маршрут: Парк Событие, ~5 км
💸 Участие: бесплатно

Темп — комфортный, без требований к подготовке.
С нами бегает фотограф — снимки пришлём после.
После финиша можно выпить кофе в AMO 🫶

До встречи на старте! 💪

А пока можешь посмотреть фото с прошлых пробежек!
https://disk.360.yandex.ru/d/qyGbYXCGzV7u1A"""


def save_registration(user_id: int, name: str, distance: str, chosen_date: str):
    remove_registration(user_id)
    with open(os.path.join(BASE_DIR, "registrations.txt"), "a") as f:
        f.write(f"{user_id}|{name}|{distance}|{chosen_date}\n")
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
    context.user_data.clear()

    if args and args[0] == "saturday":
        today = date.today()
        days_until_sat = (5 - today.weekday()) % 7
        if days_until_sat == 0:
            days_until_sat = 7
        next_sat = today + timedelta(days=days_until_sat)
        context.user_data["fixed_date"] = f"{next_sat.day} {MONTHS_RU[next_sat.month]} (суббота)"
        await update.message.reply_text(
            f"Привет! 👋\n\nТы регистрируешься на пробежку в субботу, {next_sat.day} {MONTHS_RU[next_sat.month]}.\n\nКак тебя зовут?",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ASK_NAME

    if args and args[0] == "long":
        context.user_data["preferred_long"] = True
        await update.message.reply_text(
            "Привет! 👋\n\nОтлично, что хочешь бежать дальше! Давай запишем тебя.\n\nКак тебя зовут?",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ASK_NAME

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
    context.user_data.clear()
    await update.message.reply_text(
        "Как тебя зовут?",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ASK_NAME


async def received_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text.strip()

    if context.user_data.get("preferred_long"):
        msg = "Отлично! Выбери дистанцию — мы видим, что тебя интересует что-то подлиннее 😉"
    else:
        msg = "Какую дистанцию планируешь?"

    await update.message.reply_text(msg, reply_markup=DISTANCE_KEYBOARD)
    return ASK_DISTANCE


async def received_distance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    dist_map = {
        "dist_5": "5 км",
        "dist_long": "8–10 км",
        "dist_custom": "Свой вариант",
    }
    distance = dist_map.get(query.data, "5 км")
    context.user_data["distance"] = distance

    await query.edit_message_reply_markup(reply_markup=None)
    await query.edit_message_text(f"Дистанция: {distance} ✅")

    if context.user_data.get("fixed_date"):
        return await confirm_registration(update, context, context.user_data["fixed_date"])

    dates = format_next_dates()
    keyboard = [[d] for d in dates]
    await context.bot.send_message(
        chat_id=query.from_user.id,
        text="На какую дату записываешься?",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return ASK_DATE


async def confirm_registration(update: Update, context: ContextTypes.DEFAULT_TYPE, chosen_date: str) -> int:
    user = update.effective_user or update.callback_query.from_user
    name = context.user_data.get("name", "")
    distance = context.user_data.get("distance", "5 км")
    is_saturday = context.user_data.get("fixed_date") or "суббота" in chosen_date
    info = RUN_INFO_SATURDAY if is_saturday else RUN_INFO

    save_registration(user.id, name, distance, chosen_date)

    cancel_btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Отменить регистрацию", callback_data="cancel_reg")]
    ])

    caption = f"Отлично, {name}! ✅\n\nТы зарегистрирован на пробежку {chosen_date}.\n🏃 Дистанция: {distance}\n\n{info}"

    photo_path = os.path.join(BASE_DIR, "photo.jpg")

    # find the right message object to reply to
    if update.message:
        with open(photo_path, "rb") as photo:
            await update.message.reply_photo(photo=photo, caption=caption, reply_markup=cancel_btn)
        await update.message.reply_text("Если планы изменятся — нажми кнопку выше 👆", reply_markup=MAIN_MENU)
    else:
        with open(photo_path, "rb") as photo:
            await context.bot.send_photo(chat_id=user.id, photo=photo, caption=caption, reply_markup=cancel_btn)
        await context.bot.send_message(chat_id=user.id, text="Если планы изменятся — нажми кнопку выше 👆", reply_markup=MAIN_MENU)

    owner_msg = (
        f"🆕 Новая регистрация!\n\n"
        f"Имя: {name}\n"
        f"Дата: {chosen_date}\n"
        f"Дистанция: {distance}\n"
        f"Telegram: @{user.username or '—'}\n"
        f"ID: {user.id}"
    )
    await context.bot.send_message(chat_id=OWNER_ID, text=owner_msg)

    if distance in ("8–10 км", "Свой вариант"):
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"⚡ {name} хочет бежать {distance} — возможно, стоит написать лично!\n@{user.username or str(user.id)}",
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
        reg_date = reg[3] if len(reg) > 3 else (reg[2] if len(reg) > 2 else "—")
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
            ASK_DISTANCE: [CallbackQueryHandler(received_distance, pattern="^dist_")],
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
