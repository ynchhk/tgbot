import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
Application, CommandHandler, CallbackQueryHandler,
MessageHandler, filters, ContextTypes, ConversationHandler
)

TOKEN = “8697824599:AAFBD2Cb02ztkbCXYYq5NdakFLh-mKR688g”

# ── ДАННЫЕ ПЛАНА ─────────────────────────────────────────────────────────────

PLAN = [
{
“id”: 0, “label”: “Март–Апрель”, “period”: “Недели 1–8”, “theme”: “Фундамент”,
“goal”: “Научить тело двигаться. Первое подтягивание. Бег без остановок 15 мин.”,
“targets”: [“Подтягивания: 1–3”, “Бег 3 км: ~17 мин”, “Бег 100 м: ~16 сек”],
“days”: [
{
“day”: “Понедельник”, “tag”: “Верх тела”, “duration”: 65,
“exercises”: [
{“name”: “Разминка”, “sets”: “5 мин”, “reps”: “суставная гимнастика”, “note”: “”, “no_weight”: True},
{“name”: “Тяга верхнего блока широким хватом”, “sets”: “4”, “reps”: “10”, “note”: “Локти вниз и назад, тяни к верхней груди”},
{“name”: “Тяга нижнего блока обратным хватом”, “sets”: “3”, “reps”: “10”, “note”: “Ладони к себе — имитация турника. Спина прямая”},
{“name”: “Жим гантелей лёжа”, “sets”: “3”, “reps”: “12”, “note”: “Лёгкий вес, отработка техники”},
{“name”: “Тяга блока к поясу сидя”, “sets”: “3”, “reps”: “12”, “note”: “Та же мышца что и подтягивание”},
{“name”: “Отжимания от пола”, “sets”: “3”, “reps”: “MAX”, “note”: “”, “no_weight”: True},
{“name”: “Планка”, “sets”: “3”, “reps”: “30 сек”, “note”: “”, “no_weight”: True},
],
},
{
“day”: “Среда”, “tag”: “Бег + ОФП”, “duration”: 60,
“exercises”: [
{“name”: “Разминка”, “sets”: “5 мин”, “reps”: “лёгкая ходьба”, “note”: “”, “no_weight”: True},
{“name”: “Бег/Ходьба чередование”, “sets”: “25 мин”, “reps”: “1 мин бег + 2 мин шаг”, “note”: “Должен мочь говорить во время бега”, “no_weight”: True},
{“name”: “Приседания со штангой / гантелями”, “sets”: “3”, “reps”: “15”, “note”: “Лёгкий вес, следи за коленями”},
{“name”: “Выпады с гантелями”, “sets”: “3”, “reps”: “12 на ногу”, “note”: “”},
{“name”: “Подъём ног в висе”, “sets”: “3”, “reps”: “10”, “note”: “Пресс + хват”, “no_weight”: True},
],
},
{
“day”: “Пятница”, “tag”: “Верх + скорость”, “duration”: 70,
“exercises”: [
{“name”: “Разминка”, “sets”: “5 мин”, “reps”: “суставная гимнастика”, “note”: “”, “no_weight”: True},
{“name”: “Тяга верхнего блока широким хватом”, “sets”: “4”, “reps”: “12”, “note”: “Добавь 2,5–5 кг если Пн был лёгким”},
{“name”: “Тяга гантели одной рукой”, “sets”: “3”, “reps”: “12 на руку”, “note”: “Ключевое упражнение для спины”},
{“name”: “Жим гантелей / штанги стоя”, “sets”: “3”, “reps”: “10”, “note”: “”},
{“name”: “Ускорения 60 м”, “sets”: “6”, “reps”: “по 60 м”, “note”: “Отдых 3 мин, 80% усилий”, “no_weight”: True},
{“name”: “Скручивания на пресс”, “sets”: “3”, “reps”: “20”, “note”: “”, “no_weight”: True},
],
},
],
},
{
“id”: 1, “label”: “Май–Июнь”, “period”: “Недели 9–16”, “theme”: “Прогресс”,
“goal”: “5–6 подтягиваний без помощи. Бег 3 км без остановок. 100 м за 14,8 сек.”,
“targets”: [“Подтягивания: 5–6”, “Бег 3 км: ~14:30”, “Бег 100 м: ~15 сек”],
“days”: [
{
“day”: “Понедельник”, “tag”: “Подтягивания + верх”, “duration”: 75,
“exercises”: [
{“name”: “Разминка”, “sets”: “5 мин”, “reps”: “”, “note”: “”, “no_weight”: True},
{“name”: “Тяга верхнего блока широким хватом”, “sets”: “5”, “reps”: “8”, “note”: “Когда потянешь 70–75 кг — придут подтягивания”},
{“name”: “Тяга нижнего блока обратным хватом”, “sets”: “3”, “reps”: “8”, “note”: “Та же механика что на турнике”},
{“name”: “Тяга горизонтального блока”, “sets”: “3”, “reps”: “12”, “note”: “”},
{“name”: “Отжимания ноги на скамье”, “sets”: “3”, “reps”: “12”, “note”: “Сложнее обычных — качает плечи”, “no_weight”: True},
{“name”: “Планка + боковая планка”, “sets”: “3”, “reps”: “40 сек каждая”, “note”: “”, “no_weight”: True},
],
},
{
“day”: “Среда”, “tag”: “Бег (объём)”, “duration”: 65,
“exercises”: [
{“name”: “Разминка”, “sets”: “5 мин”, “reps”: “лёгкий бег”, “note”: “”, “no_weight”: True},
{“name”: “Непрерывный бег”, “sets”: “1”, “reps”: “25–30 мин”, “note”: “Темп 6:30–7:00 мин/км. Дыши через нос”, “no_weight”: True},
{“name”: “Приседания с весом”, “sets”: “4”, “reps”: “12”, “note”: “”},
{“name”: “Жим ногами”, “sets”: “3”, “reps”: “15”, “note”: “”},
{“name”: “Икры (подъём на носки)”, “sets”: “4”, “reps”: “20”, “note”: “Важно для бега”, “no_weight”: True},
],
},
{
“day”: “Пятница”, “tag”: “Скорость + сила”, “duration”: 80,
“exercises”: [
{“name”: “Разминка”, “sets”: “10 мин”, “reps”: “динамическая растяжка”, “note”: “”, “no_weight”: True},
{“name”: “Тяга верхнего блока обратным хватом”, “sets”: “4”, “reps”: “8”, “note”: “Обратный хват сильнее включает бицепс”},
{“name”: “Ускорения 80 м”, “sets”: “8”, “reps”: “по 80 м”, “note”: “Отдых 3 мин. Работай над первыми 30 м”, “no_weight”: True},
{“name”: “Становая тяга лёгкая”, “sets”: “3”, “reps”: “10”, “note”: “Задняя поверхность бедра — нужна для бега”},
{“name”: “Подъём ног в висе”, “sets”: “4”, “reps”: “12”, “note”: “”, “no_weight”: True},
],
},
],
},
{
“id”: 2, “label”: “Июль”, “period”: “Недели 17–21”, “theme”: “Специализация”,
“goal”: “8–10 подтягиваний. 3 км за 13:30. 100 м за 14,3–14,5 сек.”,
“targets”: [“Подтягивания: 8–10”, “Бег 3 км: ~13:30”, “Бег 100 м: ~14,5 сек”],
“days”: [
{
“day”: “Понедельник”, “tag”: “Подтягивания MAX”, “duration”: 70,
“exercises”: [
{“name”: “Разминка”, “sets”: “5 мин”, “reps”: “”, “note”: “”, “no_weight”: True},
{“name”: “Подтягивания — 5 подходов на MAX”, “sets”: “5”, “reps”: “MAX”, “note”: “Записывай каждый подход. Отдых 3–4 мин”, “no_weight”: True},
{“name”: “Подтягивания обратным хватом”, “sets”: “3”, “reps”: “MAX”, “note”: “Сразу после основных”, “no_weight”: True},
{“name”: “Тяга нижнего блока”, “sets”: “3”, “reps”: “10”, “note”: “”},
{“name”: “Разведение гантелей лёжа”, “sets”: “3”, “reps”: “12”, “note”: “”},
{“name”: “Скручивания + планка”, “sets”: “3”, “reps”: “20 + 50 сек”, “note”: “”, “no_weight”: True},
],
},
{
“day”: “Среда”, “tag”: “Бег 3 км темповой”, “duration”: 60,
“exercises”: [
{“name”: “Разминка”, “sets”: “10 мин”, “reps”: “лёгкий бег + динамика”, “note”: “”, “no_weight”: True},
{“name”: “Темповой бег 3 км”, “sets”: “1”, “reps”: “засеки время!”, “note”: “Беги в соревновательном темпе — терпи!”, “no_weight”: True},
{“name”: “Заминка”, “sets”: “5 мин”, “reps”: “лёгкий бег”, “note”: “”, “no_weight”: True},
{“name”: “Выпады с ходьбой”, “sets”: “3”, “reps”: “15 на ногу”, “note”: “”},
{“name”: “Ягодичный мост со штангой”, “sets”: “3”, “reps”: “15”, “note”: “Мощные ягодицы = быстрый бег”},
],
},
{
“day”: “Пятница”, “tag”: “Спринт + ОФП”, “duration”: 75,
“exercises”: [
{“name”: “Разминка”, “sets”: “10 мин”, “reps”: “суставная + 3 × 30 м”, “note”: “”, “no_weight”: True},
{“name”: “Спринт 100 м контрольный”, “sets”: “1”, “reps”: “засеки!”, “note”: “Замер раз в 2 недели”, “no_weight”: True},
{“name”: “Ускорения 80–100 м”, “sets”: “6”, “reps”: “по 100 м”, “note”: “Отдых 4 мин. Работай руками”, “no_weight”: True},
{“name”: “Тяга штанги в наклоне”, “sets”: “4”, “reps”: “8”, “note”: “”},
{“name”: “Подъём ног в висе”, “sets”: “4”, “reps”: “15”, “note”: “”, “no_weight”: True},
],
},
],
},
{
“id”: 3, “label”: “Август”, “period”: “Недели 22–26”, “theme”: “Выход на пик”,
“goal”: “10+ подтягиваний. 3 км за 13:00. 100 м за 14,0–14,2 сек. Пробная сдача.”,
“targets”: [“Подтягивания: 10+”, “Бег 3 км: ~13:00”, “Бег 100 м: ~14,0–14,2 сек”],
“days”: [
{
“day”: “Понедельник”, “tag”: “Подтягивания пик”, “duration”: 65,
“exercises”: [
{“name”: “Разминка”, “sets”: “5 мин”, “reps”: “”, “note”: “”, “no_weight”: True},
{“name”: “Подтягивания пирамида”, “sets”: “5”, “reps”: “1-2-3-4-5-4-3-2-1”, “note”: “Отдых 30 сек между ступенями”, “no_weight”: True},
{“name”: “Подтягивания с отягощением”, “sets”: “3”, “reps”: “3–5”, “note”: “Если 10 раз легко — добавь 5–10 кг в рюкзак”, “no_weight”: True},
{“name”: “Тяга верхнего блока”, “sets”: “3”, “reps”: “8”, “note”: “”},
{“name”: “Планка 1 мин”, “sets”: “3”, “reps”: “1 мин”, “note”: “”, “no_weight”: True},
],
},
{
“day”: “Среда”, “tag”: “Пробная сдача”, “duration”: 90,
“exercises”: [
{“name”: “Разминка”, “sets”: “15 мин”, “reps”: “бег + динамика”, “note”: “Как на настоящей сдаче”, “no_weight”: True},
{“name”: “Подтягивания — МАКСИМУМ”, “sets”: “1”, “reps”: “MAX”, “note”: “Запиши результат!”, “no_weight”: True},
{“name”: “Отдых 15 мин”, “sets”: “—”, “reps”: “—”, “note”: “”, “no_weight”: True},
{“name”: “Бег 100 м — МАКСИМУМ”, “sets”: “1”, “reps”: “засеки!”, “note”: “Запиши результат!”, “no_weight”: True},
{“name”: “Отдых 30 мин”, “sets”: “—”, “reps”: “—”, “note”: “”, “no_weight”: True},
{“name”: “Бег 3 км — МАКСИМУМ”, “sets”: “1”, “reps”: “засеки!”, “note”: “Запиши результат!”, “no_weight”: True},
],
},
{
“day”: “Пятница”, “tag”: “Скорость + восстановление”, “duration”: 55,
“exercises”: [
{“name”: “Разминка”, “sets”: “10 мин”, “reps”: “”, “note”: “”, “no_weight”: True},
{“name”: “Ускорения 60 м”, “sets”: “6”, “reps”: “60 м”, “note”: “Максимальная скорость, отдых 3 мин”, “no_weight”: True},
{“name”: “Лёгкий бег”, “sets”: “1”, “reps”: “20 мин”, “note”: “Пульс не выше 140”, “no_weight”: True},
{“name”: “Растяжка и МФР роллером”, “sets”: “15 мин”, “reps”: “”, “note”: “Квадрицепс, икры, спина”, “no_weight”: True},
],
},
],
},
{
“id”: 4, “label”: “Сентябрь”, “period”: “Недели 27–28”, “theme”: “Заточка”,
“goal”: “Восстановиться, не перегореть. Войти на отбор свежим и уверенным.”,
“targets”: [“Нагрузка: вдвое меньше”, “Цель: свежесть и уверенность”],
“days”: [
{
“day”: “Понедельник”, “tag”: “Лёгкая поддержка”, “duration”: 40,
“exercises”: [
{“name”: “Подтягивания”, “sets”: “3”, “reps”: “50% от MAX”, “note”: “Нагрузка вдвое — тело отдыхает”, “no_weight”: True},
{“name”: “Тяга верхнего блока”, “sets”: “2”, “reps”: “10”, “note”: “”},
{“name”: “Отжимания”, “sets”: “2”, “reps”: “15”, “note”: “”, “no_weight”: True},
{“name”: “Планка”, “sets”: “2”, “reps”: “45 сек”, “note”: “”, “no_weight”: True},
],
},
{
“day”: “Среда”, “tag”: “Бег поддерживающий”, “duration”: 30,
“exercises”: [
{“name”: “Лёгкий бег”, “sets”: “1”, “reps”: “20 мин”, “note”: “Напоминание мышцам, не тренировка”, “no_weight”: True},
{“name”: “Ускорения 60 м”, “sets”: “3”, “reps”: “60 м”, “note”: “Почувствовать скорость. Не вымотаться”, “no_weight”: True},
],
},
{
“day”: “За 3 дня до отбора”, “tag”: “СТОП”, “duration”: 20,
“exercises”: [
{“name”: “Полный отдых”, “sets”: “—”, “reps”: “—”, “note”: “Никаких тренировок. Сон 8–9 часов”, “no_weight”: True},
{“name”: “Прогулка 20–30 мин”, “sets”: “1”, “reps”: “—”, “note”: “Снять нервное напряжение”, “no_weight”: True},
],
},
],
},
]

