import json
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, executor, types

from config import TOKEN, MANAGERS

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

STORAGE = "storage.json"
user_states = {}  # user_id -> "waiting_address"


def current_day():
    now = datetime.now()
    if now.hour < 2:
        now = now.replace(day=now.day - 1)
    return now.strftime("%Y-%m-%d")


def load_data():
    if not os.path.exists(STORAGE):
        return {}
    with open(STORAGE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(STORAGE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_manager(user_id):
    return user_id in MANAGERS


@dp.message_handler(commands=["add"])
async def add_cmd(msg: types.Message):
    if not is_manager(msg.from_user.id):
        await msg.answer("⛔ Немає доступу")
        return
    user_states[msg.from_user.id] = "waiting_address"
    await msg.answer("✍️ Введи адресу одним повідомленням")


@dp.message_handler(lambda msg: user_states.get(msg.from_user.id) == "waiting_address")
async def save_address(msg: types.Message):
    day = current_day()
    data = load_data()

    if day not in data:
        data[day] = []

    data[day].append({
        "address": msg.text
    })

    save_data(data)
    user_states.pop(msg.from_user.id)

    await msg.answer("✅ Адресу додано")


@dp.message_handler(commands=["list"])
async def list_cmd(msg: types.Message):
    day = current_day()
    data = load_data()

    if day not in data or not data[day]:
        await msg.answer("📭 Список порожній")
        return

    text = "📋 Адреси на сьогодні:\n\n"
    for i, item in enumerate(data[day], 1):
        text += f"{i}. {item['address']}\n"

    await msg.answer(text)


@dp.message_handler(commands=["info"])
async def info_cmd(msg: types.Message):
    await msg.answer(
        "/add — додати адресу\n"
        "/list — список на сьогодні\n"
        "/info — команди"
    )


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
