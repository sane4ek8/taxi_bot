import json
import os
import re
from aiogram import Bot, Dispatcher, executor, types

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

DATA_FILE = "data.json"
MAN_FILE = "managers.json"


# ---------- utils ----------
def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_manager(user_id):
    managers = load_json(MAN_FILE, [])
    return user_id in managers


# ---------- zones ----------
ZONES = {
    1: {"stations": [
        "академмістечко", "житомирська", "святошин", "ниивки",
        "берестейська", "шулявська", "політехнічний інститут",
        "вокзальна", "університет", "театральна",
        "хрещатик", "арсенальна"
    ]},
    2: {"stations": [
        "героїв дніпра", "мінська", "оболонь", "почайна",
        "тарса шевченка", "контрактова площа", "поштова площа",
        "майдан незалежності", "площа українських героїв",
        "олімпійська", "палац україна", "либідська",
        "деміївська", "голосіївська", "васильківська",
        "виставковий центр", "іподром", "теремки"
    ]},
    3: {"stations": [
        "дніпро", "гідропарк", "лівобережна",
        "дарниця", "чернігівська", "лісова",
        "троєщина"
    ]},
    4: {"stations": [
        "славутич", "осокорки", "позняки",
        "харківська", "вирлиця", "бориспільська",
        "червоний хутір"
    ]}
}


def detect_zone(station):
    s = station.lower()
    for zone, data in ZONES.items():
        if s in data["stations"]:
            return zone
    return None


# ---------- commands ----------
@dp.message_handler(commands=["start", "info"])
async def info(msg: types.Message):
    await msg.answer(
        "🤖 Бот працює\n\n"
        "Команди:\n"
        "/add — Додавання адреси\n"
        "/del — Видалення адреси\n"
        "/list — Список адрес\n"
        "/add_Man — Додати менеджера\n"
        "/del_Man — Видалити менеджера\n"
        "/info — Список команд"
    )


@dp.message_handler(commands=["add"])
async def add_hint(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return
    await msg.answer(
        "✍️ Введи адресу у форматі:\n"
        "Імʼя - адреса (станція метро)\n\n"
        "Приклад:\n"
        "Головко - проспект Петра Григоренка 14 (Позняки)"
    )


@dp.message_handler(lambda m: "-" in m.text and "(" in m.text and ")" in m.text)
async def handle_add(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return

    try:
        name, rest = msg.text.split("-", 1)
        address, station = re.findall(r"(.*)\((.*)\)", rest)[0]
    except:
        await msg.answer("❌ Невірний формат")
        return

    zone = detect_zone(station.strip())
    if not zone:
        await msg.answer("❌ Не зміг визначити зону за станцією метро")
        return

    data = load_json(DATA_FILE, {})
    data.setdefault(str(zone), []).append({
        "name": name.strip(),
        "address": address.strip(),
        "station": station.strip()
    })
    save_json(DATA_FILE, data)

    await msg.answer(f"✅ Додано до зони {zone}")


@dp.message_handler(commands=["list"])
async def list_addresses(msg: types.Message):
    data = load_json(DATA_FILE, {})
    if not data:
        await msg.answer("📭 Список порожній")
        return

    text = ""
    for zone in sorted(data, key=int):
        text += f"\n🚗 Зона {zone}:\n"
        for i, item in enumerate(data[zone], 1):
            text += f"{i}. {item['name']} — {item['address']} ({item['station']})\n"

    await msg.answer(text)


@dp.message_handler(commands=["add_Man"])
async def add_manager(msg: types.Message):
    managers = load_json(MAN_FILE, [])
    managers.append(msg.from_user.id)
    save_json(MAN_FILE, list(set(managers)))
    await msg.answer("✅ Ти доданий як менеджер")


@dp.message_handler(commands=["del_Man"])
async def del_manager(msg: types.Message):
    managers = load_json(MAN_FILE, [])
    if msg.from_user.id in managers:
        managers.remove(msg.from_user.id)
        save_json(MAN_FILE, managers)
    await msg.answer("❌ Менеджера видалено")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
