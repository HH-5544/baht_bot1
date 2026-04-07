"""
BAHT RESIDENCE — Telegram Bot + Mini App сервер
Запуск: python bot.py
"""

import asyncio
import json
import os
import logging
from pathlib import Path
from aiohttp import web, ClientSession
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ─────────────────────────────────────────────
# Конфиг (задайте свои значения в .env или здесь)
# ─────────────────────────────────────────────
BOT_TOKEN   = os.getenv("BOT_TOKEN",   "ВСТАВЬТЕ_ТОКЕН_БОТА")
CHANNEL_ID  = os.getenv("CHANNEL_ID",  "@bahtresidence")   # канал для публикации
ADMIN_IDS   = [int(x) for x in os.getenv("ADMIN_IDS", "123456789").split(",")]
MINIAPP_URL = os.getenv("MINIAPP_URL", "https://ваш-сервер.railway.app")
PORT        = int(os.getenv("PORT", 8080))
DATA_FILE   = Path("properties.json")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ─── Хранилище ────────────────────────────────
def load() -> list:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return []

def save(data: list):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def next_id(data: list) -> int:
    return max((p["id"] for p in data), default=0) + 1

# ─── FSM состояния ────────────────────────────
class Add(StatesGroup):
    photo       = State()
    name        = State()
    prop_type   = State()
    price       = State()
    address     = State()
    rooms       = State()
    description = State()

TYPES = {
    "new":        "🏗 Новостройка",
    "secondary":  "🏠 Вторичное",
    "commercial": "🏢 Коммерция",
    "rent":       "🔑 Аренда",
    "house":      "🏡 Дом / Вилла",
}

router = Router()

# ─── /start ───────────────────────────────────
@router.message(Command("start"))
async def cmd_start(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🏠 Открыть каталог",
            web_app=WebAppInfo(url=MINIAPP_URL)
        )
    ]])
    await msg.answer(
        "👋 Добро пожаловать в <b>BAHT RESIDENCE</b>!\n\n"
        "Нажмите кнопку ниже, чтобы открыть каталог объектов:",
        parse_mode="HTML",
        reply_markup=kb
    )

# ─── /help ────────────────────────────────────
@router.message(Command("help"))
async def cmd_help(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    await msg.answer(
        "<b>Команды администратора:</b>\n\n"
        "/add — добавить объект\n"
        "/list — список всех объектов\n"
        "/delete [ID] — удалить объект\n"
        "/stats — статистика каталога",
        parse_mode="HTML"
    )

# ─── /add — шаг 1: фото ──────────────────────
@router.message(Command("add"))
async def cmd_add(msg: Message, state: FSMContext):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("❌ У вас нет доступа.")
        return
    await msg.answer("📸 Отправьте фото объекта:")
    await state.set_state(Add.photo)

@router.message(Add.photo, F.photo)
async def add_photo(msg: Message, state: FSMContext):
    await state.update_data(photo=msg.photo[-1].file_id)
    await msg.answer("🏷 Введите название объекта:\n<i>Пример: Sky Residence, ЖК Pushkin</i>", parse_mode="HTML")
    await state.set_state(Add.name)

@router.message(Add.photo)
async def add_photo_wrong(msg: Message):
    await msg.answer("❌ Пожалуйста, отправьте фото (не файл).")

# ─── Шаг 2: название ──────────────────────────
@router.message(Add.name)
async def add_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text.strip())
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏗 Новостройка",  callback_data="t:new"),
         InlineKeyboardButton(text="🏠 Вторичное",   callback_data="t:secondary")],
        [InlineKeyboardButton(text="🏢 Коммерция",   callback_data="t:commercial"),
         InlineKeyboardButton(text="🔑 Аренда",      callback_data="t:rent")],
        [InlineKeyboardButton(text="🏡 Дом / Вилла", callback_data="t:house")],
    ])
    await msg.answer("📂 Выберите тип объекта:", reply_markup=kb)
    await state.set_state(Add.prop_type)

# ─── Шаг 3: тип ───────────────────────────────
@router.callback_query(Add.prop_type, F.data.startswith("t:"))
async def add_type(cb: CallbackQuery, state: FSMContext):
    key = cb.data.split(":")[1]
    await state.update_data(prop_type=TYPES[key], prop_type_key=key)
    await cb.message.answer("💰 Введите цену:\n<i>Примеры: $150 000  или  $2 500/мес</i>", parse_mode="HTML")
    await state.set_state(Add.price)
    await cb.answer()

# ─── Шаг 4: цена ──────────────────────────────
@router.message(Add.price)
async def add_price(msg: Message, state: FSMContext):
    await state.update_data(price=msg.text.strip())
    await msg.answer("📍 Введите адрес объекта:\n<i>Пример: Мирабадский р-н, ул. Навои, 45</i>", parse_mode="HTML")
    await state.set_state(Add.address)

# ─── Шаг 5: адрес ─────────────────────────────
@router.message(Add.address)
async def add_address(msg: Message, state: FSMContext):
    await state.update_data(address=msg.text.strip())
    await msg.answer("📐 Площадь и комнаты:\n<i>Пример: 95 м² · 3 комн  или  320 м² · Open space</i>", parse_mode="HTML")
    await state.set_state(Add.rooms)

