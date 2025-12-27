import json
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, executor, types
from config import TOKEN, MANAGERS

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

DATA_FILE = "storage.json"


# ---------- helpers ----------

def current_day():
    return datetime.now().strftime("%Y-%m-%d")


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_manager(user_id: int) -> bool:
    data = load_data()
    managers = set(data.get("managers", [])) | MANAGERS
    return user_id in managers


# ---------- commands ----------

@dp.message_handler(commands=["start", "info"])
async def info(msg: types.Message):
    text = (
        "🤖 Бот працює\n\n"
        "📌 Команди:\n"
        "/add — Додавання адреси\n"
        "/del — Видалення адреси\n"
        "/list — Список адрес\n"
        "/add_Man — Додавання менеджера\n"
        "/del_Man — Видалення менеджера\n"
        "/info — Список команд"
    )
    await msg.answer(text)


# ---------- addresses ----------

@dp.message_handler(commands=["add"])
async def add_address(msg: types.Message):
    if not is_manager(msg.from_user.id):
        await msg.answer("⛔ Ти не менеджер")
        return

    await msg.answer("✍️ Введи адресу одним повідомленням")
    await AddAddress.waiting.set()


class AddAddress(types.states.StatesGroup):
    waiting = types.states.State()


@dp.message_handler(state=AddAddress.waiting)
async def save_address(msg: types.Message, state):
    day = current_day()
    data = load_data()

    data.setdefault(day, [])
    data[day].append({
        "address": msg.text
    })

    save_data(data)
    await state.finish()
    await msg.answer("✅ Адресу додано")


@dp.message_handler(commands=["list"])
async def list_addresses(msg: types.Message):
    day = current_day()
    data = load_data()

    if day not in data or not data[day]:
        await msg.answer("📭 Список порожній")
        return

    text = "📋 Адреси на сьогодні:\n\n"
    for i, item in enumerate(data[day], 1):
        text += f"{i}. {item['address']}\n"

    await msg.answer(text)


@dp.message_handler(commands=["del"])
async def delete_address(msg: types.Message):
    if not is_manager(msg.from_user.id):
        await msg.answer("⛔ Ти не менеджер")
        return

    await msg.answer("❌ Введи номер адреси зі списку")
    await DeleteAddress.waiting.set()


class DeleteAddress(types.states.StatesGroup):
    waiting = types.states.State()


@dp.message_handler(state=DeleteAddress.waiting)
async def remove_address(msg: types.Message, state):
    if not msg.text.isdigit():
        await msg.answer("⚠️ Потрібно ввести номер")
        return

    index = int(msg.text) - 1
    day = current_day()
    data = load_data()

    if day not in data or index >= len(data[day]):
        await msg.answer("❌ Невірний номер")
        return

    removed = data[day].pop(index)
    save_data(data)

    await state.finish()
    await msg.answer(f"🗑 Видалено: {removed['address']}")


# ---------- managers ----------

@dp.message_handler(commands=["add_Man"])
async def add_manager(msg: types.Message):
    if not is_manager(msg.from_user.id):
        await msg.answer("⛔ Ти не менеджер")
        return

    await msg.answer("👤 Введи Telegram ID менеджера")
    await AddManager.waiting.set()


class AddManager(types.states.StatesGroup):
    waiting = types.states.State()


@dp.message_handler(state=AddManager.waiting)
async def save_manager(msg: types.Message, state):
    if not msg.text.isdigit():
        await msg.answer("⚠️ ID має бути числом")
        return

    user_id = int(msg.text)
    data = load_data()

    data.setdefault("managers", [])
    if user_id not in data["managers"]:
        data["managers"].append(user_id)
        save_data(data)
        await msg.answer("✅ Менеджера додано")
    else:
        await msg.answer("ℹ️ Менеджер вже існує")

    await state.finish()


@dp.message_handler(commands=["del_Man"])
async def delete_manager(msg: types.Message):
    if not is_manager(msg.from_user.id):
        await msg.answer("⛔ Ти не менеджер")
        return

    await msg.answer("❌ Введи Telegram ID менеджера")
    await DeleteManager.waiting.set()


class DeleteManager(types.states.StatesGroup):
    waiting = types.states.State()


@dp.message_handler(state=DeleteManager.waiting)
async def remove_manager(msg: types.Message, state):
    if not msg.text.isdigit():
        await msg.answer("⚠️ ID має бути числом")
        return

    user_id = int(msg.text)
    data = load_data()

    if user_id in data.get("managers", []):
        data["managers"].remove(user_id)
        save_data(data)
        await msg.answer("🗑 Менеджера видалено")
    else:
        await msg.answer("ℹ️ Менеджера не знайдено")

    await state.finish()


# ---------- run ----------

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
