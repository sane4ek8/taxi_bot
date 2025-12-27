import json
import os
from datetime import date

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

TOKEN = os.getenv("BOT_TOKEN")  # Railway ENV

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

STORAGE_FILE = "storage.json"


# ---------- STORAGE ----------

def load_storage():
    if not os.path.exists(STORAGE_FILE):
        return {"managers": [], "days": {}}
    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_storage(data):
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def today():
    return str(date.today())


def is_manager(user_id: int) -> bool:
    data = load_storage()
    return user_id in data["managers"]


# ---------- METRO / ZONES ----------

ZONE_1 = ["Академмістечко", "Житомирська", "Святошин", "Нивки", "Берестейська"]
ZONE_2 = ["Героїв Дніпра", "Мінська", "Оболонь", "Почайна"]
ZONE_3 = ["Лісова", "Чернігівська", "Дарниця", "Лівобережна", "Троєщина"]
ZONE_4 = ["Осокорки", "Позняки", "Славутич", "Видубичі"]


def detect_zone(text: str) -> str:
    for s in ZONE_1:
        if s.lower() in text.lower():
            return "Зона 1"
    for s in ZONE_2:
        if s.lower() in text.lower():
            return "Зона 2"
    for s in ZONE_3:
        if s.lower() in text.lower():
            return "Зона 3"
    for s in ZONE_4:
        if s.lower() in text.lower():
            return "Зона 4"
    return "Невідома зона"


# ---------- FSM ----------

class AddAddressState(StatesGroup):
    waiting = State()


# ---------- COMMANDS ----------

@dp.message_handler(commands=["info", "start"])
async def info(msg: types.Message):
    await msg.answer(
        "🟢 <b>Бот працює</b>\n\n"
        "Команди:\n"
        "/add — Додавання адреси\n"
        "/del — Видалення адреси\n"
        "/list — Список адрес\n"
        "/add_Man — Додати менеджера\n"
        "/del_Man — Видалити менеджера\n"
        "/info — Список команд",
        parse_mode="HTML"
    )


@dp.message_handler(commands=["add"])
async def add_address(msg: types.Message):
    if not is_manager(msg.from_user.id):
        await msg.answer("⛔ Ти не менеджер")
        return

    await msg.answer(
        "✍️ Введи адресу у форматі:\n"
        "<b>Імʼя - Адреса (Станція метро)</b>",
        parse_mode="HTML"
    )
    await AddAddressState.waiting.set()


@dp.message_handler(state=AddAddressState.waiting)
async def save_address(msg: types.Message, state: FSMContext):
    text = msg.text

    if "-" not in text:
        await msg.answer("❌ Невірний формат")
        return

    zone = detect_zone(text)

    data = load_storage()
    day = today()

    data["days"].setdefault(day, [])
    data["days"][day].append({
        "text": text,
        "zone": zone
    })

    save_storage(data)

    await msg.answer(f"✅ Додано\n📍 {zone}")
    await state.finish()


@dp.message_handler(commands=["list"])
async def list_addresses(msg: types.Message):
    data = load_storage()
    day = today()

    if day not in data["days"] or not data["days"][day]:
        await msg.answer("📭 Список порожній")
        return

    zones = {}
    for item in data["days"][day]:
        zones.setdefault(item["zone"], []).append(item["text"])

    text = "🚗 <b>Розподіл по машинах</b>\n\n"
    for zone, items in zones.items():
        text += f"<b>{zone}</b>\n"
        for i, addr in enumerate(items, 1):
            text += f"{i}. {addr}\n"
        text += "\n"

    await msg.answer(text, parse_mode="HTML")


@dp.message_handler(commands=["del"])
async def delete_address(msg: types.Message):
    if not is_manager(msg.from_user.id):
        await msg.answer("⛔ Ти не менеджер")
        return

    try:
        idx = int(msg.get_args()) - 1
    except:
        await msg.answer("Використання: /del 1")
        return

    data = load_storage()
    day = today()

    if day not in data["days"] or idx >= len(data["days"][day]):
        await msg.answer("❌ Невірний номер")
        return

    removed = data["days"][day].pop(idx)
    save_storage(data)

    await msg.answer(f"🗑 Видалено:\n{removed['text']}")


@dp.message_handler(commands=["add_Man"])
async def add_manager(msg: types.Message):
    try:
        user_id = int(msg.get_args())
    except:
        await msg.answer("Використання: /add_Man 123456789")
        return

    data = load_storage()
    if user_id not in data["managers"]:
        data["managers"].append(user_id)
        save_storage(data)

    await msg.answer("✅ Менеджера додано")


@dp.message_handler(commands=["del_Man"])
async def del_manager(msg: types.Message):
    try:
        user_id = int(msg.get_args())
    except:
        await msg.answer("Використання: /del_Man 123456789")
        return

    data = load_storage()
    if user_id in data["managers"]:
        data["managers"].remove(user_id)
        save_storage(data)

    await msg.answer("🗑 Менеджера видалено")


# ---------- START ----------

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
