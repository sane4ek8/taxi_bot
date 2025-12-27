import json
import datetime
from aiogram import Bot, Dispatcher, executor, types
from config import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

STORAGE_FILE = "storage.json"


# ---------- helpers ----------

def load_storage():
    try:
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"managers": [], "data": {}}


def save_storage(storage):
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(storage, f, ensure_ascii=False, indent=2)


def is_manager(user_id: int) -> bool:
    storage = load_storage()
    return user_id in storage.get("managers", [])


def today():
    return datetime.date.today().isoformat()


# ---------- commands ----------

@dp.message_handler(commands=["start", "info"])
async def info(msg: types.Message):
    text = (
        "✅ Бот працює\n\n"
        "Команди:\n"
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
        return await msg.answer("⛔ У тебе немає прав")

    await msg.answer(
        "✍️ Введи адресу у форматі:\n"
        "`Адреса | Зона`",
        parse_mode="Markdown"
    )


@dp.message_handler(lambda m: "|" in m.text)
async def save_address(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return

    try:
        address, zone = map(str.strip, msg.text.split("|", 1))
    except:
        return

    storage = load_storage()
    day = today()

    storage["data"].setdefault(day, [])
    storage["data"][day].append({
        "address": address,
        "zone": zone
    })

    save_storage(storage)
    await msg.answer("✅ Адресу додано")


@dp.message_handler(commands=["list"])
async def list_addresses(msg: types.Message):
    storage = load_storage()
    day = today()

    if day not in storage["data"] or not storage["data"][day]:
        return await msg.answer("📭 Список порожній")

    text = "📋 Адреси на сьогодні:\n\n"
    for i, item in enumerate(storage["data"][day], 1):
        text += f"{i}. {item['address']} — {item['zone']}\n"

    await msg.answer(text)


@dp.message_handler(commands=["del"])
async def delete_address(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return await msg.answer("⛔ У тебе немає прав")

    storage = load_storage()
    day = today()

    if day not in storage["data"] or not storage["data"][day]:
        return await msg.answer("📭 Немає що видаляти")

    await msg.answer("✍️ Введи номер адреси для видалення")


@dp.message_handler(lambda m: m.text.isdigit())
async def confirm_delete(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return

    storage = load_storage()
    day = today()

    idx = int(msg.text) - 1

    if day not in storage["data"]:
        return

    if idx < 0 or idx >= len(storage["data"][day]):
        return await msg.answer("❌ Невірний номер")

    removed = storage["data"][day].pop(idx)
    save_storage(storage)

    await msg.answer(f"🗑 Видалено: {removed['address']}")


# ---------- managers ----------

@dp.message_handler(commands=["add_Man"])
async def add_manager(msg: types.Message):
    if not is_manager(msg.from_user.id) and load_storage()["managers"]:
        return await msg.answer("⛔ У тебе немає прав")

    await msg.answer("✍️ Надішли Telegram ID менеджера")


@dp.message_handler(lambda m: m.text.isdigit())
async def save_manager(msg: types.Message):
    storage = load_storage()
    user_id = int(msg.text)

    if user_id in storage["managers"]:
        return await msg.answer("ℹ️ Менеджер вже існує")

    storage["managers"].append(user_id)
    save_storage(storage)

    await msg.answer("✅ Менеджера додано")


@dp.message_handler(commands=["del_Man"])
async def delete_manager(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return await msg.answer("⛔ У тебе немає прав")

    await msg.answer("✍️ Надішли Telegram ID менеджера для видалення")


@dp.message_handler(lambda m: m.text.isdigit())
async def remove_manager(msg: types.Message):
    storage = load_storage()
    user_id = int(msg.text)

    if user_id not in storage["managers"]:
        return await msg.answer("❌ Такого менеджера немає")

    storage["managers"].remove(user_id)
    save_storage(storage)

    await msg.answer("🗑 Менеджера видалено")


# ---------- start ----------

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