NORMS = {
“pullups”: [
(30, “5”), (42, “8”), (50, “10”), (58, “12”), (66, “14”),
(70, “15”), (76, “18”), (80, “20”), (90, “25”), (100, “30+”),
],
“run100”: [
(30, “15,0”), (40, “14,4”), (48, “14,0”), (60, “13,6”),
(70, “13,0”), (80, “12,8”), (90, “12,3”), (100, “11,8”),
],
“run3k”: [
(30, “14:10”), (40, “13:10”), (50, “12:24”), (60, “11:54”),
(70, “11:18”), (80, “10:48”), (90, “10:19”), (100, “9:50”),
],
}

# ── ХРАНИЛИЩЕ ДАННЫХ ────────────────────────────────────────────────────────

# Данные хранятся в памяти (словарь user_id -> data)

# Для постоянного хранения — заменить на SQLite или JSON-файл

user_data_store: dict = {}

def get_user_data(uid: int) -> dict:
if uid not in user_data_store:
user_data_store[uid] = {“weights”: {}, “results”: {}}
return user_data_store[uid]

def weight_key(month_i: int, day_i: int, ex_i: int) -> str:
return f”m{month_i}_d{day_i}_e{ex_i}”

# ── СОСТОЯНИЯ ────────────────────────────────────────────────────────────────

