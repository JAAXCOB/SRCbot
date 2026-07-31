import os
import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

BOT_TOKEN = os.environ["BOT_TOKEN"]

MESSAGE = """🏃 Дополнительная пробежка!

В эту субботу, 1 августа, выходим на утреннюю пробежку:

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
            await bot.send_message(chat_id=uid, text=MESSAGE, reply_markup=keyboard)
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
