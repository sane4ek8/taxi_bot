import json
import os
from aiogram import Bot, Dispatcher, executor, types
import pandas as pd

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

DATA_FILE = "data.json"
MAN_FILE = "managers.json"
PEOPLE_FILE = "people.xlsx"

waiting_for_surname = set()
waiting_for_delete = set()

MAX_IN_CAR = 4

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
        "академмістечко", "житомирська", "святошин", "нивки",
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
        "/add — Додати людей\n"
        "/del — Видалити людей\n"
        "/list — Список + машини\n"
        "/add_Man — Додати менеджера\n"
        "/del_Man — Видалити менеджера"
    )

# ---------- ADD ----------
@dp.message_handler(commands=["add"])
async def add_start(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return
    waiting_for_surname.add(msg.from_user.id)
    await msg.answer("✍️ Введи прізвища з Excel (можна через кому)")

@dp.message_handler(lambda m: m.from_user.id in waiting_for_surname)
async def handle_add(msg: types.Message):
    waiting_for_surname.discard(msg.from_user.id)

    df = pd.read_excel(PEOPLE_FILE)
    df["surname"] = df["surname"].astype(str).str.lower()

    surnames = [s.strip().lower() for s in msg.text.split(",") if s.strip()]
    data = load_json(DATA_FILE, {})

    added, not_found = [], []

    for surname in surnames:
        row = df[df["surname"] == surname]
        if row.empty:
            not_found.append(surname)
            continue

        person = row.iloc[0]
        zone = detect_zone(str(person["station"]))
        if not zone:
            continue

        data.setdefault(str(zone), []).append({
            "name": person["surname"],
            "address": person["address"],
            "station": person["station"]
        })
        added.append(person["surname"])

    save_json(DATA_FILE, data)

    text = ""
    if added:
        text += "✅ Додано:\n" + ", ".join(added) + "\n\n"
    if not_found:
        text += "❌ Не знайдено:\n" + ", ".join(not_found)

    await msg.answer(text.strip())

# ---------- DEL ----------
@dp.message_handler(commands=["del"])
async def del_start(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return
    waiting_for_delete.add(msg.from_user.id)
    await msg.answer("🗑 Введи прізвища для видалення (через кому)")

@dp.message_handler(lambda m: m.from_user.id in waiting_for_delete)
async def handle_del(msg: types.Message):
    waiting_for_delete.discard(msg.from_user.id)

    surnames = [s.strip().lower() for s in msg.text.split(",") if s.strip()]
    data = load_json(DATA_FILE, {})

    removed = []

    for zone in list(data.keys()):
        data[zone] = [
            p for p in data[zone]
            if not (p["name"].lower() in surnames and removed.append(p["name"]) is None)
        ]
        if not data[zone]:
            del data[zone]

    save_json(DATA_FILE, data)

    if removed:
        await msg.answer("🗑 Видалено:\n" + ", ".join(set(removed)))
    else:
        await msg.answer("❌ Нікого не знайдено")

# ---------- LIST + CARS ----------
@dp.message_handler(commands=["list"])
async def list_addresses(msg: types.Message):
    data = load_json(DATA_FILE, {})
    if not data:
        await msg.answer("📭 Список порожній")
        return

    text = ""
    for zone in sorted(data, key=int):
        text += f"\n🚦 Зона {zone}\n"
        people = data[zone]

        for i in range(0, len(people), MAX_IN_CAR):
            text += f"🚗 Машина {(i // MAX_IN_CAR) + 1}\n"
            for j, p in enumerate(people[i:i + MAX_IN_CAR], 1):
                text += f"{j}. {p['name']} — {p['address']} ({p['station']})\n"

    await msg.answer(text)

# ---------- MANAGERS ----------
@dp.message_handler(commands=["add_Man"])
async def add_manager(msg: types.Message):
    managers = load_json(MAN_FILE, [])
    managers.append(msg.from_user.id)
    save_json(MAN_FILE, list(set(managers)))
    await msg.answer("✅ Ти менеджер")

@dp.message_handler(commands=["del_Man"])
async def del_manager(msg: types.Message):
    managers = load_json(MAN_FILE, [])
    if msg.from_user.id in managers:
        managers.remove(msg.from_user.id)
        save_json(MAN_FILE, managers)
    await msg.answer("❌ Менеджера видалено")

# ---------- RUN ----------
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
