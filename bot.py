import logging
import pandas as pd
from aiogram import Bot, Dispatcher, executor, types
import os

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

MANAGERS = set()          # зберігаєш як раніше
PASSENGERS = {1: [], 2: [], 3: [], 4: []}
PEOPLE = {}               # дані з Excel

ZONES = {
    1: {"stations": [
        "героїв дніпра", "мінська", "оболонь", "почайна",
        "тарса шевченка", "контрактова площа", "поштова площа",
        "майдан незалежності", "площа українських героїв",
        "олімпійська", "палац україна", "либідська",
        "академмістечко", "житомирська", "святошин", "нивки",
        "берестейська", "шулявська", "політехнічний інститут",
        "вокзальна", "університет", "театральна",
        "хрещатик", "арсенальна", "дорогожичі", "печерськ", "сирець"
    ]},
    2: {"stations": [
        "звіринецька", "деміївська", "голосіївська",
        "васильківська", "вднх", "іподром", "теремки"
    ]},
    3: {"stations": [
        "дніпро", "гідропарк", "лівобережна",
        "дарниця", "чернігівська", "лісова", "троєщина"
    ]},
    4: {"stations": [
        "славутич", "осокорки", "позняки",
        "харківська", "вирлиця", "бориспільська",
        "червоний хутір"
    ]}
}


def get_zone_by_station(station: str):
    station = station.lower()
    for zone, data in ZONES.items():
        if station in data["stations"]:
            return zone
    return None


@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def upload_excel(message: types.Message):
    if not message.document.file_name.endswith(".xlsx"):
        return

    file = await bot.get_file(message.document.file_id)
    await bot.download_file(file.file_path, "people.xlsx")

    df = pd.read_excel("people.xlsx")

    PEOPLE.clear()
    for _, row in df.iterrows():
        PEOPLE[row["Surname"].lower()] = {
            "Address": row["Address"],
            "Station": row["Station"]
        }

    await message.answer("✅ Excel завантажено та оброблено")


@dp.message_handler(commands=["add"])
async def add_person(message: types.Message):
    surname = message.get_args().strip().lower()

    if surname not in PEOPLE:
        await message.answer("❌ Прізвище не знайдено в Excel")
        return

    data = PEOPLE[surname]
    zone = get_zone_by_station(data["station"])

    if not zone:
        await message.answer("❌ Не можу визначити зону")
        return

    PASSENGERS[zone].append(
        f"{surname.title()} — {data['address']} ({data['station']})"
    )

    await message.answer(f"✅ Додано в зону {zone}")


@dp.message_handler(commands=["list"])
async def show_list(message: types.Message):
    text = "📋 Списки по зонах:\n\n"
    for zone, people in PASSENGERS.items():
        text += f"🚗 Зона {zone}:\n"
        if people:
            for p in people:
                text += f" • {p}\n"
        else:
            text += " — порожньо\n"
        text += "\n"

    await message.answer(text)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)


