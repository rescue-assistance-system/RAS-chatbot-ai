from services.gemini_model import chat

followup_question_prompt = """
You are a first aid assistant. A user just described a potential emergency situation:

"{user_input}"

Based on this, generate 3 to 5 follow-up questions to understand the situation better. 
Your questions must be clear, direct, and tailored to the scenario described.
Return only the questions in bullet points.
"""


def generate_followup_questions(user_input):
    prompt = followup_question_prompt.format(user_input=user_input)
    return chat.send_message(prompt).text.strip()
