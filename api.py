# api.py  —  запросы к ruz.spbstu.ru
import aiohttp
import logging
from config import GROUP_ID

log = logging.getLogger(__name__)

RUZ_API = f"https://ruz.spbstu.ru/api/v1/ruz/scheduler/{GROUP_ID}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; schedule-tgbot/1.0)",
    "Accept":     "application/json",
    "Referer":    "https://ruz.spbstu.ru/",
}


async def fetch_week(date_str: str) -> dict:
    """
    Загружает расписание на неделю, содержащую дату date_str (YYYY-MM-DD).
    Возвращает сырой JSON-словарь.
    """
    url = f"{RUZ_API}?date={date_str}"
    log.info(f"Запрос: {url}")

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            resp.raise_for_status()
            return await resp.json(content_type=None)


def _to_min(time_str: str) -> int:
    """'10:00' → 600"""
    h, m = time_str.split(":")
    return int(h) * 60 + int(m)


def _lesson_cat(type_str: str) -> str:
    t = (type_str or "").lower()
    if "лек" in t: return "lec"
    if "лаб" in t: return "lab"
    if "практ" in t or "семин" in t: return "prac"
    if "экзамен" in t or "зачёт" in t or "зачет" in t or "комисс" in t: return "exam"
    return "lec"


def parse_lessons(raw: dict) -> list:
    """
    Разбирает JSON-ответ ruz.spbstu.ru в плоский список занятий.
    Каждый элемент: {dow, startMin, endMin, name, type, cat, teacher, room, bld}
    dow: 0=Пн … 6=Вс
    """
    days = raw.get("week", {}).get("days") or raw.get("days") or []
    lessons = []

    for day in days:
        # weekday: 1=Пн … 7=Вс
        if "weekday" in day:
            dow = day["weekday"] - 1
        elif "date" in day:
            from datetime import date as _date
            dt = _date.fromisoformat(day["date"])
            dow = dt.weekday()
        else:
            continue

        for l in day.get("lessons") or []:
            ts = l.get("time_start") or l.get("timeStart") or ""
            te = l.get("time_end")   or l.get("timeEnd")   or ""
            if not ts or not te:
                continue

            type_name = (l.get("typeObj") or {}).get("name") or l.get("type") or ""
            teachers  = [
                t.get("full_name") or " ".join(filter(None, [t.get("lname"), t.get("fname"), t.get("patronymic")]))
                for t in (l.get("teachers") or [])
            ]
            auds = l.get("auditories") or []
            rooms = [a.get("name", "") for a in auds if a.get("name")]
            blds  = [
                (a.get("building") or {}).get("abbr") or (a.get("building") or {}).get("name") or ""
                for a in auds
            ]

            lessons.append({
                "dow":      dow,
                "startMin": _to_min(ts),
                "endMin":   _to_min(te),
                "name":     l.get("subject") or "—",
                "type":     type_name,
                "cat":      _lesson_cat(type_name),
                "teacher":  ", ".join(filter(None, teachers)),
                "room":     ", ".join(filter(None, rooms)),
                "bld":      ", ".join(filter(None, blds)),
            })

    return lessons