WAITING_WEIGHT = 1
WAITING_RESULT = 2

# ── ВСПОМОГАТЕЛЬНЫЕ ──────────────────────────────────────────────────────────

def fmt_duration(mins: int) -> str:
if mins >= 60:
h, m = divmod(mins, 60)
return f”{h} ч {m} мин” if m else f”{h} ч”
return f”{mins} мин”

def month_menu_kb() -> InlineKeyboardMarkup:
rows = []
for m in PLAN:
rows.append([InlineKeyboardButton(
f”{’📍 ’ if m[‘id’] == 0 else ‘’}{m[‘label’]} — {m[‘theme’]}”,
callback_data=f”month_{m[‘id’]}”
)])
rows.append([InlineKeyboardButton(“📊 Мои результаты”, callback_data=“my_results”)])
rows.append([InlineKeyboardButton(“🎯 Нормативы”, callback_data=“norms”)])
return InlineKeyboardMarkup(rows)

def day_menu_kb(month_i: int) -> InlineKeyboardMarkup:
m = PLAN[month_i]
rows = []
for di, d in enumerate(m[“days”]):
rows.append([InlineKeyboardButton(
f”{d[‘day’]} — {d[‘tag’]} ({fmt_duration(d[‘duration’])})”,
callback_data=f”day_{month_i}_{di}”
)])
rows.append([InlineKeyboardButton(“◀️ Назад к месяцам”, callback_data=“back_months”)])
return InlineKeyboardMarkup(rows)

