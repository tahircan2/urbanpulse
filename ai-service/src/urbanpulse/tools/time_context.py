"""
tools/time_context.py — Istanbul time-based risk context. No API, pure Python.
"""
from __future__ import annotations
from datetime import datetime, timezone
import zoneinfo

TZ = zoneinfo.ZoneInfo("Europe/Istanbul")

HOLIDAYS: frozenset[str] = frozenset({
    "2025-01-01","2026-01-01","2025-04-23","2026-04-23",
    "2025-05-01","2026-05-01","2025-05-19","2026-05-19",
    "2025-07-15","2026-07-15","2025-08-30","2026-08-30",
    "2025-10-29","2026-10-29",
    # Ramazan 2025
    "2025-03-30","2025-03-31","2025-04-01",
    # Kurban 2025
    "2025-06-06","2025-06-07","2025-06-08","2025-06-09",
    # Ramazan 2026
    "2026-03-20","2026-03-21","2026-03-22",
    # Kurban 2026
    "2026-05-27","2026-05-28","2026-05-29","2026-05-30",
})


def get_time_risk_context() -> dict:
    now     = datetime.now(TZ)
    hour    = now.hour
    hhmm    = hour + now.minute / 60.0
    weekday = now.weekday()
    date_s  = now.strftime("%Y-%m-%d")

    is_weekend  = weekday >= 5
    is_holiday  = date_s in HOLIDAYS
    is_workday  = not is_weekend and not is_holiday
    is_night    = hour >= 22 or hour < 6
    is_rush_am  = is_workday and 7.5  <= hhmm < 9.5
    is_rush_pm  = is_workday and 17.0 <= hhmm < 19.5
    is_rush     = is_rush_am or is_rush_pm
    is_school   = is_workday and 8.0  <= hhmm < 17.0

    sla_mod = (
        "+25% (holiday — reduced staffing)" if is_holiday
        else "+25% (weekend — reduced staffing)" if is_weekend
        else "normal"
    )
    notes = []
    if is_rush:   notes.append("rush hour — traffic incidents +1 priority")
    if is_night:  notes.append("night — noise violations auto-escalate")
    if is_school: notes.append("school hours — incidents near schools +1 priority")
    if is_holiday:notes.append("public holiday — reduced capacity")

    return {
        "current_time":    now.strftime("%H:%M"),
        "current_date":    date_s,
        "day_of_week":     now.strftime("%A"),
        "is_workday":      is_workday,
        "is_rush_hour":    is_rush,
        "is_rush_morning": is_rush_am,
        "is_rush_evening": is_rush_pm,
        "is_school_hours": is_school,
        "is_night":        is_night,
        "is_weekend":      is_weekend,
        "is_holiday":      is_holiday,
        "sla_modifier":    sla_mod,
        "priority_notes":  notes,
        "summary":         (
            f"{now.strftime('%H:%M %A')}. "
            + ("Rush hour active. " if is_rush else "")
            + ("School hours. " if is_school else "")
            + ("Night time. " if is_night else "")
            + ("Public holiday — reduced capacity. " if is_holiday else "")
        ).strip(),
    }
