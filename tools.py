"""เครื่องมือ (tools) ที่ Claude เรียกใช้ได้ - โค้ดส่วนนี้รันบนเครื่องคุณ"""

import json
import urllib.parse
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# คำนิยามเครื่องมือที่ส่งให้ Claude (JSON Schema)
CLIENT_TOOLS = [
    {
        "name": "get_current_time",
        "description": "Get the current date and time in a given IANA timezone. "
        "Use this whenever the user asks about today's date or the current time.",
        "eager_input_streaming": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "IANA timezone name, e.g. 'Asia/Bangkok'. Default Asia/Bangkok.",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_weather",
        "description": "Get the current weather (temperature, humidity, wind, conditions) "
        "for a city, using the Open-Meteo API.",
        "eager_input_streaming": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name, e.g. 'Bangkok' or 'Chiang Mai'.",
                }
            },
            "required": ["city"],
        },
    },
]

# รหัสสภาพอากาศของ Open-Meteo (WMO code) -> คำอธิบาย
_WEATHER_CODES = {
    0: "ท้องฟ้าแจ่มใส", 1: "มีเมฆเล็กน้อย", 2: "มีเมฆบางส่วน", 3: "เมฆมาก",
    45: "มีหมอก", 48: "มีหมอกน้ำค้างแข็ง",
    51: "ฝนปรอยเล็กน้อย", 53: "ฝนปรอย", 55: "ฝนปรอยหนัก",
    61: "ฝนตกเล็กน้อย", 63: "ฝนตกปานกลาง", 65: "ฝนตกหนัก",
    80: "ฝนไล่ช่วงเล็กน้อย", 81: "ฝนไล่ช่วง", 82: "ฝนไล่ช่วงหนัก",
    95: "พายุฝนฟ้าคะนอง", 96: "พายุฝนฟ้าคะนองมีลูกเห็บ", 99: "พายุฝนฟ้าคะนองลูกเห็บหนัก",
}


class ToolInputError(ValueError):
    """input จาก Claude ไม่ตรง schema"""


def _fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "claude-api-chat"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_current_time(timezone: str = "Asia/Bangkok") -> str:
    try:
        now = datetime.now(ZoneInfo(timezone))
    except (ZoneInfoNotFoundError, ValueError):
        raise ToolInputError(f"Unknown timezone: {timezone!r}")
    return now.strftime(f"%Y-%m-%d %H:%M:%S ({timezone}, %A)")


def get_weather(city: str) -> str:
    q = urllib.parse.urlencode({"name": city, "count": 1, "language": "en"})
    geo = _fetch_json(f"https://geocoding-api.open-meteo.com/v1/search?{q}")
    if not geo.get("results"):
        return f"ไม่พบเมืองชื่อ {city!r}"
    place = geo["results"][0]
    params = urllib.parse.urlencode({
        "latitude": place["latitude"],
        "longitude": place["longitude"],
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
        "timezone": "auto",
    })
    data = _fetch_json(f"https://api.open-meteo.com/v1/forecast?{params}")
    cur = data["current"]
    return json.dumps({
        "place": f"{place['name']}, {place.get('country', '')}",
        "time": cur["time"],
        "temperature_c": cur["temperature_2m"],
        "humidity_percent": cur["relative_humidity_2m"],
        "wind_kmh": cur["wind_speed_10m"],
        "conditions": _WEATHER_CODES.get(cur["weather_code"], f"code {cur['weather_code']}"),
    }, ensure_ascii=False)


def _validate(name: str, args: object) -> dict:
    """ตรวจ input ก่อนรันจริง (eager input streaming ไม่ได้ตรวจให้)"""
    if not isinstance(args, dict):
        raise ToolInputError("Tool input must be a JSON object")
    if name == "get_current_time":
        tz = args.get("timezone", "Asia/Bangkok")
        if not isinstance(tz, str) or not tz.strip():
            raise ToolInputError("'timezone' must be a non-empty string")
        return {"timezone": tz.strip()}
    if name == "get_weather":
        city = args.get("city")
        if not isinstance(city, str) or not city.strip():
            raise ToolInputError("'city' is required and must be a non-empty string")
        return {"city": city.strip()}
    raise ToolInputError(f"Unknown tool: {name}")


_HANDLERS = {"get_current_time": get_current_time, "get_weather": get_weather}


def run_tool(name: str, args: object) -> tuple[str, bool]:
    """รันเครื่องมือ คืนค่า (ผลลัพธ์, is_error)"""
    try:
        clean = _validate(name, args)
        return _HANDLERS[name](**clean), False
    except ToolInputError as e:
        return f"Invalid input: {e}. Raw input: {json.dumps(args, ensure_ascii=False)}", True
    except Exception as e:  # เครือข่ายล่ม ฯลฯ - ส่งกลับให้ Claude รู้
        return f"Tool failed: {type(e).__name__}: {e}", True