def exercises_kb(month_i: int, day_i: int, uid: int) -> InlineKeyboardMarkup:
ud = get_user_data(uid)
m = PLAN[month_i]
d = m[“days”][day_i]
rows = []
for ei, ex in enumerate(d[“exercises”]):
if ex.get(“no_weight”):
continue
key = weight_key(month_i, day_i, ei)
saved = ud[“weights”].get(key)
label = f”✅ {ex[‘name’][:22]}: {saved} кг” if saved else f”+ {ex[‘name’][:28]}”
rows.append([InlineKeyboardButton(label, callback_data=f”setw_{month_i}*{day_i}*{ei}”)])
rows.append([InlineKeyboardButton(“◀️ Назад к дням”, callback_data=f”month_{month_i}”)])
return InlineKeyboardMarkup(rows)

def format_workout(month_i: int, day_i: int, uid: int) -> str:
ud = get_user_data(uid)
m = PLAN[month_i]
d = m[“days”][day_i]
lines = [
f”*{d[‘day’]} — {d[‘tag’]}*”,
f”⏱ Время: *{fmt_duration(d[‘duration’])}*\n”,
]
for ei, ex in enumerate(d[“exercises”]):
key = weight_key(month_i, day_i, ei)
saved = ud[“weights”].get(key)
weight_str = f”  💾 *мой вес: {saved} кг*” if saved else “”
name = f”*{ex[‘name’]}*”
sets_reps = “”
if ex[“sets”] not in (””, “—”):
sets_reps += f”  {ex[‘sets’]} подх.”
if ex[“reps”] not in (””, “—”):
sets_reps += f” × {ex[‘reps’]}”
note = f”\n   *{ex[‘note’]}*” if ex[“note”] else “”
lines.append(f”{’🔥 ’ if ei == 0 else ’▸ ’}{name}{sets_reps}{weight_str}{note}”)
return “\n”.join(lines)

