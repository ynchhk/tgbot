"""
Телеграм-бот расписания СПбПУ — группа 5130903/50002
Стек: Python 3.11+, aiogram 3.x, aiohttp
"""

import asyncio
import logging
from datetime import date, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_TOKEN, GROUP_ID
from api import fetch_week, parse_lessons
from schedule_data import PERSONAL, DAY_FULL, DAY_SHORT
import workout_handlers

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher()
dp.include_router(workout_handlers.router)


# ── HELPERS ───────────────────────────────────────────────────────────────────

def get_monday(d: date) -> date:
    return d - timedelta(days=d.weekday())

def fmt_date(d: date) -> str:
    months = ['янв','фев','мар','апр','май','июн','июл','авг','сен','окт','ноя','дек']
    return f"{d.day} {months[d.month-1]}"

def fmt_time(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"

def today() -> date:
    return date.today()


# ── KEYBOARD BUILDERS ─────────────────────────────────────────────────────────

def main_keyboard(monday: date, selected_day: int) -> InlineKeyboardMarkup:
    """Главная клавиатура: строка дней + кнопки навигации по неделям."""
    builder = InlineKeyboardBuilder()

    # Строка дней (7 кнопок)
    for i, short in enumerate(DAY_SHORT):
        d = monday + timedelta(days=i)
        is_today = (d == today())
        label = f"{'•' if is_today else ''}{short}\n{fmt_date(d)}"
        active = "✓ " if i == selected_day else ""
        builder.button(
            text=f"{active}{short} {fmt_date(d)}{' 🔵' if is_today else ''}",
            callback_data=f"day:{monday.isoformat()}:{i}"
        )

    builder.adjust(4, 3)  # 4 кнопки в первой строке, 3 во второй

    # Навигация по неделям
    prev_mon = monday - timedelta(weeks=1)
    next_mon = monday + timedelta(weeks=1)
    builder.row(
        InlineKeyboardButton(text="← Пред. неделя", callback_data=f"week:{prev_mon.isoformat()}:0"),
        InlineKeyboardButton(text="Сегодня 📍",      callback_data=f"goto_today"),
        InlineKeyboardButton(text="След. неделя →",  callback_data=f"week:{next_mon.isoformat()}:0"),
    )

    return builder.as_markup()


def day_keyboard(monday: date, day_idx: int) -> InlineKeyboardMarkup:
    """Клавиатура под днём: ← → по дням, кнопка 'Вся неделя'."""
    builder = InlineKeyboardBuilder()

    prev_day = day_idx - 1
    next_day = day_idx + 1

    row = []
    if prev_day >= 0:
        row.append(InlineKeyboardButton(
            text=f"← {DAY_SHORT[prev_day]}",
            callback_data=f"day:{monday.isoformat()}:{prev_day}"
        ))
    row.append(InlineKeyboardButton(
        text="📅 Неделя",
        callback_data=f"week:{monday.isoformat()}:{day_idx}"
    ))
    if next_day <= 6:
        row.append(InlineKeyboardButton(
            text=f"{DAY_SHORT[next_day]} →",
            callback_data=f"day:{monday.isoformat()}:{next_day}"
        ))

    builder.row(*row)
    return builder.as_markup()


# ── MESSAGE FORMATTERS ────────────────────────────────────────────────────────

CAT_EMOJI = {
    'lec':   '📘',
    'prac':  '📗',
    'lab':   '🔬',
    'exam':  '📝',
    'work':  '💼',
    'hw':    '📚',
    'fe':    '💻',
    'meet':  '🤝',
    'train': '🏋️',
}
CAT_NAME = {
    'lec':   'Лекция',
    'prac':  'Практика',
    'lab':   'Лаб.',
    'exam':  'Экзамен/Зачёт',
    'work':  'Работа',
    'hw':    'ДЗ',
    'fe':    'Фронтенд',
    'meet':  'Собрание',
    'train': 'Тренировка',
}

def lesson_cat(type_str: str) -> str:
    t = (type_str or '').lower()
    if 'лек' in t: return 'lec'
    if 'лаб' in t: return 'lab'
    if 'практ' in t or 'семин' in t: return 'prac'
    if 'экзамен' in t or 'зачёт' in t or 'зачет' in t or 'комисс' in t: return 'exam'
    return 'lec'


def format_day(monday: date, day_idx: int, api_lessons: list) -> str:
    """Формирует текст расписания на день."""
    d = monday + timedelta(days=day_idx)
    is_today = (d == today())

    # Воскресенье
    if day_idx == 6:
        return (
            f"🌙 *{DAY_FULL[6]}, {fmt_date(d)}*\n\n"
            "Выходной день. Отдыхай! 🛌"
        )

    header = f"{'🔵 ' if is_today else ''}*{DAY_FULL[day_idx]}, {fmt_date(d)}*"
    if is_today:
        header += "  ← _сегодня_"

    # Собираем все события
    events = []

    # Университетское расписание
    for l in api_lessons:
        if l['dow'] == day_idx:
            events.append({
                'start': l['startMin'],
                'end':   l['endMin'],
                'name':  l['name'],
                'cat':   l['cat'],
                'sub':   ' | '.join(filter(None, [
                    l.get('type', ''),
                    l.get('teacher', ''),
                    f"ауд. {l['room']}" if l.get('room') else '',
                    l.get('bld', ''),
                ]))
            })

    # Личные события
    for p in PERSONAL:
        if p['d'] == day_idx:
            h, m = p['s'].split(':')
            eh, em = p['e'].split(':')
            events.append({
                'start': int(h)*60 + int(m),
                'end':   int(eh)*60 + int(em),
                'name':  p['name'],
                'cat':   p['cat'],
                'sub':   '',
            })

    events.sort(key=lambda x: x['start'])

    if not events:
        return f"{header}\n\n_Занятий нет_ 🎉"

    lines = [header, ""]
    for ev in events:
        emoji = CAT_EMOJI.get(ev['cat'], '📌')
        time_str = f"`{fmt_time(ev['start'])}–{fmt_time(ev['end'])}`"
        cat_str = CAT_NAME.get(ev['cat'], ev['cat'])
        lines.append(f"{emoji} {time_str}  *{ev['name']}*")
        lines.append(f"    _{cat_str}_" + (f"  •  {ev['sub']}" if ev['sub'] else ""))
        lines.append("")

    return "\n".join(lines).strip()


def format_week(monday: date, api_lessons: list) -> str:
    """Краткое расписание на всю неделю."""
    sun = monday + timedelta(days=6)
    lines = [
        f"📅 *Расписание {fmt_date(monday)} – {fmt_date(sun)}*",
        f"_Группа 5130903/50002_",
        ""
    ]

    for i in range(7):
        d = monday + timedelta(days=i)
        is_today = (d == today())
        marker = " 🔵" if is_today else ""

        day_events = []
        for l in api_lessons:
            if l['dow'] == i:
                day_events.append(f"`{fmt_time(l['startMin'])}` {l['name']}")
        for p in PERSONAL:
            if p['d'] == i:
                h, m = p['s'].split(':')
                day_events.append(f"`{p['s']}` {p['name']}")

        day_events_sorted = sorted(day_events)

        if i == 6:
            lines.append(f"*{DAY_SHORT[i]}* {fmt_date(d)}{marker} — выходной 🌙")
        elif day_events:
            lines.append(f"*{DAY_SHORT[i]}* {fmt_date(d)}{marker}")
            for ev in day_events_sorted[:5]:  # не больше 5 в краткой сводке
                lines.append(f"  {ev}")
            if len(day_events_sorted) > 5:
                lines.append(f"  _... ещё {len(day_events_sorted)-5}_")
        else:
            lines.append(f"*{DAY_SHORT[i]}* {fmt_date(d)}{marker} — _нет занятий_")

        lines.append("")

    return "\n".join(lines).strip()


# ── COMMAND HANDLERS ──────────────────────────────────────────────────────────

@dp.message(CommandStart())
async def cmd_start(msg: Message):
    await msg.answer(
        "👋 *Привет! Я бот расписания СПбПУ*\n\n"
        "Группа: `5130903/50002`\n\n"
        "*Расписание:*\n"
        "/today — расписание на сегодня\n"
        "/tomorrow — на завтра\n"
        "/week — текущая неделя\n"
        "/monday, /tuesday … /sunday — конкретный день\n\n"
        "*Тренировки (военная кафедра):*\n"
        "/workout — план тренировок\n"
        "/norms — нормативы\n"
        "/nutrition — план питания\n"
        "/result — записать результат\n\n"
        "/help — полная справка",
        parse_mode="Markdown"
    )
    await send_today(msg)


@dp.message(Command("help"))
async def cmd_help(msg: Message):
    await msg.answer(
        "📖 *Команды бота*\n\n"
        "*Расписание:*\n"
        "/today — сегодня\n"
        "/tomorrow — завтра\n"
        "/week — вся неделя\n"
        "/monday — понедельник\n"
        "/tuesday — вторник\n"
        "/wednesday — среда\n"
        "/thursday — четверг\n"
        "/friday — пятница\n"
        "/saturday — суббота\n"
        "/sunday — воскресенье\n\n"
        "*Тренировки (военная кафедра):*\n"
        "/workout — весь план по месяцам\n"
        "/norms — нормативы с баллами\n"
        "/nutrition — план питания\n"
        "/result [название] [значение] — записать результат\n"
        "  Пример: `/result подтягивания 8`\n"
        "/cancel — отменить ввод веса\n\n"
        "В расписании — кнопки ← → для перехода между днями.\n"
        "В тренировках — кнопка 'Записать веса' для сохранения рабочих весов.",
        parse_mode="Markdown"
    )


@dp.message(Command("today"))
async def cmd_today(msg: Message):
    await send_today(msg)


@dp.message(Command("tomorrow"))
async def cmd_tomorrow(msg: Message):
    t = today() + timedelta(days=1)
    monday = get_monday(t)
    dow = t.weekday()
    await send_day(msg, monday, dow)


@dp.message(Command("week"))
async def cmd_week(msg: Message):
    monday = get_monday(today())
    await send_week(msg, monday)


# Команды по дням недели
DAY_COMMANDS = {
    "monday":    0,
    "tuesday":   1,
    "wednesday": 2,
    "thursday":  3,
    "friday":    4,
    "saturday":  5,
    "sunday":    6,
}

@dp.message(Command(*DAY_COMMANDS.keys()))
async def cmd_weekday(msg: Message):
    cmd = msg.text.lstrip('/').split('@')[0].lower()
    dow = DAY_COMMANDS[cmd]
    # Ищем ближайший такой день (текущая или следующая неделя)
    t = today()
    current_dow = t.weekday()
    delta = (dow - current_dow) % 7
    target = t + timedelta(days=delta)
    monday = get_monday(target)
    await send_day(msg, monday, dow)


# ── SENDERS ───────────────────────────────────────────────────────────────────

async def send_today(msg: Message):
    t = today()
    monday = get_monday(t)
    dow = t.weekday()
    await send_day(msg, monday, dow)


async def send_day(msg: Message, monday: date, day_idx: int, edit=False):
    lessons = await load_lessons(monday)
    text = format_day(monday, day_idx, lessons)
    kb = day_keyboard(monday, day_idx)
    if edit and hasattr(msg, 'edit_text'):
        await msg.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    else:
        await msg.answer(text, parse_mode="Markdown", reply_markup=kb)


async def send_week(msg: Message, monday: date):
    lessons = await load_lessons(monday)
    text = format_week(monday, lessons)
    kb = main_keyboard(monday, today().weekday() if get_monday(today()) == monday else 0)
    await msg.answer(text, parse_mode="Markdown", reply_markup=kb)


async def load_lessons(monday: date) -> list:
    try:
        raw = await fetch_week(monday.isoformat())
        return parse_lessons(raw)
    except Exception as e:
        log.error(f"API error: {e}")
        return []


# ── CALLBACK HANDLERS ─────────────────────────────────────────────────────────

@dp.callback_query(F.data.startswith("day:"))
async def cb_day(call: CallbackQuery):
    _, mon_str, day_str = call.data.split(":")
    monday = date.fromisoformat(mon_str)
    day_idx = int(day_str)

    lessons = await load_lessons(monday)
    text = format_day(monday, day_idx, lessons)
    kb = day_keyboard(monday, day_idx)

    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await call.answer()


@dp.callback_query(F.data.startswith("week:"))
async def cb_week(call: CallbackQuery):
    _, mon_str, _ = call.data.split(":")
    monday = date.fromisoformat(mon_str)

    lessons = await load_lessons(monday)
    text = format_week(monday, lessons)
    kb = main_keyboard(monday, today().weekday() if get_monday(today()) == monday else 0)

    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await call.answer()


@dp.callback_query(F.data == "goto_today")
async def cb_today(call: CallbackQuery):
    monday = get_monday(today())
    dow = today().weekday()

    lessons = await load_lessons(monday)
    text = format_day(monday, dow, lessons)
    kb = day_keyboard(monday, dow)

    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await call.answer("Перехожу на сегодня 📍")


# ── MAIN ──────────────────────────────────────────────────────────────────────

async def main():
    log.info("Бот запускается…")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
