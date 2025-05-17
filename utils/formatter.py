from services.gemini_model import chat


def format_guide_for_victims(guide):
    title = guide["title"]
    content = guide["content"]

    prompt = f"""
    You are a first aid assistant helping people in emergency situations.

    Here is a guide titled: "{title}"

    --- Guide Content ---
    {content}
    ----------------------

    Please rewrite this guide to be:
    - Clear and friendly for a victim or bystander
    - Broken down into 3–5 main steps
    - Focused only on what to **do** first
    - Avoid medical jargon
    - Keep sentences short and calm

    Respond in this format:
    📌 Title: <short version>
    📝 Steps:
    - Step 1: ...
    - Step 2: ...
    - ...
    ⚠️ Note: (if any warning needed)
    """
    return chat.send_message(prompt).text.strip()
