import json
import os
from aiogram import Bot, Dispatcher, executor, types

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

STORAGE = "storage.json"


# ---------- utils ----------

def load_data():
    if not os.path.exists(STORAGE):
        return {"addresses": [], "managers": []}
    with open(STORAGE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(STORAGE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_manager(user_id):
    data = load_data()
    return user_id in data["managers"]


# ---------- metro → zones ----------

METRO_ZONES = {
    # Зона 1 — червона, правий берег
    "академмістечко": 1,
    "житомирська": 1,
    "святошин": 1,
    "нивки": 1,
    "берестейська": 1,
    "шулявська": 1,
    "політехнічний інститут": 1,
    "вокзальна": 1,

    # Зона 2 — синя, правий берег
    "героїв дніпра": 2,
    "мінська": 2,
    "оболонь": 2,
    "почайна": 2,
    "контрактова площа": 2,
    "поштова площа": 2,

    # Зона 3 — червона, лівий берег
    "дарниця": 3,
    "лівобережна": 3,
    "чернігівська": 3,
    "лісова": 3,
    "троєщина": 3,

    # Зона 4 — зелена, лівий берег
    "славутич": 4,
    "позняки": 4,
    "осокорки": 4,
    "харківська": 4,
    "вирлиця": 4,
    "бориспільська": 4,
    "червоний хутір": 4,
}


def detect_zone(address: str):
    address = address.lower()
    for station, zone in METRO_ZONES.items():
        if station in address:
            return zone
    return "❓ Невідома зона"


# ---------- commands ----------

@dp.message_handler(commands=["info", "start"])
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


@dp.message_handler(commands=["add"])
async def add_address(msg: types.Message):
    if not is_manager(msg.from_user.id):
        await msg.answer("❌ Ви не менеджер")
        return

    await msg.answer("✍️ Введи у форматі:\nІмʼя, адреса")


@dp.message_handler(lambda m: "," in m.text and is_manager(m.from_user.id))
async def save_address(msg: types.Message):
    name, address = map(str.strip, msg.text.split(",", 1))
    zone = detect_zone(address)

    data = load_data()
    data["addresses"].append({
        "name": name,
        "address": address,
        "zone": zone
    })
    save_data(data)

    await msg.answer(f"✅ Додано\n🚗 Зона: {zone}")


@dp.message_handler(commands=["list"])
async def list_addresses(msg: types.Message):
    data = load_data()
    if not data["addresses"]:
        await msg.answer("📭 Список порожній")
        return

    grouped = {}
    for item in data["addresses"]:
        grouped.setdefault(item["zone"], []).append(item)

    text = ""
    for zone, items in grouped.items():
        text += f"\n🚗 Машина — Зона {zone}\n"
        for i, a in enumerate(items, 1):
            text += f"{i}. {a['name']} — {a['address']}\n"

    await msg.answer(text)


@dp.message_handler(commands=["del"])
async def delete_address(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return

    data = load_data()
    if not data["addresses"]:
        await msg.answer("Список порожній")
        return

    text = "Введи номер адреси:\n"
    for i, a in enumerate(data["addresses"], 1):
        text += f"{i}. {a['name']} — {a['address']}\n"

    await msg.answer(text)
    dp.register_message_handler(confirm_delete, state=None)


async def confirm_delete(msg: types.Message):
    if not msg.text.isdigit():
        return
    idx = int(msg.text) - 1

    data = load_data()
    if 0 <= idx < len(data["addresses"]):
        removed = data["addresses"].pop(idx)
        save_data(data)
        await msg.answer(f"🗑 Видалено: {removed['name']}")


@dp.message_handler(commands=["add_Man"])
async def add_manager(msg: types.Message):
    data = load_data()
    if msg.from_user.id not in data["managers"] and data["managers"]:
        await msg.answer("❌ Тільки менеджер може додавати інших")
        return

    await msg.answer("Введи Telegram ID менеджера")


@dp.message_handler(lambda m: m.text.isdigit())
async def save_manager(msg: types.Message):
    data = load_data()
    uid = int(msg.text)

    if uid not in data["managers"]:
        data["managers"].append(uid)
        save_data(data)
        await msg.answer("✅ Менеджера додано")


@dp.message_handler(commands=["del_Man"])
async def del_manager(msg: types.Message):
    data = load_data()
    await msg.answer("Введи Telegram ID для видалення")


@dp.message_handler()
async def remove_manager(msg: types.Message):
    if not msg.text.isdigit():
        return

    uid = int(msg.text)
    data = load_data()

    if uid in data["managers"]:
        data["managers"].remove(uid)
        save_data(data)
        await msg.answer("🗑 Менеджера видалено")


if __name__ == "__main__":
    executor.start_polling(dp)