# ─── Шаг 6: площадь ───────────────────────────
@router.message(Add.rooms)
async def add_rooms(msg: Message, state: FSMContext):
    await state.update_data(rooms=msg.text.strip())
    await msg.answer("📝 Краткое описание (или '-' чтобы пропустить):")
    await state.set_state(Add.description)

# ─── Шаг 7: описание + публикация ─────────────
@router.message(Add.description)
async def add_description(msg: Message, state: FSMContext, bot: Bot):
    data   = await state.get_data()
    desc   = msg.text.strip() if msg.text.strip() != "-" else ""
    props  = load()
    prop   = {
        "id":          next_id(props),
        "name":        data["name"],
        "type":        data["prop_type"],
        "type_key":    data["prop_type_key"],
        "price":       data["price"],
        "address":     data["address"],
        "rooms":       data["rooms"],
        "description": desc,
        "photo":       data["photo"],
        "active":      True,
    }
    props.append(prop)
    save(props)

    # Подпись для канала
    caption = (
        f"🏠 <b>{prop['name']}</b>\n\n"
        f"📂 {prop['type']}\n"
        f"💰 {prop['price']}\n"
        f"📍 {prop['address']}\n"
        f"📐 {prop['rooms']}"
    )
    if desc:
        caption += f"\n\n{desc}"

    kb_channel = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Открыть каталог", web_app=WebAppInfo(url=MINIAPP_URL))],
        [InlineKeyboardButton(text="📞 Связаться",       url="https://t.me/bahtresidence")],
    ])

    await bot.send_photo(
        CHANNEL_ID, prop["photo"],
        caption=caption, parse_mode="HTML",
        reply_markup=kb_channel
    )

    await msg.answer(
        f"✅ Объект <b>«{prop['name']}»</b> (ID: {prop['id']}) добавлен и опубликован в канале!",
        parse_mode="HTML"
    )
    await state.clear()

# ─── /list ────────────────────────────────────
@router.message(Command("list"))
async def cmd_list(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    props = [p for p in load() if p.get("active")]
    if not props:
        await msg.answer("📭 Каталог пуст.")
        return
    lines = [f"#{p['id']} <b>{p['name']}</b> — {p['price']}" for p in props]
    await msg.answer(
        f"📋 <b>Каталог ({len(props)} объектов):</b>\n\n" + "\n".join(lines),
        parse_mode="HTML"
    )

# ─── /delete ──────────────────────────────────
@router.message(Command("delete"))
async def cmd_delete(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    parts = msg.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await msg.answer("Использование: /delete [ID]\nID узнайте через /list")
        return
    pid = int(parts[1])
    props = load()
    for p in props:
        if p["id"] == pid and p.get("active"):
            p["active"] = False
            save(props)
            await msg.answer(f"✅ Объект #{pid} «{p['name']}» удалён из каталога.")
            return
    await msg.answer(f"❌ Объект #{pid} не найден.")

# ─── /stats ───────────────────────────────────
@router.message(Command("stats"))
async def cmd_stats(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    all_props   = load()
    active      = [p for p in all_props if p.get("active")]
    by_type     = {}
    for p in active:
        key = p.get("type", "—")
        by_type[key] = by_type.get(key, 0) + 1
    lines = "\n".join(f"  {k}: {v}" for k, v in by_type.items())
    await msg.answer(
        f"📊 <b>Статистика:</b>\n\n"
        f"Всего добавлено: {len(all_props)}\n"
        f"Активных: {len(active)}\n\n"
        f"По типам:\n{lines}",
        parse_mode="HTML"
    )

# ─── Web server ───────────────────────────────
MINIAPP_HTML = Path("miniapp.html")

async def api_properties(request):
    """Отдаёт список активных объектов как JSON."""
    props = [p for p in load() if p.get("active")]
    return web.json_response(props, headers={"Access-Control-Allow-Origin": "*"})

async def api_photo(request):
    """Проксирует фото из Telegram (скрывает токен бота от фронтенда)."""
    file_id = request.match_info["file_id"]
    bot: Bot = request.app["bot"]
    try:
        file = await bot.get_file(file_id)
        url  = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
        async with ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.read()
                ct   = resp.headers.get("Content-Type", "image/jpeg")
        return web.Response(body=data, content_type=ct,
                            headers={"Access-Control-Allow-Origin": "*",
                                     "Cache-Control": "public, max-age=86400"})
    except Exception as e:
        log.error(f"Photo proxy error: {e}")
        return web.Response(status=404)

async def serve_miniapp(request):
    """Отдаёт Mini App HTML."""
    if MINIAPP_HTML.exists():
        return web.Response(text=MINIAPP_HTML.read_text(encoding="utf-8"),
                            content_type="text/html")
    return web.Response(text="<h1>miniapp.html not found</h1>", content_type="text/html")

# ─── Main ─────────────────────────────────────
async def main():
    bot = Bot(token=BOT_TOKEN)
    dp  = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    # Web app
    app = web.Application()
    app["bot"] = bot
    app.router.add_get("/",                        serve_miniapp)
    app.router.add_get("/api/properties",          api_properties)
    app.router.add_get("/api/photo/{file_id}",     api_photo)

    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    log.info(f"🌐 Веб-сервер запущен на порту {PORT}")
    log.info(f"🤖 Бот запускается...")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
