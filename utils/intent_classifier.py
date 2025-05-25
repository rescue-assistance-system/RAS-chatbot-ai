from services.gemini_model import chat
from utils.ras_reader import read_ras_info_md


def classify_intent_with_gemini(user_input: str) -> str:
    ras_context = read_ras_info_md()

    prompt = f"""
You are an AI assistant that classifies user input related to the Rescue Assistance System (RAS).

Context (about RAS):
{ras_context}

Given the user input, classify it into one of the following categories:
- ras_info
- ras_usage
- ras_features
- ras_target
- general

Return only the category name (e.g., "ras_info") and nothing else.

User input: "{user_input}"
"""
    result = chat.send_message(prompt).text.strip().lower()
    return result


def generate_response_with_gemini(user_input: str) -> dict:
    intent = classify_intent_with_gemini(user_input)
    ras_data = read_ras_info_md()
    ras_content = ras_data.get(intent)

    if intent.startswith("ras_") and ras_content:
        prompt = f"""
You are a helpful assistant for the Rescue Assistance System (RAS).

Below is relevant information about RAS:
\"\"\"
{ras_content}
\"\"\"

Based on this content and the user's question below, provide a natural, friendly, and informative answer.

User: "{user_input}"
"""
        final_response = chat.send_message(prompt).text.strip()
        return {"success": True, "category": intent, "content": final_response}

    else:
        return {
            "success": False,
            "category": "general",
            "content": "Sorry, I couldn't find relevant information to answer your question.",
        }
