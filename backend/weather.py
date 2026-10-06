import os
import requests
from dotenv import load_dotenv

load_dotenv()                                  # reads your .env file
API_KEY = os.getenv("OPENWEATHER_API_KEY")
BASE = "https://api.openweathermap.org/data/2.5"


class WeatherError(Exception):
    """Our own error type, so we can give friendly messages."""


def get_weather(city: str) -> dict:
    if not API_KEY:
        raise WeatherError("API key missing. Check your .env file.")

    params = {"q": city, "appid": API_KEY, "units": "metric"}

    try:
        now = requests.get(f"{BASE}/weather", params=params, timeout=10)
        if now.status_code == 404:
            raise WeatherError("City not found. Check the spelling.")
        if now.status_code == 401:
            raise WeatherError("API key invalid or not active yet.")
        now.raise_for_status()
        now = now.json()

        forecast = requests.get(f"{BASE}/forecast", params=params, timeout=10)
        forecast.raise_for_status()
        forecast = forecast.json()
    except requests.RequestException:
        raise WeatherError("Could not reach the weather service.")

    # Add up all the rain expected in the next 5 days (each slot is 3 hours)
    rain_5d = sum(slot.get("rain", {}).get("3h", 0) for slot in forecast["list"])

    return {
        "city": now["name"],
        "temperature": round(now["main"]["temp"], 1),
        "humidity": now["main"]["humidity"],
        "rain_forecast_5d_mm": round(rain_5d, 1),
    }