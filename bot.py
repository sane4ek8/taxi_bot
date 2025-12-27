import json
import os
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

from config import TOKEN, MANAGERS

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

STORAGE_FILE = "storage.json"
MAX_IN_CAR = 4


# ---------- ДОПОМІЖНЕ ----------

def load_data():
    if not os.path.exists(STORAGE_FILE):
        return {}
    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def current_day():
    now = datetime.now()
    if now.hour < 2:
        now -= timedelta(days=1)
    return now.strftime("%Y-%m-%d")


def is_manager(user_id):
    return user_id in MANAGERS


# ---------- ВИЗНАЧЕННЯ ЗОНИ ----------

def detect_zone(address: str) -> str:
    a = address.lower()

    # Лівий берег
    if any(x in a for x in ["троєщина", "закревського", "милославська"]):
        return "Зона 4 (лівий берег, червона гілка)"
    if any(x in a for x in ["харківське", "позняки", "осокорки", "дарниця"]):
        return "Зона 3 (лівий берег, зелена гілка)"

    # Правий берег
    if any(x in a for x in ["борщаг", "академ", "святошин", "ніволки"]):
        return "Зона 1 (правий берег, червона гілка)"
    if any(x in a for x in ["оболонь", "печерськ", "голосіїв"]):
        return "Зона 2 (правий берег, синя гілка)"

    return "Зона 1 (правий берег, червона гілка)"


# ---------- КОМАНДИ ----------

@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    await msg.answer(
        "🤖 Бот таксі\n\n"
        "Команди:\n"
        "/add — додати адресу\n"
        "/del — видалити адресу\n"
        "/list — список адрес\n"
        "/cars — По машинам 🚕\n"
        "/info — допомога"
    )


@dp.message_handler(commands=["info"])
async def info(msg: types.Message):
    await msg.answer(
        "📌 Доступні команди:\n"
        "/add — додати адресу (менеджер)\n"
        "/del — видалити адресу (менеджер)\n"
        "/list — список на сьогодні\n"
        "/cars — сформувати таксі\n\n"
        "Новий день починається о 02:00"
    )


@dp.message_handler(commands=["add"])
async def add_address(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return

    await msg.answer("✍️ Введи адресу одним повідомленням")


@dp.message_handler(lambda m: not m.text.startswith("/"))
async def handle_text(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return

    day = current_day()
    data = load_data()
    data.setdefault(day, [])

    zone = detect_zone(msg.text)

    data[day].append({
        "address": msg.text,
        "zone": zone
    })

    save_data(data)

    await msg.answer(f"✅ Додано\n📍 {msg.text}\n🗺 {zone}")


@dp.message_handler(commands=["list"])
async def list_addresses(msg: types.Message):
    day = current_day()
    data = load_data()

    if day not in data or not data[day]:
        await msg.answer("Список порожній")
        return

    text = "📋 Адреси на сьогодні:\n\n"
    for i, item in enumerate(data[day], 1):
        text += f"{i}. {item['address']} — {item['zone']}\n"

    await msg.answer(text)


@dp.message_handler(commands=["del"])
async def delete_address(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return

    day = current_day()
    data = load_data()

    if day not in data or not data[day]:
        await msg.answer("Немає що видаляти")
        return

    text = "❌ Вибери номер для видалення:\n"
    for i, item in enumerate(data[day], 1):
        text += f"{i}. {item['address']}\n"

    await msg.answer(text)


@dp.message_handler(commands=["cars"])
async def cars(msg: types.Message):
    day = current_day()
    data = load_data()

    if day not in data or not data[day]:
        await msg.answer("Немає адрес")
        return

    zones = {}
    for item in data[day]:
        zones.setdefault(item["zone"], []).append(item["address"])

    result = "🚕 По машинам 🚕\n\n"
    car_num = 1

    for zone, addresses in zones.items():
        for i in range(0, len(addresses), MAX_IN_CAR):
            group = addresses[i:i + MAX_IN_CAR]
            result += f"🚕 Машина {car_num} ({zone}):\n"
            for addr in group:
                result += f"• {addr}\n"
            result += "\n"
            car_num += 1

    await msg.answer(result)


if __name__ == "__main__":
    executor.start_polling(dp)
