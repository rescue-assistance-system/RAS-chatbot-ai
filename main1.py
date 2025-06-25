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
from utils.similarity_utils import (
    display_similarity_scores,
    get_best_match_with_confidence,
)
import time
from typing import Optional

ai_call_count = 0

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
    lat: Optional[float] = None
    lon: Optional[float] = None


# === Initialize Vector Store ===
# Initialize the vector store and retriever
vectorstore = initialize_vector_store()
retriever = vectorstore.as_retriever()


# === Logic ===
def build_prompt_with_context(user_input, retriever):
    # Sử dụng similarity_search_with_score thay vì invoke
    docs_with_scores = vectorstore.similarity_search_with_score(user_input, k=5)

    if not docs_with_scores:
        context = "No relevant information was found in the current knowledge base."
    else:
        # Sort by score (lower = more similar for some vector stores)
        sorted_docs = sorted(docs_with_scores, key=lambda x: x[1])
        top_docs = sorted_docs[:3]

        # Log scores for debugging
        print(f"[SIMILARITY SCORES] Top {len(top_docs)} results:")
        for i, (doc, score) in enumerate(top_docs):
            cosine_similarity = 1 - score  # Convert distance to similarity
            print(
                f"  Doc {i+1}: Cosine Similarity = {cosine_similarity:.4f} | Title: {doc.metadata.get('title', 'N/A')}"
            )

        context = "\n\n".join(
            [f"[Score: {1-score:.4f}] {doc.page_content}" for doc, score in top_docs]
        )

    prompt = f"""
Context with similarity scores:
{context}

User question:
{user_input}

You are an AI emergency assistant. The user is in a possible medical emergency.
Please provide clear, direct, and helpful instructions based on the following context.
If the context is not sufficient, use your general emergency knowledge to provide first aid guidance for the user's situation.
"""
    return prompt


def safe_send_message(prompt):
    global ai_call_count
    ai_call_count += 1  # đếm số lần gọi AI
    print(f"[AI CALL LOG] Gemini đã được gọi {ai_call_count} lần.")
    return chat.send_message(prompt)


def handle_user_input(user_input: str, lat: float = None, lon: float = None):
    intent = classify_intent_with_gemini(user_input)

    if intent.startswith("ras_"):
        ras_data = read_ras_info_md()
        return {
            # "type": "ras_info",
            "category": intent,
            "content": ras_data.get(intent, "No matching content found."),
        }

    if intent == "rescue-team":
        if lat is not None and lon is not None:
            try:
                # lat = float(user_input.split("lat=")[1].split()[0])
                # lon = float(user_input.split("lon=")[1].split()[0])
                rescue_teams = find_nearest_rescue_team(lat, lon)
                formatted_text = format_rescue_teams_text(rescue_teams)
                return {
                    # "type": "rescue_team",
                    "category": intent,
                    "content": formatted_text,
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

    # location_info = None
    if intent == "weather":
        if lat is not None and lon is not None:
            try:
                # lat = float(user_input.split("lat=")[1].split()[0])
                # lon = float(user_input.split("lon=")[1].split()[0])
                weather_info = get_weather_by_location(lat, lon)
                return {
                    # "type": "weather",
                    "category": intent,
                    "content": weather_info,
                }
            except Exception as e:
                return {
                    # "type": "weather",
                    "category": intent,
                    "content": f"❌ Error parsing location: {str(e)}",
                }
        else:
            return {
                # "type": "weather",
                "category": intent,
                "content": "❌ Please provide your location with lat= and lon=.",
            }

    # RAG search with similarity scores
    docs_with_scores = vectorstore.similarity_search_with_score(user_input, k=5)

    # Debug: Log similarity scores
    print(f"[DEBUG] User input: {user_input}")
    print(f"[DEBUG] Found {len(docs_with_scores)} documents with scores")

    for i, (doc, score) in enumerate(docs_with_scores):
        cosine_similarity = 1 - score  # Convert distance to cosine similarity
        print(f"[DEBUG] Doc {i+1}:")
        print(f"  - Title: {doc.metadata.get('title', 'N/A')}")
        print(f"  - Distance Score: {score:.4f}")
        print(f"  - Cosine Similarity: {cosine_similarity:.4f}")
        print(f"  - Content preview: {doc.page_content[:100]}...")

    if docs_with_scores:
        # Filter by similarity threshold
        similarity_threshold = 0.7  # Adjust this value
        relevant_docs = [
            (doc, score)
            for doc, score in docs_with_scores
            if (1 - score) >= similarity_threshold
        ]

        if relevant_docs:
            if len(relevant_docs) == 1:
                doc, score = relevant_docs[0]
                cosine_sim = 1 - score
                formatted = format_guide_for_victims(
                    {
                        "title": doc.metadata["title"],
                        "category": intent,
                        "content": doc.page_content,
                    }
                )
                return {
                    "type": "guide",
                    "title": doc.metadata["title"],
                    "content": doc.page_content,
                    "image_url": doc.metadata.get("image_url"),
                    "similarity_score": cosine_sim,
                    "formatted": formatted,
                }
            else:
                prompt = build_prompt_with_context(user_input, retriever)
                response = safe_send_message(prompt).text.strip()
                return {
                    "category": intent,
                    "content": response,
                    "similarity_scores": [1 - score for _, score in relevant_docs[:3]],
                }
        else:
            print(
                f"[INFO] No documents above similarity threshold {similarity_threshold}"
            )

    context = (
        f"✅ No emergency guide found in knowledge base.\n"
        # f"{location_info or 'Please provide coordinates for weather.'}\n"
        f"Proceeding with general advice..."
    )
    rag_chain = (
        {"context": lambda _: context, "question": RunnablePassthrough()}
        | default_response_template
        | (lambda x: safe_send_message(x.text).text.strip())
    )
    return {
        "type": "general",
        "category": intent,
        "content": rag_chain.invoke(user_input),
    }


# === API Route ===
@app.post("/chat")
async def chat_with_ai(request: ChatRequest):
    try:
        result = handle_user_input(request.user_input, request.lat, request.lon)

        # Add debug info if needed
        if "similarity_score" in result:
            print(
                f"[API RESPONSE] Returning result with similarity score: {result['similarity_score']:.4f}"
            )

        return {"success": True, "data": result}
    except Exception as e:
        print(f"[API ERROR] {str(e)}")
        return {"success": False, "error": str(e)}
