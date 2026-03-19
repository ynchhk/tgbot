# workout_handlers.py — обработчики тренировочного блока
# Подключается к основному bot.py через include_router

import json
import os
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from workout_data import PLAN, NUTRITION_MEALS, NUTRITION_RULES, NORMS_TEXT

router = Router()

# ── ХРАНИЛИЩЕ ВЕСОВ ──────────────────────────────────────────────────────────
# Файл weights.json рядом с ботом. Формат: {user_id: {"m0_d0_e1": "40", ...}}

WEIGHTS_FILE = "weights.json"

def load_all_weights() -> dict:
    if os.path.exists(WEIGHTS_FILE):
        try:
            with open(WEIGHTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_all_weights(data: dict):
    with open(WEIGHTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user_weights(uid: int) -> dict:
    all_w = load_all_weights()
    return all_w.get(str(uid), {})

def set_user_weight(uid: int, key: str, value: str):
    all_w = load_all_weights()
    uid_str = str(uid)
    if uid_str not in all_w:
        all_w[uid_str] = {}
    if value.strip() == "":
        all_w[uid_str].pop(key, None)
    else:
        all_w[uid_str][key] = value.strip()
    save_all_weights(all_w)

def wkey(month_i: int, day_i: int, ex_i: int) -> str:
    return f"m{month_i}_d{day_i}_e{ex_i}"

# Временное состояние ожидания ввода веса: {user_id: (month_i, day_i, ex_i)}
pending_weight: dict = {}

# ── ФОРМАТТЕРЫ ───────────────────────────────────────────────────────────────

def fmt_duration(mins: int) -> str:
    if mins >= 60:
        h, m = divmod(mins, 60)
        return f"{h} ч {m} мин" if m else f"{h} ч"
    return f"{mins} мин"

def format_month_menu() -> str:
    lines = ["*Выбери период подготовки:*\n"]
    for m in PLAN:
        lines.append(f"*{m['label']}* — {m['theme']}")
        lines.append(f"  _{m['period']}_")
        lines.append(f"  Цель: {m['goal']}\n")
    return "\n".join(lines)

def format_day(month_i: int, day_i: int, uid: int) -> str:
    m = PLAN[month_i]
    d = m["days"][day_i]
    weights = get_user_weights(uid)

    lines = [
        f"*{m['label']} — {m['theme']}*",
        f"_{m['period']}_\n",
        f"*{d['day']} | {d['tag']}*",
        f"Фокус: _{d['focus']}_ | Время: *{fmt_duration(d['duration'])}*\n",
    ]

    for i, ex in enumerate(d["exercises"]):
        key = wkey(month_i, day_i, i)
        saved = weights.get(key)

        # Основная строка
        sets_reps = ""
        if ex["sets"] not in ("", "-"):
            sets_reps += f"{ex['sets']} подх."
        if ex["reps"] not in ("", "-"):
            sets_reps += f" × {ex['reps']}"

        weight_str = f" 💾 _{saved} кг_" if saved else ""
        lines.append(f"{'🔥' if i == 0 else '▸'} *{ex['name']}*  {sets_reps}{weight_str}")

        # Группы мышц
        if ex.get("muscles"):
            lines.append(f"   💪 _{ex['muscles']}_")

        # Примечание
        if ex.get("note"):
            lines.append(f"   ℹ️ {ex['note']}")

        lines.append("")

    # Питание периода
    n = m["nutrition"]
    lines.append(f"─────────────────")
    lines.append(f"🍽 *Питание ({n['phase']}):* {n['kcal']} ккал | белок {n['protein']} г")
    lines.append(f"_{n['note']}_")

    return "\n".join(lines)

def format_nutrition() -> str:
    lines = ["*План питания*\n"]
    for meal in NUTRITION_MEALS:
        lines.append(f"*{meal['name']}* ({meal['time']})")
        lines.append(f"_{meal['kcal']} | белок {meal['protein']}_")
        for j, opt in enumerate(meal["options"], 1):
            lines.append(f"  Вариант {j}: {opt}")
        lines.append("")

    lines.append("*Правила:*")
    for rule in NUTRITION_RULES:
        lines.append(f"▸ {rule}")
    return "\n".join(lines)

# ── КЛАВИАТУРЫ ───────────────────────────────────────────────────────────────

def kb_months() -> InlineKeyboardBuilder:
    b = InlineKeyboardBuilder()
    for m in PLAN:
        b.button(text=f"{m['label']} — {m['theme']}", callback_data=f"wm_{m['id']}")
    b.button(text="📊 Мои результаты", callback_data="w_results")
    b.button(text="🍗 Питание", callback_data="w_nutrition")
    b.button(text="🎯 Нормативы", callback_data="w_norms")
    b.adjust(1, 1, 1, 1, 1, 2)
    return b

def kb_days(month_i: int) -> InlineKeyboardBuilder:
    m = PLAN[month_i]
    b = InlineKeyboardBuilder()
    for di, d in enumerate(m["days"]):
        b.button(
            text=f"{d['day']} — {d['tag']} ({fmt_duration(d['duration'])})",
            callback_data=f"wd_{month_i}_{di}"
        )
    b.button(text="◀️ К месяцам", callback_data="w_back_months")
    b.adjust(1)
    return b

def kb_day_actions(month_i: int, day_i: int, uid: int) -> InlineKeyboardBuilder:
    m = PLAN[month_i]
    d = m["days"][day_i]
    b = InlineKeyboardBuilder()

    # Кнопки для упражнений с весом
    weights = get_user_weights(uid)
    has_weight_ex = any(not ex.get("no_weight") for ex in d["exercises"])
    if has_weight_ex:
        b.button(text="💾 Записать веса", callback_data=f"wweights_{month_i}_{day_i}")

    b.button(text="◀️ К дням", callback_data=f"wm_{month_i}")
    b.adjust(1)
    return b

def kb_exercises(month_i: int, day_i: int, uid: int) -> InlineKeyboardBuilder:
    d = PLAN[month_i]["days"][day_i]
    weights = get_user_weights(uid)
    b = InlineKeyboardBuilder()
    for ei, ex in enumerate(d["exercises"]):
        if ex.get("no_weight"):
            continue
        key = wkey(month_i, day_i, ei)
        saved = weights.get(key)
        label = f"✅ {ex['name'][:25]}: {saved} кг" if saved else f"+ {ex['name'][:30]}"
        b.button(text=label, callback_data=f"wsetw_{month_i}_{day_i}_{ei}")
    b.button(text="◀️ Назад", callback_data=f"wd_{month_i}_{day_i}")
    b.adjust(1)
    return b

# ── ХЭНДЛЕРЫ ─────────────────────────────────────────────────────────────────

@router.message(Command("workout"))
async def cmd_workout(msg: Message):
    await msg.answer(
        "*Тренировки — военная кафедра*\n\n"
        "Цели: 10+ подтягиваний | 100 м ≤14,4 сек | 3 км ≤13:10\n"
        "Бонус: V-силуэт + минус 5-7 кг жира\n\n"
        "Выбери период:",
        parse_mode="Markdown",
        reply_markup=kb_months().as_markup()
    )

@router.message(Command("norms"))
async def cmd_norms(msg: Message):
    b = InlineKeyboardBuilder()
    b.button(text="🏋️ К тренировкам", callback_data="w_back_months")
    await msg.answer(
        f"*{NORMS_TEXT}*" if False else NORMS_TEXT,
        parse_mode="Markdown",
        reply_markup=b.as_markup()
    )

@router.message(Command("nutrition"))
async def cmd_nutrition(msg: Message):
    b = InlineKeyboardBuilder()
    b.button(text="🏋️ К тренировкам", callback_data="w_back_months")
    await msg.answer(
        format_nutrition(),
        parse_mode="Markdown",
        reply_markup=b.as_markup()
    )

@router.message(Command("result"))
async def cmd_result(msg: Message):
    args = msg.text.split(maxsplit=2)
    if len(args) < 3:
        await msg.answer(
            "*Запись результата:*\n\n"
            "Примеры:\n"
            "`/result подтягивания 8`\n"
            "`/result бег100 14.5`\n"
            "`/result бег3км 13:22`\n\n"
            "Смотреть: /workout → Мои результаты",
            parse_mode="Markdown"
        )
        return

    name, value = args[1], args[2]
    all_w = load_all_weights()
    uid_str = str(msg.from_user.id)
    if uid_str not in all_w:
        all_w[uid_str] = {}
    all_w[uid_str][f"result_{name}"] = value
    save_all_weights(all_w)
    await msg.answer(
        f"Записано: *{name}* = *{value}*",
        parse_mode="Markdown"
    )

# ── CALLBACK ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "w_back_months")
async def cb_back_months(call: CallbackQuery):
    await call.message.edit_text(
        "*Тренировки — военная кафедра*\n\nВыбери период:",
        parse_mode="Markdown",
        reply_markup=kb_months().as_markup()
    )
    await call.answer()

@router.callback_query(F.data.startswith("wm_"))
async def cb_month(call: CallbackQuery):
    month_i = int(call.data.split("_")[1])
    m = PLAN[month_i]
    text = (
        f"*{m['label']} — {m['theme']}*\n"
        f"_{m['period']}_\n\n"
        f"Цель: {m['goal']}\n\n"
        + "\n".join(f"▸ {t}" for t in m["targets"])
        + f"\n\n🍽 Питание: *{m['nutrition']['phase']}* — "
        + f"{m['nutrition']['kcal']} ккал | белок {m['nutrition']['protein']} г\n"
        + f"_{m['nutrition']['note']}_\n\n"
        + "Выбери день:"
    )
    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=kb_days(month_i).as_markup())
    await call.answer()

@router.callback_query(F.data.startswith("wd_"))
async def cb_day(call: CallbackQuery):
    parts = call.data.split("_")
    month_i, day_i = int(parts[1]), int(parts[2])
    uid = call.from_user.id
    text = format_day(month_i, day_i, uid)
    kb = kb_day_actions(month_i, day_i, uid)
    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=kb.as_markup())
    await call.answer()

