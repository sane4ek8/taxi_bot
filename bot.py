import json
import os
import re
from aiogram import Bot, Dispatcher, executor, types

TOKEN = os.getenv("BOT_TOKEN")  # Railway env
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

DATA_FILE = "data.json"
MANAGERS_FILE = "managers.json"


# ---------- UTILS ----------
def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_manager(user_id: int) -> bool:
    managers = load_json(MANAGERS_FILE, [])
    return user_id in managers


# ---------- METRO → ZONES ----------
ZONES = {
    1: ["академмістечко", "житомирська", "святошин", "нивки", "берестейська", "шулявська", "політехнічний інститут", "вокзальна"],
    2: ["олімпійська", "палац україна", "либі́дська", "деміївська", "голосіївська", "васильківська", "виставковий центр", "іподром", "теремки"],
    3: ["лісова", "чернігівська", "дарниця", "лівобережна", "гідропарк", "троєщина"],
    4: ["осокорки", "позняки", "харківська", "вирлиця", "бориспільська", "червоний хутір", "славутич"]
}


def detect_zone(metro: str) -> int | None:
    metro = metro.lower()
    for zone, stations in ZONES.items():
        if any(st in metro for st in stations):
            return zone
    return None


# ---------- COMMANDS ----------
@dp.message_handler(commands=["info", "start"])
async def info(msg: types.Message):
    await msg.answer(
        "🤖 Бот працює\n\n"
        "Команди:\n"
        "/add – Додавання адреси\n"
        "/del – Видалення адреси\n"
        "/list – Список адрес\n"
        "/add_Man – Додавання менеджера\n"
        "/del_Man – Видалення менеджера\n"
        "/info – Список команд\n\n"
        "Формат адреси:\n"
        "Імʼя - адреса (станція метро)"
    )


@dp.message_handler(commands=["add"])
async def add_address(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return
    await msg.answer(
        "✍️ Введи адресу у форматі:\n"
        "Імʼя - адреса (станція метро)\n\n"
        "Приклад:\n"
        "Головко - проспект Петра Григоренка 14 (Позняки)"
    )


@dp.message_handler(lambda m: "-" in m.text and "(" in m.text and ")" in m.text)
async def save_address(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return

    match = re.match(r"(.+?)\s*-\s*(.+?)\s*\((.+?)\)", msg.text)
    if not match:
        await msg.answer("❌ Невірний формат")
        return

    name, address, metro = match.groups()
    zone = detect_zone(metro)

    if not zone:
        await msg.answer("❌ Не вдалося визначити зону за станцією метро")
        return

    data = load_json(DATA_FILE, {})
    data.setdefault(str(zone), []).append({
        "name": name.strip(),
        "address": address.strip(),
        "metro": metro.strip()
    })
    save_json(DATA_FILE, data)

    await msg.answer(f"✅ Додано в зону {zone}")


@dp.message_handler(commands=["list"])
async def list_addresses(msg: types.Message):
    data = load_json(DATA_FILE, {})
    if not data:
        await msg.answer("📭 Список порожній")
        return

    text = "📋 Адреси по зонах:\n\n"
    for zone in sorted(data.keys()):
        text += f"🚕 Зона {zone}:\n"
        for i, item in enumerate(data[zone], 1):
            text += f"{i}. {item['name']} — {item['address']} ({item['metro']})\n"
        text += "\n"

    await msg.answer(text)


@dp.message_handler(commands=["del"])
async def delete_last(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return

    data = load_json(DATA_FILE, {})
    for zone in sorted(data.keys(), reverse=True):
        if data[zone]:
            data[zone].pop()
            save_json(DATA_FILE, data)
            await msg.answer("🗑 Останню адресу видалено")
            return

    await msg.answer("❌ Немає що видаляти")


@dp.message_handler(commands=["add_Man"])
async def add_manager(msg: types.Message):
    managers = load_json(MANAGERS_FILE, [])
    try:
        user_id = int(msg.get_args())
    except:
        await msg.answer("❌ Вкажи ID")
        return

    if user_id not in managers:
        managers.append(user_id)
        save_json(MANAGERS_FILE, managers)
        await msg.answer("✅ Менеджера додано")


@dp.message_handler(commands=["del_Man"])
async def del_manager(msg: types.Message):
    managers = load_json(MANAGERS_FILE, [])
    try:
        user_id = int(msg.get_args())
    except:
        await msg.answer("❌ Вкажи ID")
        return

    if user_id in managers:
        managers.remove(user_id)
        save_json(MANAGERS_FILE, managers)
        await msg.answer("🗑 Менеджера видалено")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
