import json
from datetime import datetime
from aiogram import Bot, Dispatcher, executor, types
from config import TOKEN, STORAGE_FILE

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


# ---------- helpers ----------

def load_storage():
    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_storage(data):
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def current_day():
    return datetime.now().strftime("%Y-%m-%d")


def is_manager(user_id: int) -> bool:
    storage = load_storage()
    return user_id in storage.get("managers", [])


# ---------- commands ----------

@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    await msg.answer("🚕 Бот працює\nКоманди: /add /list /addMan /delMan")


@dp.message_handler(commands=["list"])
async def list_addresses(msg: types.Message):
    storage = load_storage()
    day = current_day()

    if day not in storage["data"] or not storage["data"][day]:
        await msg.answer("📭 Список порожній")
        return

    text = "📋 Адреси на сьогодні:\n\n"
    for i, item in enumerate(storage["data"][day], 1):
        text += f"{i}. {item}\n"

    await msg.answer(text)


@dp.message_handler(commands=["add"])
async def add_address(msg: types.Message):
    if not is_manager(msg.from_user.id):
        await msg.answer("⛔ Ти не менеджер")
        return

    await msg.answer("✍️ Надішли адресу одним повідомленням")
    dp.register_message_handler(save_address, state=None, content_types=types.ContentTypes.TEXT)


async def save_address(msg: types.Message):
    storage = load_storage()
    day = current_day()

    storage["data"].setdefault(day, [])
    storage["data"][day].append(msg.text)

    save_storage(storage)
    await msg.answer("✅ Адресу додано")
    dp.message_handlers.unregister(save_address)


# ---------- managers ----------

@dp.message_handler(commands=["addMan"])
async def add_manager(msg: types.Message):
    if not is_manager(msg.from_user.id):
        await msg.answer("⛔ Ти не менеджер")
        return

    try:
        new_id = int(msg.get_args())
    except:
        await msg.answer("❗ Використання: /addMan 123456789")
        return

    storage = load_storage()

    if new_id in storage["managers"]:
        await msg.answer("ℹ️ Цей користувач вже менеджер")
        return

    storage["managers"].append(new_id)
    save_storage(storage)
    await msg.answer("✅ Менеджера додано")


@dp.message_handler(commands=["delMan"])
async def del_manager(msg: types.Message):
    if not is_manager(msg.from_user.id):
        await msg.answer("⛔ Ти не менеджер")
        return

    try:
        rem_id = int(msg.get_args())
    except:
        await msg.answer("❗ Використання: /delMan 123456789")
        return

    storage = load_storage()

    if rem_id not in storage["managers"]:
        await msg.answer("ℹ️ Цей користувач не менеджер")
        return

    storage["managers"].remove(rem_id)
    save_storage(storage)
    await msg.answer("🗑 Менеджера видалено")


# ---------- run ----------

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
