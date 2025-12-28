import os
import logging
import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ====== ЗОНИ ======
ZONES = {
    1: ["героїв дніпра","мінська","оболонь","почайна","тарса шевченка",
        "контрактова площа","поштова площа","майдан незалежності",
        "площа українських героїв","олімпійська","палац україна",
        "либідська","академмістечко","житомирська","святошин",
        "нивки","берестейська","шулявська","політехнічний інститут",
        "вокзальна","університет","театральна","хрещатик",
        "арсенальна","дорогожичі","печерськ","сирець"],

    2: ["звіринецька","деміївська","голосіївська",
        "васильківська","вднх","іподром","теремки"],

    3: ["дніпро","гідропарк","лівобережна",
        "дарниця","чернігівська","лісова","троєщина"],

    4: ["славутич","осокорки","позняки",
        "харківська","вирлиця","бориспільська","червоний хутір"]
}

# ====== СХОВИЩА ======
waiting_for_surname = set()
rides = {1: [], 2: [], 3: [], 4: []}

# ====== EXCEL ======
EXCEL_PATH = "data.xlsx"
df = pd.read_excel(EXCEL_PATH)

df["surname"] = df["surname"].str.lower().str.strip()
df["station"] = df["station"].str.lower().str.strip()

# ====== HELP ======
@dp.message_handler(Command("info"))
async def info(msg: types.Message):
    await msg.answer(
        "Бот працює\n\n"
        "/add — додати пасажира\n"
        "/list — список по зонах\n"
        "/info — команди"
    )

# ====== ADD ======
@dp.message_handler(Command("add"))
async def add_start(msg: types.Message):
    waiting_for_surname.add(msg.from_user.id)
    await msg.answer("Введи прізвище")

@dp.message_handler(lambda msg: msg.from_user.id in waiting_for_surname)
async def add_surname(msg: types.Message):
    surname = msg.text.lower().strip()
    waiting_for_surname.discard(msg.from_user.id)

    row = df[df["surname"] == surname]
    if row.empty:
        await msg.answer("❌ Прізвище не знайдено в Excel")
        return

    station = row.iloc[0]["station"]

    zone_found = None
    for zone, stations in ZONES.items():
        if station in stations:
            zone_found = zone
            break

    if not zone_found:
        await msg.answer("❌ Не вдалося визначити зону")
        return

    rides[zone_found].append(row.iloc[0]["surname"].title())
    await msg.answer(f"✅ Додано в зону {zone_found}")

# ====== LIST ======
@dp.message_handler(Command("list"))
async def show_list(msg: types.Message):
    text = ""
    for zone, people in rides.items():
        text += f"\nЗона {zone}:\n"
        if people:
            for p in people:
                text += f" - {p}\n"
        else:
            text += " (порожньо)\n"

    await msg.answer(text)

# ====== START ======
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
