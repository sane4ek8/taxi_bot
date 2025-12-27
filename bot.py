import json
import os
from aiogram import Bot, Dispatcher, executor, types
from config import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

STORAGE_FILE = "storage.json"

# ---------- helpers ----------

def load_storage():
    if not os.path.exists(STORAGE_FILE):
        return {"managers": [], "addresses": []}
    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_storage(data):
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_manager(user_id: int) -> bool:
    data = load_storage()
    return user_id in data["managers"]

# ---------- zones ----------

ZONE_1 = ["Академмістечко", "Житомирська", "Святошин"]
ZONE_2 = ["Героїв Дніпра", "Мінська", "Оболонь"]
ZONE_3 = ["Лісова", "Чернігівська", "Дарниця", "Троєщина"]
ZONE_4 = ["Славутич", "Осокорки", "Позняки", "Харківська"]

def detect_zone(text: str) -> str:
    t = text.lower()
    for s in ZONE_1:
        if s.lower() in t:
            return "Зона 1 (червона, правий берег)"
    for s in ZONE_2:
        if s.lower() in t:
            return "Зона 2 (синя, правий берег)"
    for s in ZONE_3:
        if s.lower() in t:
            return "Зона 3 (червона, лівий берег)"
    for s in ZONE_4:
        if s.lower() in t:
            return "Зона 4 (зелена, лівий берег)"
    return "❓ Невідома зона"

# ---------- commands ----------

@dp.message_handler(commands=["start", "info"])
async def info(msg: types.Message):
    text = (
        "✅ Бот працює\n\n"
        "Команди:\n"
        "/add — Додавання адреси\n"
        "/del — Видалення адреси\n"
        "/list — Список адрес\n"
        "/add_Man — Додати менеджера\n"
        "/del_Man — Видалити менеджера\n"
        "/info — Список команд"
    )
    await msg.answer(text)

# ---------- managers ----------

@dp.message_handler(commands=["add_Man"])
async def add_manager(msg: types.Message):
    data = load_storage()

    if data["managers"] and msg.from_user.id not in data["managers"]:
        await msg.answer("⛔ Ти не менеджер")
        return

    parts = msg.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await msg.answer("Формат: /add_Man 123456789")
        return

    uid = int(parts[1])
    if uid not in data["managers"]:
        data["managers"].append(uid)
        save_storage(data)
        await msg.answer("✅ Менеджера додано")
    else:
        await msg.answer("ℹ️ Він вже менеджер")

@dp.message_handler(commands=["del_Man"])
async def del_manager(msg: types.Message):
    data = load_storage()

    if msg.from_user.id not in data["managers"]:
        await msg.answer("⛔ Ти не менеджер")
        return

    parts = msg.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await msg.answer("Формат: /del_Man 123456789")
        return

    uid = int(parts[1])
    if uid in data["managers"]:
        data["managers"].remove(uid)
        save_storage(data)
        await msg.answer("🗑 Менеджера видалено")
    else:
        await msg.answer("❌ Немає такого менеджера")

# ---------- addresses ----------

@dp.message_handler(commands=["add"])
async def add_address(msg: types.Message):
    if not is_manager(msg.from_user.id):
        await msg.answer("⛔ Ти не менеджер")
        return

    await msg.answer(
        "✍️ Введи адресу у форматі:\n"
        "Імʼя - Адреса (найближча станція метро)\n\n"
        "Приклад:\n"
        "Іван - вул. Хрещатик 1 (Майдан)"
    )

@dp.message_handler(lambda m: "-" in m.text and "(" in m.text and ")" in m.text)
async def save_address(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return

    data = load_storage()

    zone = detect_zone(msg.text)

    data["addresses"].append({
        "text": msg.text,
        "zone": zone
    })

    save_storage(data)
    await msg.answer(f"✅ Додано\n📍 {zone}")

@dp.message_handler(commands=["list"])
async def list_addresses(msg: types.Message):
    data = load_storage()

    if not data["addresses"]:
        await msg.answer("📭 Список порожній")
        return

    text = "📋 Адреси:\n\n"
    for i, a in enumerate(data["addresses"], 1):
        text += f"{i}. {a['text']}\n➡️ {a['zone']}\n\n"

    await msg.answer(text)

@dp.message_handler(commands=["del"])
async def del_address(msg: types.Message):
    if not is_manager(msg.from_user.id):
        await msg.answer("⛔ Ти не менеджер")
        return

    parts = msg.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await msg.answer("Формат: /del 1")
        return

    idx = int(parts[1]) - 1
    data = load_storage()

    if 0 <= idx < len(data["addresses"]):
        data["addresses"].pop(idx)
        save_storage(data)
        await msg.answer("🗑 Адресу видалено")
    else:
        await msg.answer("❌ Невірний номер")

# ---------- run ----------

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
