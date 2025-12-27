import json
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, executor, types
from config import TOKEN, MANAGERS

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

STORAGE_FILE = "storage.json"


# ---------- utils ----------
def load_data():
    if not os.path.exists(STORAGE_FILE):
        return {"addresses": {}, "managers": list(MANAGERS)}
    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def today():
    return datetime.now().strftime("%Y-%m-%d")


def is_manager(user_id: int) -> bool:
    data = load_data()
    return user_id in data["managers"]


# ---------- start ----------
@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    await msg.answer("🤖 Бот працює")


# ---------- ADD ADDRESS ----------
@dp.message_handler(commands=["add"])
async def add_address(msg: types.Message):
    if not is_manager(msg.from_user.id):
        await msg.answer("⛔ Ти не менеджер")
        return

    await msg.answer("✍️ Напиши адресу одним повідомленням")

    @dp.message_handler(lambda m: m.text and not m.text.startswith("/"))
    async def save_address(m: types.Message):
        data = load_data()
        day = today()

        if day not in data["addresses"]:
            data["addresses"][day] = []

        data["addresses"][day].append({
            "address": m.text,
            "added_by": m.from_user.id
        })

        save_data(data)
        await m.answer("✅ Адресу додано")

        dp.message_handlers.unregister(save_address)


# ---------- LIST ----------
@dp.message_handler(commands=["list"])
async def list_addresses(msg: types.Message):
    data = load_data()
    day = today()

    if day not in data["addresses"] or not data["addresses"][day]:
        await msg.answer("📭 Список порожній")
        return

    text = "📋 Адреси на сьогодні:\n\n"
    for i, item in enumerate(data["addresses"][day], 1):
        text += f"{i}. {item['address']}\n"

    await msg.answer(text)


# ---------- ADD MANAGER ----------
@dp.message_handler(commands=["addman"])
async def add_manager(msg: types.Message):
    if not is_manager(msg.from_user.id):
        await msg.answer("⛔ Ти не менеджер")
        return

    await msg.answer("👤 Надішли ID користувача")

    @dp.message_handler(lambda m: m.text.isdigit())
    async def save_manager(m: types.Message):
        user_id = int(m.text)
        data = load_data()

        if user_id in data["managers"]:
            await m.answer("ℹ️ Уже є менеджером")
        else:
            data["managers"].append(user_id)
            save_data(data)
            await m.answer("✅ Менеджера додано")

        dp.message_handlers.unregister(save_manager)


# ---------- DELETE MANAGER ----------
@dp.message_handler(commands=["delman"])
async def del_manager(msg: types.Message):
    if not is_manager(msg.from_user.id):
        await msg.answer("⛔ Ти не менеджер")
        return

    await msg.answer("❌ Надішли ID менеджера для видалення")

    @dp.message_handler(lambda m: m.text.isdigit())
    async def remove_manager(m: types.Message):
        user_id = int(m.text)
        data = load_data()

        if user_id not in data["managers"]:
            await m.answer("ℹ️ Такого менеджера немає")
        else:
            data["managers"].remove(user_id)
            save_data(data)
            await m.answer("🗑 Менеджера видалено")

        dp.message_handlers.unregister(remove_manager)


# ---------- LIST MANAGERS ----------
@dp.message_handler(commands=["managers"])
async def list_managers(msg: types.Message):
    data = load_data()
    text = "👥 Менеджери:\n\n"
    for m in data["managers"]:
        text += f"- `{m}`\n"
    await msg.answer(text, parse_mode="Markdown")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
