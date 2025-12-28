import json
import os
from aiogram import Bot, Dispatcher, executor, types
from config import (
    TOKEN,
    PEOPLE_STORAGE,
    TAXI_STORAGE,
    MANAGERS_FILE,
    MAX_IN_CAR
)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

waiting_for_add = set()
waiting_for_del = set()

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
    managers = load_json(MANAGERS_FILE, [])
    return user_id in managers

# ---------- zones ----------
ZONES = {
    1: {"stations": [
        "академмістечко", "житомирська", "святошин", "нивки",
        "берестейська", "шулявська", "політехнічний інститут",
        "вокзальна", "університет", "театральна",
        "хрещатик", "арсенальна", "героїв дніпра", "мінська",
        "оболонь", "почайна", "тарса шевченка",
        "контрактова площа", "поштова площа",
        "майдан незалежності", "сирець",
        "дорогожичі", "лук'янівська", "золоті ворота"
    ]},
    2: {"stations": [
        "палац спорту", "кловська", "печерська",
        "звіринецька", "видубичі",
        "площа українських героїв", "олімпійська",
        "палац україна", "либідська",
        "деміївська", "голосіївська", "васильківська",
        "вднг", "іподром", "теремки"
    ]},
    3: {"stations": [
        "дніпро", "гідропарк", "лівобережна",
        "дарниця", "чернігівська", "лісова"
    ]},
    4: {"stations": [
        "славутич", "осокорки", "позняки",
        "харківська", "вирлиця",
        "бориспільська", "червоний хутір"
    ]}
}

def detect_zone(station):
    s = station.lower()
    for zone, data in ZONES.items():
        if s in data["stations"]:
            return zone
    return None

# ---------- INFO ----------
@dp.message_handler(commands=["start", "info"])
async def info(msg: types.Message):
    await msg.answer(
        "🤖 Бот працює\n\n"
        "Команди:\n"
        "/add — Додати людей у таксі\n"
        "/del — Видалити людей з таксі\n"
        "/list — Всі люди (storage)\n"
        "/taxi — Таксі по зонах\n"
        "/add_Man — Додати менеджера\n"
        "/del_Man — Видалити менеджера"
    )

# ---------- ADD ----------
@dp.message_handler(commands=["add"])
async def add_start(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return
    waiting_for_add.add(msg.from_user.id)
    await msg.answer("✍️ Введи прізвища (через кому)")

@dp.message_handler(lambda m: m.from_user.id in waiting_for_add)
async def handle_add(msg: types.Message):
    waiting_for_add.discard(msg.from_user.id)

    people = load_json(PEOPLE_STORAGE, {})
    taxi = load_json(TAXI_STORAGE, {})

    surnames = [s.strip().lower() for s in msg.text.split(",") if s.strip()]
    added, not_found = [], []

    for s in surnames:
        if s not in people:
            not_found.append(s)
            continue

        person = people[s]
        zone = detect_zone(person["station"])
        if not zone:
            continue

        taxi.setdefault(str(zone), []).append(person)
        added.append(person["surname"])

    save_json(TAXI_STORAGE, taxi)

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
    waiting_for_del.add(msg.from_user.id)
    await msg.answer("🗑 Введи прізвища для видалення (через кому)")

@dp.message_handler(lambda m: m.from_user.id in waiting_for_del)
async def handle_del(msg: types.Message):
    waiting_for_del.discard(msg.from_user.id)

    surnames = [s.strip().lower() for s in msg.text.split(",") if s.strip()]
    taxi = load_json(TAXI_STORAGE, {})
    removed = []

    for zone in list(taxi.keys()):
        taxi[zone] = [
            p for p in taxi[zone]
            if not (p["surname"].lower() in surnames and removed.append(p["surname"]) is None)
        ]
        if not taxi[zone]:
            del taxi[zone]

    save_json(TAXI_STORAGE, taxi)

    if removed:
        await msg.answer("🗑 Видалено:\n" + ", ".join(set(removed)))
    else:
        await msg.answer("❌ Нікого не знайдено")

# ---------- LIST STORAGE ----------
@dp.message_handler(commands=["list"])
async def list_people(msg: types.Message):
    people = load_json(PEOPLE_STORAGE, {})
    if not people:
        await msg.answer("📭 Сторейж порожній")
        return

    text = "📋 Всі люди:\n\n"
    for i, p in enumerate(people.values(), 1):
        text += f"{i}. {p['surname']} — {p['address']} ({p['station']})\n"

    await msg.answer(text)

# ---------- TAXI ----------
@dp.message_handler(commands=["taxi"])
async def taxi_list(msg: types.Message):
    taxi = load_json(TAXI_STORAGE, {})
    if not taxi:
        await msg.answer("📭 Таксі порожнє")
        return

    text = ""
    for zone in sorted(taxi, key=int):
        text += f"\n🚦 Зона {zone}\n"
        people = taxi[zone]
        for i in range(0, len(people), MAX_IN_CAR):
            text += f"🚗 Машина {(i // MAX_IN_CAR) + 1}\n"
            for j, p in enumerate(people[i:i + MAX_IN_CAR], 1):
                text += f"{j}. {p['surname']} — {p['address']} ({p['station']})\n"

    await msg.answer(text)

# ---------- MANAGERS ----------
@dp.message_handler(commands=["add_Man"])
async def add_manager(msg: types.Message):
    managers = load_json(MANAGERS_FILE, [])
    managers.append(msg.from_user.id)
    save_json(MANAGERS_FILE, list(set(managers)))
    await msg.answer("✅ Ти менеджер")

@dp.message_handler(commands=["del_Man"])
async def del_manager(msg: types.Message):
    managers = load_json(MANAGERS_FILE, [])
    if msg.from_user.id in managers:
        managers.remove(msg.from_user.id)
        save_json(MANAGERS_FILE, managers)
    await msg.answer("❌ Менеджера видалено")

# ---------- RUN ----------
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)





