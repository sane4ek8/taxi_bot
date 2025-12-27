import json
import os
from aiogram import Bot, Dispatcher, executor, types

TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

STORAGE_FILE = "storage.json"


# ---------- STORAGE ----------
def load_data():
    if not os.path.exists(STORAGE_FILE):
        return {"addresses": [], "managers": []}
    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------- MANAGERS ----------
def is_manager(user_id: int) -> bool:
    data = load_data()
    return user_id in data["managers"]


# ---------- METRO → ZONES ----------
METRO_ZONES = {
    # Зона 1 — червона гілка, правий берег
    "Академмістечко": 1,
    "Житомирська": 1,
    "Святошин": 1,
    "Нивки": 1,
    "Берестейська": 1,
    "Шулявська": 1,

    # Зона 2 — синя гілка, правий берег
    "Героїв Дніпра": 2,
    "Мінська": 2,
    "Оболонь": 2,
    "Почайна": 2,
    "Петрівка": 2,

    # Зона 3 — червона гілка, лівий берег
    "Дарниця": 3,
    "Лівобережна": 3,
    "Чернігівська": 3,
    "Лісова": 3,
    "Троєщина": 3,

    # Зона 4 — зелена гілка, лівий берег
    "Осокорки": 4,
    "Позняки": 4,
    "Харківська": 4,
    "Вирлиця": 4,
    "Бориспільська": 4,
    "Славутич": 4,
}


def detect_zone(address: str):
    for station, zone in METRO_ZONES.items():
        if station.lower() in address.lower():
            return zone
    return None


# ---------- COMMANDS ----------
@dp.message_handler(commands=["info", "start"])
async def info(msg: types.Message):
    text = (
        "✅ Бот працює\n\n"
        "Команди:\n"
        "/add — Додавання адреси\n"
        "/del — Видалення адреси\n"
        "/list — Список адрес (по зонах)\n"
        "/add_Man — Додавання менеджера\n"
        "/del_Man — Видалення менеджера\n"
        "/info — Список команд\n\n"
        "📌 Формат вводу адреси:\n"
        "Імʼя - адреса (найближча станція метро)"
    )
    await msg.answer(text)


# ---------- ADD ADDRESS ----------
@dp.message_handler(commands=["add"])
async def add_address(msg: types.Message):
    if not is_manager(msg.from_user.id):
        await msg.answer("❌ Ти не менеджер")
        return

    await msg.answer(
        "✍️ Введи адресу у форматі:\n"
        "Імʼя - адреса (найближча станція метро)\n\n"
        "Приклад:\n"
        "Іван - вул. Драйзера 15 (Чернігівська)"
    )


@dp.message_handler(lambda m: "-" in m.text and "(" in m.text and ")" in m.text)
async def save_address(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return

    try:
        name, rest = msg.text.split("-", 1)
        address = rest.strip()
    except ValueError:
        return

    zone = detect_zone(address)
    if not zone:
        await msg.answer("❌ Не вдалося визначити зону. Вкажи станцію метро.")
        return

    data = load_data()
    data["addresses"].append({
        "name": name.strip(),
        "address": address,
        "zone": zone
    })
    save_data(data)

    await msg.answer(f"✅ Додано в ЗОНУ {zone}")


# ---------- LIST ----------
@dp.message_handler(commands=["list"])
async def list_addresses(msg: types.Message):
    data = load_data()
    if not data["addresses"]:
        await msg.answer("📭 Список порожній")
        return

    zones = {}
    for item in data["addresses"]:
        zones.setdefault(item["zone"], []).append(item)

    text = "🚕 Адреси по машинах (зонах):\n\n"
    for zone in sorted(zones):
        text += f"🟢 ЗОНА {zone}:\n"
        for i, a in enumerate(zones[zone], 1):
            text += f"{i}. {a['name']} — {a['address']}\n"
        text += "\n"

    await msg.answer(text)


# ---------- DELETE ADDRESS ----------
@dp.message_handler(commands=["del"])
async def delete_address(msg: types.Message):
    if not is_manager(msg.from_user.id):
        await msg.answer("❌ Ти не менеджер")
        return

    data = load_data()
    if not data["addresses"]:
        await msg.answer("📭 Список порожній")
        return

    data["addresses"].pop()
    save_data(data)
    await msg.answer("🗑 Останню адресу видалено")


# ---------- MANAGERS ----------
@dp.message_handler(commands=["add_Man"])
async def add_manager(msg: types.Message):
    data = load_data()
    if msg.from_user.id not in data["managers"] and data["managers"]:
        await msg.answer("❌ Тільки менеджер може додавати менеджерів")
        return

    try:
        new_id = int(msg.text.split()[1])
    except:
        await msg.answer("Формат: /add_Man 123456789")
        return

    if new_id not in data["managers"]:
        data["managers"].append(new_id)
        save_data(data)
        await msg.answer("✅ Менеджера додано")


@dp.message_handler(commands=["del_Man"])
async def del_manager(msg: types.Message):
    data = load_data()
    if msg.from_user.id not in data["managers"]:
        await msg.answer("❌ Ти не менеджер")
        return

    try:
        rem_id = int(msg.text.split()[1])
    except:
        await msg.answer("Формат: /del_Man 123456789")
        return

    if rem_id in data["managers"]:
        data["managers"].remove(rem_id)
        save_data(data)
        await msg.answer("🗑 Менеджера видалено")


# ---------- RUN ----------
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
