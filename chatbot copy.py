from supabase import create_client, Client
import os
import google.generativeai as genai
from dotenv import load_dotenv
import requests
from datetime import datetime

# Load environment variables
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
weather_api_key = os.getenv("WEATHER_API_KEY")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_API_KEY")

# Initialize Supabase client
supabase: Client = create_client(supabase_url, supabase_key)

# Configure Gemini
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel("gemini-2.0-flash")
chat = model.start_chat(history=[])


# Get weather based on coordinates
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


# Search for a first aid guide based on user input
def search_first_aid_guide(user_input: str):
    keywords = [
        "burn",
        "injury",
        "bleeding",
        "fracture",
        "fall",
        "snake",
        "seizure",
        "shock",
    ]
    matched = [k for k in keywords if k in user_input.lower()]

    if not matched:
        return None

    keyword = matched[0]

    response = (
        supabase.table("first_aid_guides")
        .select("*")
        .ilike("title", f"%{keyword}%")
        .execute()
    )
    guides = response.data
    print(f"Found {len(guides)} guides for keyword '{keyword}'.")
    print(guides)

    if not guides:
        return "No relevant first aid guide found."

    guide = guides[0]
    return f"📌 **{guide['title']}**\n\n{guide['content']}\n\n🖼️ {guide.get('image_url', 'No image available.')}"


# Handle user input and determine response
def handle_user_input(user_input):
    emergency_keywords = [
        "accident",
        "burn",
        "fall",
        "fracture",
        "bleeding",
        "pain",
        "SOS",
    ]
    has_emergency = any(keyword in user_input.lower() for keyword in emergency_keywords)

    location_info = None
    if "lat=" in user_input and "lon=" in user_input:
        try:
            lat = float(user_input.split("lat=")[1].split()[0])
            lon = float(user_input.split("lon=")[1].split()[0])
            location_info = get_weather_by_location(lat, lon)
        except:
            location_info = "Unable to extract location from your input."

    first_aid_response = search_first_aid_guide(user_input)

    if has_emergency and first_aid_response:
        context = (
            "🚨 Emergency detected. Please stay calm. Here's a relevant first aid guide:\n\n"
            + first_aid_response
        )
    else:
        weather_advice = (
            location_info
            or "No location provided. Please share coordinates to get weather updates."
        )
        context = (
            f"✅ No emergency detected.\n{weather_advice}\n"
            "Meanwhile, here are some general safety tips for the current season:"
        )

    prompt = f"{context}\nUser said: {user_input}\n→ Respond in a clear, concise, helpful, and friendly manner."
    response = chat.send_message(prompt)
    return response.text.strip()


# Command-line chatbot interface
def chat_terminal():
    print("🚨 AI SOS Chatbot (CLI mode) 🚨")
    print("Type 'exit' to quit.")
    print("You can provide location with format: lat=16.06 lon=108.20\n")
    while True:
        user_input = input("👤 You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        try:
            reply = handle_user_input(user_input)
            print("🤖 AI:", reply)
        except Exception as e:
            print("❌ Error calling the API:", str(e))


if __name__ == "__main__":
    chat_terminal()
