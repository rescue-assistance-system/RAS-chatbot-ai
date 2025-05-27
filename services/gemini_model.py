import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise Exception("Missing GEMINI_API_KEY environment variable.")

genai.configure(api_key=gemini_api_key)

model = genai.GenerativeModel(
    "gemini-2.0-flash",
    system_instruction="""
You are a helpful assistant specialized in first aid and emergency response.

You must ONLY answer questions related to:
- First aid procedures
- Emergency medical response
- Safety instructions in urgent situations

You are NOT a doctor and should not provide diagnosis or long-term treatment advice.

If the context is insufficient, you may use your general first aid knowledge to guide the user.

If the question is outside of this scope (e.g., cooking, programming, finance), reply EXACTLY with:

❌ Sorry, I don't have information related to that.
""",
    generation_config=genai.GenerationConfig(temperature=0.7),
)

chat = model.start_chat(history=[])


def ask(prompt: str) -> str:
    """Gửi prompt và trả về text trả lời từ Gemini."""
    response = chat.send_message(prompt)
    return response.text
