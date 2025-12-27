import json
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, executor, types
from config import TOKEN, MANAGERS

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

STORAGE = "storage.json"
WAITING_FOR_ADDRESS = set()


# ---------- helpers ----------

def is_manager(user_id: int) -> bool:
    return user_id in MANAGERS


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


def detect_zone(address: str) -> str:
    a = address.lower()

    if "троєщ" in a:
        return "4 зона (червона, лівий берег)"
    if "лівобереж" in a or "дарниц" in a:
        return "3 зона (зелена, лівий берег)"
    if "оболон" in a or "мінськ" in a:
        return "2 зона (синя, правий берег)"
    return "1 зона (червона, правий берег)"


# ---------- commands ----------

@dp.message_handler(commands=["start", "info"])
async def info(msg: types.Message):
    await msg.answer(
        "🚕 Бот таксі\n\n"
        "/add — додати адресу\n"
        "/list — список на сьогодні\n"
        "/clear — очистити сьогоднішній список"
    )


@dp.message_handler(commands=["add"])
async def add_cmd(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return

    WAITING_FOR_ADDRESS.add(msg.from_user.id)
    await msg.answer("✍️ Введи адресу одним повідомленням")


@dp.message_handler(lambda msg: msg.from_user.id in WAITING_FOR_ADDRESS)
async def save_address(msg: types.Message):
    user_id = msg.from_user.id
    WAITING_FOR_ADDRESS.discard(user_id)

    address = msg.text.strip()
    zone = detect_zone(address)
    day = current_day()

    data = load_data()
    data.setdefault(day, [])
    data[day].append({
        "address": address,
        "zone": zone
    })

    save_data(data)

    await msg.answer(f"✅ Додано:\n{address}\n📍 {zone}")


@dp.message_handler(commands=["list"])
async def list_cmd(msg: types.Message):
    day = current_day()
    data = load_data()

    if day not in data or not data[day]:
        await msg.answer("📭 Список порожній")
        return

    text = "📋 Адреси на сьогодні:\n\n"
    for i, item in enumerate(data[day], 1):
        text += f"{i}. {item['address']} — {item['zone']}\n"

    await msg.answer(text)


@dp.message_handler(commands=["clear"])
async def clear_cmd(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return

    data = load_data()
    data[current_day()] = []
    save_data(data)

    await msg.answer("🗑 Список очищено")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
