import json
import os
from datetime import date
from aiogram import Bot, Dispatcher, executor, types

TOKEN = os.getenv("BOT_TOKEN")  # Railway ENV
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

STORAGE = "storage.json"


# ---------- helpers ----------
def load():
    with open(STORAGE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(data):
    with open(STORAGE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def today():
    return str(date.today())


def is_manager(uid):
    return uid in load()["managers"]


def detect_zone(text: str):
    text = text.lower()
    for zone, stations in METRO_ZONES.items():
        for st in stations:
            if st in text:
                return zone
    return None


# ---------- commands ----------
@dp.message_handler(commands=["start", "info"])
async def info(msg: types.Message):
    await msg.answer(
        "🤖 Бот працює\n\n"
        "Команди:\n"
        "/add – Додавання адреси\n"
        "/list – Список адрес\n"
        "/del – Видалення адреси\n"
        "/add_Man – Додати менеджера\n"
        "/del_Man – Видалити менеджера\n"
        "/info – Список команд\n\n"
        "Формат адреси:\n"
        "Імʼя - адреса (станція метро)"
    )


@dp.message_handler(commands=["add"])
async def add(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return
    await msg.answer(
        "✍️ Введи адресу одним повідомленням\n"
        "Приклад:\n"
        "Головко - проспект Петра Григоренка 14 (Позняки)"
    )


@dp.message_handler(lambda m: "-" in m.text)
async def catch_address(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return

    zone = detect_zone(msg.text)
    if not zone:
        await msg.answer("❌ Не можу визначити зону (немає станції метро)")
        return

    data = load()
    day = today()
    data["data"].setdefault(day, [])
    data["data"][day].append({
        "text": msg.text,
        "zone": zone
    })
    save(data)

    await msg.answer(f"✅ Додано (зона {zone})")


@dp.message_handler(commands=["list"])
async def list_cmd(msg: types.Message):
    data = load()
    day = today()

    if day not in data["data"] or not data["data"][day]:
        await msg.answer("📭 Список порожній")
        return

    text = "📋 Адреси по зонах:\n\n"
    for zone in range(1, 5):
        items = [a for a in data["data"][day] if a["zone"] == zone]
        if items:
            text += f"🚗 Зона {zone}:\n"
            for i, a in enumerate(items, 1):
                text += f"{i}. {a['text']}\n"
            text += "\n"

    await msg.answer(text)


@dp.message_handler(commands=["del"])
async def delete(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return
    args = msg.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await msg.answer("❌ /del НОМЕР")
        return

    idx = int(args[1]) - 1
    data = load()
    day = today()

    try:
        removed = data["data"][day].pop(idx)
        save(data)
        await msg.answer(f"🗑 Видалено:\n{removed['text']}")
    except:
        await msg.answer("❌ Невірний номер")


@dp.message_handler(commands=["add_Man"])
async def add_man(msg: types.Message):
    data = load()
    uid = msg.from_user.id
    if uid not in data["managers"]:
        data["managers"].append(uid)
        save(data)
        await msg.answer("✅ Ти доданий як менеджер")


@dp.message_handler(commands=["del_Man"])
async def del_man(msg: types.Message):
    data = load()
    uid = msg.from_user.id
    if uid in data["managers"]:
        data["managers"].remove(uid)
        save(data)
        await msg.answer("❌ Ти більше не менеджер")


if __name__ == "__main__":
    executor.start_polling(dp)
