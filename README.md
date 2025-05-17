# 🚨 RAS-chatbot-ai (First Aid Emergency Assistant)

A lightweight command-line AI chatbot designed to provide **first aid**, **emergency response**, and **safety instructions** using Google Gemini 2.0 and **Retrieval-Augmented Generation (RAG)** for high-accuracy responses in critical moments.

---

## 🧠 What is RAS-chatbot-ai?

`RAS-chatbot-ai` stands for **Retrieval-Augmented System** chatbot AI — a specialized assistant trained and constrained to only answer **first aid and emergency-related questions**.

> 💬 "Is someone choking? Bleeding? Unconscious? Ask the chatbot — it gives step-by-step instructions immediately."

If a user asks something **unrelated** to first aid, the chatbot will **refuse to answer**.

---

## 🎯 Features

- ✅ Focused on **First Aid, Emergency Response, and Safety**
- 📚 Uses **RAG (Retrieval-Augmented Generation)** to load contextual documents
- 🤖 Powered by **Google Gemini 2.0 Flash** for fast, accurate completions
- 🌤️ Optional latitude/longitude input for weather-based emergency context
- ❌ Refuses to answer non-emergency questions
- 🧪 Includes testing for behavior control (domain lock)

---

## 📦 Built With

- **Python 3.10+**
- **Google Generative AI SDK (Gemini 2.0 Flash)**
- **RAG (Retrieval-Augmented Generation)**
- **Command-line Interface (CLI)**

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/rescue-assistance-system/RAS-chatbot-ai
cd RAS-chatbot-ai

python main.py
🚨 AI SOS Chatbot (CLI mode) 🚨
Type 'exit' to quit.
👤 You:

✨ Sample Usage
👤 You: My friend is bleeding from a deep cut.
🤖 AI: 🚨 Emergency detected. Here's an AI-assisted summary:

1.  **Apply Direct Pressure:** Use a clean cloth, gauze, or bandage to apply direct pressure to the wound.
2.  **Elevate the Injured Area:** If possible, raise the injured limb above the heart to help reduce blood flow.
3.  **Do Not Remove Embedded Objects:** If there are any objects embedded in the wound, do not remove them. Instead, apply pressure around the object.
4.  **Continue Applying Pressure:** If the bleeding does not stop after 5-10 minutes, continue applying pressure for another 5-10 minutes.
5.  **Call Emergency Services:** If the bleeding is severe and doesn't stop with pressure, call emergency services immediately.
👤 You:
