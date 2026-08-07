import os
import asyncio
from datetime import date, timedelta
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

BOT_TOKEN = os.environ["BOT_TOKEN"]

MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
}


def next_saturday_label() -> str:
    today = date.today()
    days_until_sat = (5 - today.weekday()) % 7
    if days_until_sat == 0:
        days_until_sat = 7
    sat = today + timedelta(days=days_until_sat)
    return f"{sat.day} {MONTHS_RU[sat.month]}"


def build_message() -> str:
    sat = next_saturday_label()
    return f"""🏃 Субботняя пробежка!

В эту субботу, {sat}, выходим на утреннюю пробежку:

📍 Место сбора: кофейня AMO, Мичуринский проспект, 56
🕙 Сбор: 10:00 | Старт: 10:30
🗺 Маршрут: Парк Событие, ~5 км
💸 Участие: бесплатно

Темп — комфортный, без требований к подготовке.
С нами бегает фотограф — снимки пришлём после 📸

Записывайся ниже 👇"""


async def send_to(user_ids: list[int]):
    bot = Bot(token=BOT_TOKEN)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Зарегистрироваться 👟", url="https://t.me/skyrunnersclub_bot?start=saturday")]
    ])
    for uid in user_ids:
        try:
            await bot.send_message(chat_id=uid, text=build_message(), reply_markup=keyboard)
            print(f"✅ Отправлено: {uid}")
        except Exception as e:
            print(f"❌ Ошибка {uid}: {e}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        ids = [int(x) for x in sys.argv[1:]]
    else:
        ids = [1237520343]  # по умолчанию — только владелец
    asyncio.run(send_to(ids))
