from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from utils.intent_classifier import classify_intent_with_gemini
from utils.ras_reader import read_ras_info_md
from services.weather import get_weather_by_location
from services.vectorstore import initialize_vector_store
from services.gemini_model import chat
from utils.formatter import format_guide_for_victims
from utils.prompt_templates import default_response_template
from langchain.schema.runnable import RunnablePassthrough
from services.rescue import find_nearest_rescue_team, format_rescue_teams_text

# Create FastAPI app
app = FastAPI()

# Accept CORS for FE can call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Data model for request
class ChatRequest(BaseModel):
    user_input: str


# === Initialize Vector Store ===
# Initialize the vector store and retriever
vectorstore = initialize_vector_store()
retriever = vectorstore.as_retriever()


# === Logic ===
def build_prompt_with_context(user_input, retriever):
    docs = retriever.invoke(user_input)
    if not docs:
        context = "No relevant information was found in the current knowledge base. Please use the base model to answer the question."
    else:
        sorted_docs = sorted(docs, key=lambda d: d.metadata.get("score", 1.0))
        top_docs = sorted_docs[: min(3, len(sorted_docs))]
        context = "\n\n".join([doc.page_content for doc in top_docs])

    prompt = f"""
Context (may be empty if no relevant documents found):
{context}

User question:
{user_input}

You are an AI emergency assistant. The user is in a possible medical emergency.
Please provide clear, direct, and helpful instructions based on the following context.
If the context is not sufficient, use your general emergency knowledge to provide first aid guidance for the user's situation.
"""
    return prompt


def handle_user_input(user_input: str):

    intent = classify_intent_with_gemini(user_input)
    if intent.startswith("ras_"):
        ras_data = read_ras_info_md()
        return {
            "type": "ras_info",
            "category": intent,
            "content": ras_data.get(intent, "No matching content found."),
        }

    if intent == "rescue-team":
        if "lat=" in user_input and "lon=" in user_input:
            try:
                lat = float(user_input.split("lat=")[1].split()[0])
                lon = float(user_input.split("lon=")[1].split()[0])
                rescue_teams = find_nearest_rescue_team(lat, lon)
                formatted_text = format_rescue_teams_text(rescue_teams)
                return {
                    "type": "rescue_team",
                    "teams": formatted_text,
                }
            except Exception as e:
                return {
                    "type": "rescue_team",
                    "error": f"Error parsing location or finding teams: {str(e)}",
                }
        else:
            return {
                "type": "rescue_team",
                "error": "Missing location info. Please include lat= and lon= in your message.",
            }

    location_info = None
    if intent == "weather":
        if "lat=" in user_input and "lon=" in user_input:
            try:
                lat = float(user_input.split("lat=")[1].split()[0])
                lon = float(user_input.split("lon=")[1].split()[0])
                weather_info = get_weather_by_location(lat, lon)
                return {
                    "type": "weather",
                    "response": weather_info,
                }
            except Exception as e:
                return {
                    "type": "weather",
                    "response": f"❌ Error parsing location: {str(e)}",
                }
        else:
            return {
                "type": "weather",
                "response": "❌ Please provide your location with lat= and lon=.",
            }

    docs = retriever.invoke(user_input)
    if docs:
        if len(docs) == 1:
            guide = docs[0]
            formatted = format_guide_for_victims(
                {
                    "title": guide.metadata["title"],
                    "content": guide.page_content,
                }
            )
            return {
                "type": "guide",
                "title": guide.metadata["title"],
                "content": guide.page_content,
                "image_url": guide.metadata["image_url"],
                "formatted": formatted,
            }
        else:
            prompt = build_prompt_with_context(user_input, retriever)
            response = chat.send_message(prompt).text.strip()
            return {
                "type": "summary",
                "response": response,
            }
    else:
        context = (
            f"✅ No emergency guide found in knowledge base.\n"
            f"{location_info or 'Please provide coordinates for weather.'}\n"
            f"Proceeding with general advice..."
        )
        rag_chain = (
            {"context": lambda _: context, "question": RunnablePassthrough()}
            | default_response_template
            | (lambda x: chat.send_message(x.text).text.strip())
        )
        return {
            "type": "general",
            "response": rag_chain.invoke(user_input),
        }


# === API Route ===
@app.post("/chat")
async def chat_with_ai(request: ChatRequest):
    try:
        result = handle_user_input(request.user_input)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
