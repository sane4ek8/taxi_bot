import os
import json
import pandas as pd
from aiogram import Bot, Dispatcher, executor, types

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

STORAGE = "storage.json"
EXCEL_FILE = "people.xlsx"


# ---------- ZONES ----------
ZONES = {
    1: {"stations": [
        "героїв дніпра", "мінська", "оболонь", "почайна",
        "тарса шевченка", "контрактова площа", "поштова площа",
        "майдан незалежності", "площа українських героїв",
        "олімпійська", "палац україна", "либідська",
        "академмістечко", "житомирська", "святошин", "нивки",
        "берестейська", "шулявська", "політехнічний інститут",
        "вокзальна", "університет", "театральна",
        "хрещатик", "арсенальна", "дорогожичі",
        "печерськ", "сирець"
    ]},
    2: {"stations": [
        "звіринецька", "деміївська", "голосіївська",
        "васильківська", "вднх", "іподром", "теремки"
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


def detect_zone(metro: str):
    metro = metro.lower()
    for zone, data in ZONES.items():
        if metro in data["stations"]:
            return zone
    return None


# ---------- STORAGE ----------
def load_storage():
    if not os.path.exists(STORAGE):
        return {"managers": [], "today": []}
    with open(STORAGE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_storage(data):
    with open(STORAGE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_manager(uid):
    return uid in load_storage()["managers"]


# ---------- EXCEL ----------
def load_people():
    df = pd.read_excel(EXCEL_FILE)
    people = {}
    for _, row in df.iterrows():
        surname = str(row["surname"]).strip().lower()
        people[surname] = {
            "address": str(row["address"]).strip(),
            "metro": str(row["metro"]).strip().lower()
        }
    return people


PEOPLE = load_people()


# ---------- COMMANDS ----------
@dp.message_handler(commands=["start", "info"])
async def info(msg: types.Message):
    await msg.answer(
        "🤖 Бот працює\n\n"
        "Команди:\n"
        "/add – додати людину (по прізвищу)\n"
        "/list – список адрес по зонах\n"
        "/add_Man – додати менеджера\n"
        "/del_Man – видалити менеджера"
    )


@dp.message_handler(commands=["add"])
async def add_hint(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return
    await msg.answer("✍️ Введи прізвище (як в Excel)")


@dp.message_handler(lambda m: m.text.isalpha())
async def add_by_surname(msg: types.Message):
    if not is_manager(msg.from_user.id):
        return

    surname = msg.text.lower()
    if surname not in PEOPLE:
        await msg.answer("❌ Такого прізвища немає в Excel")
        return

    person = PEOPLE[surname]
    zone = detect_zone(person["metro"])
    if not zone:
        await msg.answer("❌ Не можу визначити зону по метро")
        return

    data = load_storage()
    data["today"].append({
        "surname": surname.capitalize(),
        "address": person["address"],
        "metro": person["metro"],
        "zone": zone
    })
    save_storage(data)

    await msg.answer(f"✅ Додано в зону {zone}")


@dp.message_handler(commands=["list"])
async def list_today(msg: types.Message):
    data = load_storage()
    if not data["today"]:
        await msg.answer("📭 Список порожній")
        return

    text = "📋 Адреси по зонах:\n\n"
    for zone in range(1, 5):
        items = [p for p in data["today"] if p["zone"] == zone]
        if items:
            text += f"🚗 Зона {zone}:\n"
            for i, p in enumerate(items, 1):
                text += f"{i}. {p['surname']} — {p['address']} ({p['metro']})\n"
            text += "\n"

    await msg.answer(text)


@dp.message_handler(commands=["add_Man"])
async def add_manager(msg: types.Message):
    data = load_storage()
    if msg.from_user.id not in data["managers"]:
        data["managers"].append(msg.from_user.id)
        save_storage(data)
    await msg.answer("✅ Ти менеджер")


@dp.message_handler(commands=["del_Man"])
async def del_manager(msg: types.Message):
    data = load_storage()
    if msg.from_user.id in data["managers"]:
        data["managers"].remove(msg.from_user.id)
        save_storage(data)
    await msg.answer("❌ Менеджера видалено")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