# ── ХЭНДЛЕРЫ ────────────────────────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
text = (
“💪 *Бот подготовки к военной кафедре*\n\n”
“Рост 175 · Вес 78 кг · 3 тренировки в неделю\n\n”
“🎯 *Нормативы (цель к сентябрю):*\n”
“▸ Подтягивания: 10+ раз\n”
“▸ Бег 100 м: ≤14,4 сек\n”
“▸ Бег 3 км: ≤13:10\n\n”
“Выбери период:”
)
await update.message.reply_text(text, parse_mode=“Markdown”, reply_markup=month_menu_kb())

async def cb_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
data = query.data
uid = query.from_user.id

```
# ── Назад к месяцам
if data == "back_months":
    await query.edit_message_text(
        "Выбери период:", reply_markup=month_menu_kb()
    )
    return

# ── Выбор месяца
if data.startswith("month_"):
    month_i = int(data.split("_")[1])
    m = PLAN[month_i]
    text = (
        f"*{m['label']} — {m['theme']}*\n"
        f"_{m['period']}_\n\n"
        f"🎯 {m['goal']}\n\n"
        f"*Ориентиры к концу периода:*\n" +
        "\n".join(f"  ▸ {t}" for t in m["targets"]) +
        "\n\nВыбери день:"
    )
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=day_menu_kb(month_i))
    return

# ── Выбор дня
if data.startswith("day_"):
    _, month_i, day_i = data.split("_")
    month_i, day_i = int(month_i), int(day_i)
    text = format_workout(month_i, day_i, uid)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💾 Записать веса", callback_data=f"weights_{month_i}_{day_i}")],
        [InlineKeyboardButton("◀️ Назад к дням", callback_data=f"month_{month_i}")],
    ])
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=kb)
    return

# ── Меню весов
if data.startswith("weights_"):
    _, month_i, day_i = data.split("_")
    month_i, day_i = int(month_i), int(day_i)
    m = PLAN[month_i]
    d = m["days"][day_i]
    has_weights = any(not ex.get("no_weight") for ex in d["exercises"])
    if not has_weights:
        await query.answer("В этой тренировке нет упражнений с весом", show_alert=True)
        return
    await query.edit_message_text(
        f"💾 *Записать веса — {d['day']}*\n\nНажми на упражнение чтобы обновить вес:",
        parse_mode="Markdown",
        reply_markup=exercises_kb(month_i, day_i, uid)
    )
    return

# ── Выбор конкретного упражнения для записи веса
if data.startswith("setw_"):
    parts = data.split("_")
    month_i, day_i, ex_i = int(parts[1]), int(parts[2]), int(parts[3])
    ex = PLAN[month_i]["days"][day_i]["exercises"][ex_i]
    ud = get_user_data(uid)
    key = weight_key(month_i, day_i, ex_i)
    current = ud["weights"].get(key, "не записан")
    ctx.user_data["pending_weight"] = (month_i, day_i, ex_i)
    await query.edit_message_text(
        f"✏️ *{ex['name']}*\n\n"
        f"Текущий вес: _{current}_\n\n"
        f"Напиши новый вес в кг (например: *45*)\n"
        f"или /cancel для отмены",
        parse_mode="Markdown"
    )
    return ConversationHandler.END  # не через ConversationHandler, ловим в message

# ── Мои результаты
if data == "my_results":
    ud = get_user_data(uid)
    res = ud.get("results", {})
    if not res:
        text = (
            "📊 *Мои результаты*\n\n"
            "Ещё нет записей.\n\n"
            "Используй /result чтобы записать результат сдачи нормативов.\n"
            "Например: /result подтягивания 8"
        )
    else:
        lines = ["📊 *Мои результаты:*\n"]
        for k, v in sorted(res.items()):
            lines.append(f"▸ {k}: *{v}*")
        text = "\n".join(lines)
    await query.edit_message_text(text, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back_months")]]))
    return

# ── Нормативы
if data == "norms":
    text = (
        "🎯 *Нормативы военной кафедры*\n\n"
        "*Подтягивания:*\n"
        "  ▸ Минимум (30 б): 5 раз\n"
        "  ▸ Хорошо (50 б): 10 раз\n"
        "  ▸ Отлично (76 б): 18 раз\n\n"
        "*Бег 100 м:*\n"
        "  ▸ Минимум (30 б): 15,0 сек\n"
        "  ▸ Хорошо (48 б): 14,0 сек\n"
        "  ▸ Отлично (76 б): 13,0 сек\n\n"
        "*Бег 3 км:*\n"
        "  ▸ Минимум (30 б): 14:10\n"
        "  ▸ Хорошо (50 б): 12:24\n"
        "  ▸ Отлично (76 б): 11:18\n\n"
        "Минимальный проходной балл: *120 очков суммарно*\n"
        "_(не менее 30 баллов за каждое упражнение)_"
    )
    await query.edit_message_text(text, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back_months")]]))
    return
```

