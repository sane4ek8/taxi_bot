import json
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, executor, types

from config import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

STORAGE_FILE = "storage.json"


# ---------- helpers ----------
def load_storage():
    if not os.path.exists(STORAGE_FILE):
        return {"managers": [], "data": {}}
    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_storage(data):
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_manager(user_id: int) -> bool:
    storage = load_storage()
    return user_id in storage.get("managers", [])


def today():
    return datetime.now().strftime("%Y-%m-%d")


# ---------- commands ----------
@dp.message_handler(commands=["start", "info"])
async def info(msg: types.Message):
    text = (
        "✅ *Бот працює*\n\n"
        "Команди:\n"
        "/add — Додавання адреси\n"
        "/list — Список адрес\n"
        "/add_Man — Додавання менеджера\n"
        "/del_Man — Видалення менеджера\n"
        "/info — Список команд"
    )
    await msg.answer(text, parse_mode="Markdown")


@dp.message_handler(commands=["add"])
async def add_address(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return await msg.answer("⛔ Ти не менеджер")

    await msg.answer("✍️ Надішли адресу одним повідомленням")

    @dp.message_handler(lambda m: m.from_user.id == msg.from_user.id)
    async def save_address(m: types.Message):
        storage = load_storage()
        day = today()
        storage["data"].setdefault(day, [])
        storage["data"][day].append(m.text)
        save_storage(storage)

        await m.answer("✅ Адресу додано")
        dp.message_handlers.unregister(save_address)


@dp.message_handler(commands=["list"])
async def list_addresses(msg: types.Message):
    storage = load_storage()
    day = today()
    items = storage.get("data", {}).get(day, [])

    if not items:
        return await msg.answer("📭 Список порожній")

    text = "📋 *Адреси на сьогодні:*\n\n"
    for i, addr in enumerate(items, 1):
        text += f"{i}. {addr}\n"

    await msg.answer(text, parse_mode="Markdown")


@dp.message_handler(commands=["add_Man"])
async def add_manager(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return await msg.answer("⛔ Ти не менеджер")

    await msg.answer("👤 Надішли Telegram ID менеджера")

    @dp.message_handler(lambda m: m.from_user.id == msg.from_user.id)
    async def save_manager(m: types.Message):
        try:
            new_id = int(m.text)
        except ValueError:
            return await m.answer("❌ ID має бути числом")

        storage = load_storage()
        if new_id in storage["managers"]:
            await m.answer("ℹ️ Він вже менеджер")
        else:
            storage["managers"].append(new_id)
            save_storage(storage)
            await m.answer("✅ Менеджера додано")

        dp.message_handlers.unregister(save_manager)


@dp.message_handler(commands=["del_Man"])
async def del_manager(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return await msg.answer("⛔ Ти не менеджер")

    await msg.answer("🗑 Надішли Telegram ID менеджера для видалення")

    @dp.message_handler(lambda m: m.from_user.id == msg.from_user.id)
    async def remove_manager(m: types.Message):
        try:
            rem_id = int(m.text)
        except ValueError:
            return await m.answer("❌ ID має бути числом")

        storage = load_storage()
        if rem_id not in storage["managers"]:
            await m.answer("ℹ️ Такого менеджера нема")
        else:
            storage["managers"].remove(rem_id)
            save_storage(storage)
            await m.answer("✅ Менеджера видалено")

        dp.message_handlers.unregister(remove_manager)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