@router.callback_query(F.data.startswith("wweights_"))
async def cb_weights_menu(call: CallbackQuery):
    parts = call.data.split("_")
    month_i, day_i = int(parts[1]), int(parts[2])
    uid = call.from_user.id
    d = PLAN[month_i]["days"][day_i]
    await call.message.edit_text(
        f"*Записать веса — {d['day']}*\n\nНажми на упражнение:",
        parse_mode="Markdown",
        reply_markup=kb_exercises(month_i, day_i, uid).as_markup()
    )
    await call.answer()

@router.callback_query(F.data.startswith("wsetw_"))
async def cb_set_weight(call: CallbackQuery):
    parts = call.data.split("_")
    month_i, day_i, ex_i = int(parts[1]), int(parts[2]), int(parts[3])
    uid = call.from_user.id
    ex = PLAN[month_i]["days"][day_i]["exercises"][ex_i]
    saved = get_user_weights(uid).get(wkey(month_i, day_i, ex_i), "не записан")

    pending_weight[uid] = (month_i, day_i, ex_i)

    await call.message.edit_text(
        f"*{ex['name']}*\n"
        f"Текущий вес: _{saved}_\n\n"
        f"Напиши вес в кг (например: *45*)\n"
        f"или /cancel для отмены",
        parse_mode="Markdown"
    )
    await call.answer()

