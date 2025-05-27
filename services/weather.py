import requests
import os
from services.gemini_model import chat

weather_api_key = os.getenv("WEATHER_API_KEY")


def get_location_name(lat, lon):
    try:
        nominatim_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        headers = {"User-Agent": "WeatherApp/1.0"}
        res = requests.get(nominatim_url, headers=headers)
        data = res.json()

        address = data.get("address", {})
        # You can customize the returned name from these fields
        location_parts = [
            address.get("suburb"),
            address.get("city") or address.get("town") or address.get("village"),
            address.get("state"),
        ]
        location_name = ", ".join([part for part in location_parts if part])
        return location_name or "your area"
    except Exception:
        return "your location"


def get_weather_by_location(lat, lon):
    try:
        # Step 1: Get weather data from OpenWeatherMap
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={weather_api_key}&units=metric&lang=en"
        weather_response = requests.get(weather_url)
        weather_data = weather_response.json()

        if weather_response.status_code != 200:
            return "Unable to fetch weather data for your location."

        temp = weather_data["main"]["temp"]
        weather = weather_data["weather"][0]["description"]
        humidity = weather_data["main"]["humidity"]

        # Step 2: Get accurate location name from lat/lon
        city = get_location_name(lat, lon)

        # Step 3: Generate advice with Gemini
        prompt = f"""
You are a weather advisory assistant.

Given the following weather information:
- Temperature: {temp}°C
- Weather: {weather}
- Humidity: {humidity}%
- Location: {city}

Generate a helpful and relevant weather warning or advice message in English for users based on these conditions.
Be concise and user-friendly.
"""
        gemini_response = chat.send_message(prompt).text.strip()

        return f"Current weather in {city}: {weather}, {temp}°C, humidity {humidity}%. {gemini_response}"
    except Exception as e:
        return "Error fetching weather information: " + str(e)
