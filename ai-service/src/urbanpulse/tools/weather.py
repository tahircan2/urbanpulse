"""Open-Meteo weather API — free, no key, sync."""
from __future__ import annotations
import httpx

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
WEATHER_CODES  = {
    0:"Clear sky",1:"Mainly clear",2:"Partly cloudy",3:"Overcast",
    45:"Fog",61:"Slight rain",63:"Moderate rain",65:"Heavy rain",
    80:"Slight showers",81:"Moderate showers",82:"Violent showers",
    95:"Thunderstorm",99:"Thunderstorm with hail",
}


def get_weather_context(latitude: float, longitude: float) -> dict:
    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.get(OPEN_METEO_URL, params={
                "latitude": latitude, "longitude": longitude,
                "current": "temperature_2m,precipitation,windspeed_10m,weathercode,visibility,relative_humidity_2m",
                "forecast_days": 1, "timezone": "Europe/Istanbul",
            }, headers={"User-Agent": "UrbanPulse/3.0"})
            resp.raise_for_status()
            cur = resp.json().get("current", {})

        temp  = float(cur.get("temperature_2m", 20))
        prec  = float(cur.get("precipitation", 0))
        wind  = float(cur.get("windspeed_10m", 0))
        code  = int(cur.get("weathercode", 0))
        vis   = float(cur.get("visibility", 10000))
        humid = float(cur.get("relative_humidity_2m", 50))
        cond  = WEATHER_CODES.get(code, f"Code {code}")

        boost, reasons = 0, []
        if prec > 5.0 or code in (65, 82):       boost += 2; reasons.append(f"heavy rain ({prec}mm/h)")
        if temp > 32 and humid < 30 and wind > 30: boost += 2; reasons.append("fire weather")
        if code in (95, 99) or wind > 60:          boost += 1; reasons.append("storm")

        return {
            "temperature_c": temp, "precipitation_mm": prec,
            "windspeed_kmh": wind, "humidity_pct": humid,
            "visibility_m": vis,  "condition": cond,
            "flood_risk":   prec > 5.0 or code in (65, 82),
            "fire_weather": temp > 32 and humid < 30 and wind > 30,
            "priority_boost": min(boost, 2), "boost_reasons": reasons,
            "summary": f"{cond}, {temp}°C, precip {prec}mm/h, wind {wind}km/h",
        }
    except httpx.TimeoutException:
        return {"error": "timeout", "priority_boost": 0, "summary": "Weather unavailable"}
    except Exception as exc:
        return {"error": str(exc), "priority_boost": 0, "summary": "Weather unavailable"}
