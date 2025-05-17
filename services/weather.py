import requests
import os

weather_api_key = os.getenv("WEATHER_API_KEY")


def get_weather_by_location(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={weather_api_key}&units=metric&lang=en"
        response = requests.get(url)
        data = response.json()

        if response.status_code != 200:
            return "Unable to fetch weather data for your location."

        temp = data["main"]["temp"]
        weather = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]
        city = data["name"]

        advice = (
            f"Current weather in {city}: {weather}, {temp}°C, humidity {humidity}%. "
        )
        if temp > 35:
            advice += "⚠️ It's very hot. Stay hydrated and avoid going out at noon."
        elif temp < 18:
            advice += "⚠️ It's cold. Dress warmly and avoid early morning activities."
        else:
            advice += "🌤️ The weather is pleasant, but stay alert to sudden changes."
        return advice
    except Exception as e:
        return "Error fetching weather information: " + str(e)
