import logging
import pandas as pd
from aiogram import Bot, Dispatcher, executor, types

TOKEN = "PASTE_YOUR_TOKEN_HERE"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ---------- ЗОНИ ----------
ZONES = {
    1: [
        "героїв дніпра", "мінська", "оболонь", "почайна",
        "тарса шевченка", "контрактова площа", "поштова площа",
        "майдан незалежності", "площа українських героїв",
        "олімпійська", "палац україна", "либідська",
        "академмістечко", "житомирська", "святошин", "нивки",
        "берестейська", "шулявська", "політехнічний інститут",
        "вокзальна", "університет", "театральна",
        "хрещатик", "арсенальна", "дорогожичі", "печерськ", "сирець"
    ],
    2: [
        "звіринецька", "деміївська", "голосіївська",
        "васильківська", "вднх", "іподром", "теремки"
    ],
    3: [
        "дніпро", "гідропарк", "лівобережна",
        "дарниця", "чернігівська", "лісова", "троєщина"
    ],
    4: [
        "славутич", "осокорки", "позняки",
        "харківська", "вирлиця", "бориспільська", "червоний хутір"
    ]
}

# ---------- СТАН ----------
waiting_for_surname = set()
cars = {1: [], 2: [], 3: [], 4: []}

# ---------- ДОП ФУНКЦІЇ ----------
def get_zone_by_metro(metro: str):
    metro = metro.lower().strip()
    for zone, stations in ZONES.items():
        if metro in stations:
            return zone
    return None

# ---------- КОМАНДИ ----------
@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    await msg.answer(
        "🚕 Бот таксі\n\n"
        "/add — додати людину (вводиться ТІЛЬКИ прізвище)\n"
        "/list — показати машини\n"
        "/clear — очистити список"
    )

@dp.message_handler(commands=["add"])
async def add(msg: types.Message):
    waiting_for_surname.add(msg.from_user.id)
    await msg.answer("Введи прізвище (як в Excel):")

@dp.message_handler(commands=["list"])
async def show_list(msg: types.Message):
    text = "🚕 Розподіл по машинах:\n\n"
    for zone, people in cars.items():
        text += f"Зона {zone}:\n"
        if people:
            for p in people:
                text += f"• {p}\n"
        else:
            text += "— порожньо\n"
        text += "\n"
    await msg.answer(text)

@dp.message_handler(commands=["clear"])
async def clear(msg: types.Message):
    for z in cars:
        cars[z].clear()
    await msg.answer("🧹 Список очищено")

# ---------- ОБРОБКА ПРІЗВИЩА ----------
@dp.message_handler()
async def handle_surname(msg: types.Message):
    if msg.from_user.id not in waiting_for_surname:
        return

    waiting_for_surname.remove(msg.from_user.id)

    surname_input = msg.text.strip().lower()

    try:
        df = pd.read_excel("people.xlsx")
    except Exception as e:
        await msg.answer("❌ Не можу відкрити Excel")
        return

    df["surname"] = df["surname"].astype(str).str.lower().str.strip()

    person = df[df["surname"] == surname_input]

    if person.empty:
        await msg.answer("❌ Прізвище не знайдено в Excel")
        return

    row = person.iloc[0]
    metro = str(row["metro"]).lower().strip()
    address = str(row["address"])

    zone = get_zone_by_metro(metro)

    if not zone:
        await msg.answer(f"❌ Станція «{metro}» не входить в жодну зону")
        return

    cars[zone].append(f"{row['surname']} — {address} ({metro})")

    await msg.answer(
        f"✅ Додано\n"
        f"👤 {row['surname']}\n"
        f"🚇 {metro}\n"
        f"🟦 Зона {zone}"
    )

# ---------- СТАРТ ----------
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
