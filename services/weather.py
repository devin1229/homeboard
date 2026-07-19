"""
Weather service for Homeboard.
"""

from datetime import datetime, timedelta
import requests

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

LATITUDE = 33.38
LONGITUDE = -84.65

CACHE_DURATION = timedelta(minutes=30)

_weather_cache = {
    "data": None,
    "updated_at": None,
}

def decode_weather_code(code):
    weather_codes = {
        0: {
            "condition": "Clear Sky",
            "icon": "clear",
        },
        1: {
            "condition": "Mostly Clear",
            "icon": "mostly-clear",
        },
        2: {
            "condition": "Partly Cloudy",
            "icon": "partly-cloudy",
        },
        3: {
            "condition": "Overcast",
            "icon": "cloudy",
        },
        45: {
            "condition": "Foggy",
            "icon": "fog",
        },
        48: {
            "condition": "Foggy",
            "icon": "fog",
        },
        51: {
            "condition": "Light Drizzle",
            "icon": "drizzle",
        },
        53: {
            "condition": "Drizzle",
            "icon": "drizzle",
        },
        55: {
            "condition": "Heavy Drizzle",
            "icon": "drizzle",
        },
        61: {
            "condition": "Light Rain",
            "icon": "rain",
        },
        63: {
            "condition": "Rain",
            "icon": "rain",
        },
        65: {
            "condition": "Heavy Rain",
            "icon": "heavy-rain",
        },
        71: {
            "condition": "Light Snow",
            "icon": "snow",
        },
        73: {
            "condition": "Snow",
            "icon": "snow",
        },
        75: {
            "condition": "Heavy Snow",
            "icon": "snow",
        },
        80: {
            "condition": "Light Showers",
            "icon": "showers",
        },
        81: {
            "condition": "Showers",
            "icon": "showers",
        },
        82: {
            "condition": "Heavy Showers",
            "icon": "heavy-rain",
        },
        95: {
            "condition": "Thunderstorms",
            "icon": "thunderstorm",
        },
        96: {
            "condition": "Thunderstorms",
            "icon": "thunderstorm",
        },
        99: {
            "condition": "Severe Thunderstorms",
            "icon": "thunderstorm",
        },
    }

    return weather_codes.get(
        code,
        {
            "condition": "Unknown",
            "icon": "cloudy",
        }
    )

def get_weather():
    now = datetime.now()

    if (
        _weather_cache["data"] is not None
        and _weather_cache["updated_at"] is not None
        and now - _weather_cache["updated_at"] < CACHE_DURATION
    ):
        return _weather_cache["data"]

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "current": [
            "temperature_2m",
            "weather_code",
        ],
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min"
        ],
        "temperature_unit": "fahrenheit",
        "timezone": "America/New_York",
        "forecast_days": 1,
    }

    try:
        response = requests.get(
            WEATHER_URL,
            params=params,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        weather_code = data["current"]["weather_code"]
        weather_info = decode_weather_code(weather_code)

        weather_data = {
            "temperature": round(
                data["current"]["temperature_2m"]
            ),
            "condition": weather_info["condition"],
            "high": round(
                data["daily"]["temperature_2m_max"][0]
            ),
            "low": round(
                data["daily"]["temperature_2m_min"][0]
            ),
            "icon": weather_info["icon"],
            "available": True,
        }

        _weather_cache["data"] = weather_data
        _weather_cache["updated_at"] = now

        return weather_data
    
    except (
        requests.RequestException,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        print(f"Weather service error: {error}")

        return {
            "temperature": None,
            "condition": "Weather unavailable",
            "high": None,
            "low": None,
            "icon": "cloudy",
            "available": False,
        }