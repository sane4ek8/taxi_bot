import json
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, executor, types
from config import TOKEN, MANAGERS

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

STORAGE_FILE = "storage.json"
user_states = {}  # хто зараз вводить адресу


# ---------- helpers ----------

def is_manager(user_id: int) -> bool:
    return user_id in MANAGERS


def current_day() -> str:
    now = datetime.now()
    # новий день з 02:00
    if now.hour < 2:
        now = now.replace(day=now.day - 1)
    return now.strftime("%Y-%m-%d")


def load_data():
    if not os.path.exists(STORAGE_FILE):
        return {}
    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------- commands ----------

@dp.message_handler(commands=["start", "info"])
async def info(msg: types.Message):
    await msg.answer(
        "🤖 Бот для формування таксі\n\n"
        "/add — додати адресу\n"
        "/list — показати список\n"
        "/clear — очистити список (менеджери)"
    )


@dp.message_handler(commands=["add"])
async def add_cmd(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return

    user_states[msg.from_user.id] = "waiting_address"
    await msg.answer("✍️ Надішли адресу ОДНИМ повідомленням")


@dp.message_handler(commands=["list"])
async def list_cmd(msg: types.Message):
    day = current_day()
    data = load_data()

    if day not in data or len(data[day]) == 0:
        await msg.answer("📭 Список порожній")
        return

    text = f"📋 Адреси на {day}:\n\n"
    for i, item in enumerate(data[day], 1):
        text += f"{i}. {item['address']}\n"

    await msg.answer(text)


@dp.message_handler(commands=["clear"])
async def clear_cmd(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return

    data = load_data()
    day = current_day()
    data[day] = []
    save_data(data)

    await msg.answer("🧹 Список очищено")


# ---------- address input ----------

@dp.message_handler()
async def handle_text(msg: types.Message):
    uid = msg.from_user.id

    if user_states.get(uid) != "waiting_address":
        return

    address = msg.text.strip()
    day = current_day()
    data = load_data()

    if day not in data:
        data[day] = []

    data[day].append({
        "address": address
    })

    save_data(data)
    user_states.pop(uid)

    await msg.answer(f"✅ Адресу додано:\n{address}")


# ---------- start ----------

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