async def message_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
“”“Ловим текстовые сообщения — запись веса”””
uid = update.effective_user.id
text = update.message.text.strip()

```
if text.startswith("/"):
    return  # команды обрабатываются отдельно

pending = ctx.user_data.get("pending_weight")
if pending:
    month_i, day_i, ex_i = pending
    ex = PLAN[month_i]["days"][day_i]["exercises"][ex_i]
    try:
        val = float(text.replace(",", "."))
        if val <= 0 or val > 500:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Введи число, например *45* или *32.5*", parse_mode="Markdown")
        return
    ud = get_user_data(uid)
    key = weight_key(month_i, day_i, ex_i)
    ud["weights"][key] = text
    ctx.user_data.pop("pending_weight", None)
    await update.message.reply_text(
        f"✅ Сохранено!\n*{ex['name']}* → *{text} кг*\n\nВозвращайся к плану: /start",
        parse_mode="Markdown"
    )
    return

await update.message.reply_text(
    "Используй /start для открытия плана или /help для справки."
)
```

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
ctx.user_data.pop(“pending_weight”, None)
await update.message.reply_text(“Отменено. /start — вернуться к плану.”)

async def result_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
“””
/result подтягивания 8
/result бег100 14.5
/result бег3км 13:22
“””
uid = update.effective_user.id
args = ctx.args
if len(args) < 2:
await update.message.reply_text(
“📝 *Запись результата:*\n\n”
“Примеры:\n”
“`/result подтягивания 8`\n”
“`/result бег100 14.5`\n”
“`/result бег3км 13:22`”,
parse_mode=“Markdown”
)
return
name = args[0]
value = “ “.join(args[1:])
ud = get_user_data(uid)
ud[“results”][name] = value
await update.message.reply_text(
f”✅ Записано: *{name}* = *{value}*\n\nПосмотреть все результаты: /start → Мои результаты”,
parse_mode=“Markdown”
)

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(
“📋 *Команды бота:*\n\n”
“/start — главное меню и план тренировок\n”
“/result [название] [значение] — записать результат\n”
“  Пример: `/result подтягивания 8`\n”
“/cancel — отменить ввод веса\n”
“/help — эта справка\n\n”
“💾 *Как записать вес:*\n”
“Открой любой день → нажми «Записать веса» → выбери упражнение → введи число.”,
parse_mode=“Markdown”
)

# ── ЗАПУСК ───────────────────────────────────────────────────────────────────

def main():
app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler(“start”, start))
app.add_handler(CommandHandler(“help”, help_cmd))
app.add_handler(CommandHandler(“cancel”, cancel))
app.add_handler(CommandHandler(“result”, result_cmd))
app.add_handler(CallbackQueryHandler(cb_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
print(“Бот запущен. Ctrl+C для остановки.”)
app.run_polling()

if **name** == “**main**”:
main()