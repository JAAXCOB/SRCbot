import os
import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

BOT_TOKEN = os.environ["BOT_TOKEN"]
BASE_DIR = "/opt/srcbot"

MESSAGE = """🎉 Сезон открыт!

Sky Runners Club снова начинает бегать. Ждём тебя на первой пробежке в этом сезоне!

Записывайся ниже 👇"""


async def send_reopen():
    bot = Bot(token=BOT_TOKEN)
    notify_file = os.path.join(BASE_DIR, "notify_list.txt")
    if not os.path.exists(notify_file):
        print("notify_list.txt не найден — некому отправлять.")
        return
    user_ids = [int(line.strip()) for line in open(notify_file).readlines() if line.strip()]
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Зарегистрироваться 👟", url="https://t.me/skyrunnersclub_bot")]
    ])
    for uid in user_ids:
        try:
            await bot.send_message(chat_id=uid, text=MESSAGE, reply_markup=keyboard)
            print(f"✅ Отправлено: {uid}")
        except Exception as e:
            print(f"❌ Ошибка {uid}: {e}")


if __name__ == "__main__":
    asyncio.run(send_reopen())
