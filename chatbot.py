import os
import google.generativeai as genai
from dotenv import load_dotenv
import requests
from datetime import datetime

# Load API keys from .env
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
weather_api_key = os.getenv("WEATHER_API_KEY")

genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel("gemini-2.0-flash")
chat = model.start_chat(history=[])


def get_weather_by_location(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={weather_api_key}&units=metric&lang=vi"
        response = requests.get(url)
        data = response.json()

        if response.status_code != 200:
            return "Không thể lấy dữ liệu thời tiết tại vị trí của bạn."

        temp = data["main"]["temp"]
        weather = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]
        city = data["name"]

        advice = f"Hiện tại thời tiết ở {city} là {weather}, nhiệt độ {temp}°C, độ ẩm {humidity}%. "
        if temp > 35:
            advice += (
                "⚠️ Nắng nóng gay gắt, bạn nên uống nhiều nước, tránh ra ngoài lúc trưa."
            )
        elif temp < 18:
            advice += "⚠️ Trời lạnh, bạn nên giữ ấm và hạn chế ra ngoài vào sáng sớm."
        else:
            advice += (
                "🌤️ Thời tiết khá dễ chịu, bạn vẫn nên đề phòng các thay đổi bất thường."
            )

        return advice
    except Exception as e:
        return "Lỗi khi lấy thông tin thời tiết: " + str(e)


def handle_user_input(user_input):
    sos_keywords = ["tai nạn", "bỏng", "ngã", "gãy", "chảy máu", "đau", "SOS"]
    has_emergency = any(keyword in user_input.lower() for keyword in sos_keywords)

    location_info = None
    if "lat=" in user_input and "lon=" in user_input:
        try:
            lat = float(user_input.split("lat=")[1].split()[0])
            lon = float(user_input.split("lon=")[1].split()[0])
            location_info = get_weather_by_location(lat, lon)
        except:
            location_info = "Không thể phân tích vị trí từ yêu cầu của bạn."

    if has_emergency:
        context = "Bạn đang trong tình huống khẩn cấp. Hãy giữ bình tĩnh. Sau đây là hướng dẫn sơ cứu:"
    else:
        weather_advice = (
            location_info
            or "Không có thông tin vị trí. Hãy cung cấp toạ độ để nhận cảnh báo thời tiết."
        )
        context = f"Không có tình huống khẩn cấp được ghi nhận. {weather_advice}\nNgoài ra, đây là một số mẹo để giữ an toàn trong mùa này:"

    prompt = f"{context}\nNgười dùng nói: {user_input}\n→ Trả lời một cách dễ hiểu, ngắn gọn, chi tiết, dễ hiểu và thân thiện."
    response = chat.send_message(prompt)
    return response.text.strip()


def chat_terminal():
    print("🚨 AI SOS Chatbot (CLI mode) 🚨")
    print("Gõ 'exit' để thoát.")
    print("Bạn có thể cung cấp vị trí bằng cú pháp: lat=16.06 lon=108.20\n")
    while True:
        user_input = input("👤 Bạn: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        try:
            reply = handle_user_input(user_input)
            print("🤖 AI:", reply)
        except Exception as e:
            print("❌ Lỗi khi gọi API:", str(e))


if __name__ == "__main__":
    chat_terminal()