@router.callback_query(F.data == "w_results")
async def cb_results(call: CallbackQuery):
    uid = call.from_user.id
    all_w = load_all_weights()
    user_data = all_w.get(str(uid), {})
    results = {k: v for k, v in user_data.items() if k.startswith("result_")}

    if not results:
        text = (
            "*Мои результаты*\n\n"
            "Ещё нет записей.\n\n"
            "Используй: `/result подтягивания 8`"
        )
    else:
        lines = ["*Мои результаты:*\n"]
        for k, v in sorted(results.items()):
            name = k.replace("result_", "")
            lines.append(f"▸ {name}: *{v}*")
        text = "\n".join(lines)

    b = InlineKeyboardBuilder()
    b.button(text="◀️ К тренировкам", callback_data="w_back_months")
    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=b.as_markup())
    await call.answer()

@router.callback_query(F.data == "w_nutrition")
async def cb_nutrition(call: CallbackQuery):
    b = InlineKeyboardBuilder()
    b.button(text="◀️ К тренировкам", callback_data="w_back_months")
    await call.message.edit_text(
        format_nutrition(),
        parse_mode="Markdown",
        reply_markup=b.as_markup()
    )
    await call.answer()

@router.callback_query(F.data == "w_norms")
async def cb_norms(call: CallbackQuery):
    b = InlineKeyboardBuilder()
    b.button(text="◀️ К тренировкам", callback_data="w_back_months")
    await call.message.edit_text(
        NORMS_TEXT,
        parse_mode="Markdown",
        reply_markup=b.as_markup()
    )
    await call.answer()

# ── ВВОД ВЕСА (текстовое сообщение) ──────────────────────────────────────────

@router.message(Command("cancel"))
async def cmd_cancel(msg: Message):
    pending_weight.pop(msg.from_user.id, None)
    await msg.answer("Отменено. /workout — вернуться к тренировкам.")

@router.message(F.text & ~F.text.startswith("/"))
async def handle_weight_input(msg: Message):
    uid = msg.from_user.id
    if uid not in pending_weight:
        return  # не наш — пусть основной бот обрабатывает

    month_i, day_i, ex_i = pending_weight[uid]
    ex = PLAN[month_i]["days"][day_i]["exercises"][ex_i]
    text = msg.text.strip().replace(",", ".")

    try:
        val = float(text)
        if val <= 0 or val > 500:
            raise ValueError
    except ValueError:
        await msg.answer("Введи число, например *45* или *32.5*", parse_mode="Markdown")
        return

    set_user_weight(uid, wkey(month_i, day_i, ex_i), text)
    pending_weight.pop(uid, None)

    await msg.answer(
        f"Сохранено! *{ex['name']}* → *{text} кг*\n\n"
        f"/workout — вернуться к плану",
        parse_mode="Markdown"
    )
