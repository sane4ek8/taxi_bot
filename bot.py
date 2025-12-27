import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text

TOKEN = os.getenv("BOT_TOKEN")  # токен тільки через env
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

STORAGE_FILE = "storage.json"

# ---------- STORAGE ----------
def load_data():
    if not os.path.exists(STORAGE_FILE):
        return {"managers": [], "addresses": []}
    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_manager(user_id):
    data = load_data()
    return user_id in data["managers"]

# ---------- ZONES ----------
ZONE_MAP = {
    1: ["академмістечко", "житомирська", "святошин", "ниви", "берестейська"],
    2: ["теремки", "іподром", "васильківська", "голосіївська"],
    3: ["лісова", "чернігівська", "дарниця", "троєщина"],
    4: ["осокорки", "позняки", "харківська", "славутич"]
}

def detect_zone(text: str):
    t = text.lower()
    for zone, stations in ZONE_MAP.items():
        for s in stations:
            if s in t:
                return zone
    return None

# ---------- COMMANDS ----------
@dp.message_handler(commands=["info"])
async def info(msg: types.Message):
    await msg.answer(
        "✅ Бот працює\n\n"
        "Команди:\n"
        "/add — Додати адресу\n"
        "/list — Список адрес\n"
        "/del — Видалити адресу\n"
        "/add_Man — Додати менеджера\n"
        "/del_Man — Видалити менеджера\n"
        "/info — Команди"
    )

@dp.message_handler(commands=["add"])
async def add(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return await msg.answer("❌ Ти не менеджер")
    await msg.answer(
        "✍️ Введи адресу у форматі:\n"
        "Імʼя - адреса (найближча станція метро)\n\n"
        "Приклад:\n"
        "Іван - вул. Хрещатик 10 (Театральна)"
    )

@dp.message_handler(commands=["list"])
async def list_addresses(msg: types.Message):
    data = load_data()
    if not data["addresses"]:
        return await msg.answer("📭 Список порожній")

    text = "📋 Адреси по зонах:\n\n"
    for zone in sorted(ZONE_MAP.keys()):
        zone_items = [a for a in data["addresses"] if a["zone"] == zone]
        if not zone_items:
            continue
        text += f"🚗 Зона {zone}:\n"
        for i, a in enumerate(zone_items, 1):
            text += f"{i}. {a['name']} — {a['address']}\n"
        text += "\n"

    await msg.answer(text)

@dp.message_handler(commands=["del"])
async def delete(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return await msg.answer("❌ Ти не менеджер")
    data = load_data()
    if not data["addresses"]:
        return await msg.answer("Список порожній")
    data["addresses"].pop()
    save_data(data)
    await msg.answer("🗑 Адресу видалено")

@dp.message_handler(commands=["add_Man"])
async def add_manager(msg: types.Message):
    data = load_data()
    uid = msg.from_user.id
    if uid not in data["managers"]:
        data["managers"].append(uid)
        save_data(data)
        await msg.answer("✅ Ти доданий як менеджер")
    else:
        await msg.answer("Ти вже менеджер")

@dp.message_handler(commands=["del_Man"])
async def del_manager(msg: types.Message):
    data = load_data()
    uid = msg.from_user.id
    if uid in data["managers"]:
        data["managers"].remove(uid)
        save_data(data)
        await msg.answer("❌ Ти видалений з менеджерів")

# ---------- TEXT INPUT (ВАЖЛИВО: В КІНЦІ!) ----------
@dp.message_handler(lambda m: "-" in m.text and "(" in m.text and ")" in m.text)
async def handle_address(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return

    try:
        name, rest = msg.text.split("-", 1)
        zone = detect_zone(msg.text)
        if not zone:
            return await msg.answer("❌ Не вдалося визначити зону")

        data = load_data()
        data["addresses"].append({
            "name": name.strip(),
            "address": rest.strip(),
            "zone": zone
        })
        save_data(data)
        await msg.answer(f"✅ Додано в зону {zone}")
    except:
        await msg.answer("❌ Невірний формат")

# ---------- START ----------
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
