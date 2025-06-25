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
from services.supabase_client import supabase
from langchain.docstore.document import Document
import time
from typing import Optional
import threading
import schedule
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ai_call_count = 0
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Data model for request
class ChatRequest(BaseModel):
    user_input: str
    lat: Optional[float] = None
    lon: Optional[float] = None


# Initialize Vector Store
vectorstore = initialize_vector_store(
    persist_directory="./chroma_db", reset=True
)  # Reset on startup
retriever = vectorstore.as_retriever()

# Cron Job using schedule
last_updated = None


def check_and_update_vector_store():
    """Check for changes in the first_aid_guides table and update vector store incrementally."""
    global vectorstore, retriever, last_updated
    try:
        response = (
            supabase.table("first_aid_guides")
            .select("updated_at")
            .order("updated_at", desc=True)
            .limit(1)
            .execute()
        )
        latest_update = response.data[0]["updated_at"] if response.data else None

        if last_updated is None:
            last_updated = latest_update
            print("[INFO] Initial updated_at time set.")
            print(
                f"[DEBUG] Current total documents in vectorstore: {vectorstore._collection.count()}"
            )
            return

        if latest_update != last_updated:
            print(
                "[INFO] Detected changes in the first_aid_guides table (updated_at). Updating vector store incrementally..."
            )
            # Fetch new or updated records
            response = (
                supabase.table("first_aid_guides")
                .select("id, title, content, image_url")
                .gt("updated_at", last_updated)
                .execute()
            )
            new_or_updated_guides = response.data

            if new_or_updated_guides:
                documents = []
                for guide in new_or_updated_guides:
                    image_list = guide.get("image_url", []) or []
                    image_url = (
                        image_list[0]
                        if isinstance(image_list, list) and image_list
                        else "No image available."
                    )
                    doc = Document(
                        page_content=f"{guide['title']}\n{guide['content']}",
                        metadata={
                            "title": guide["title"],
                            "image_url": image_url,
                            "id": str(guide["id"]),  # Unique identifier
                        },
                    )
                    documents.append(doc)

                # Delete outdated embeddings
                old_ids = [str(guide["id"]) for guide in new_or_updated_guides]
                vectorstore.delete(ids=old_ids)
                # Add new embeddings
                vectorstore.add_documents(documents)
                print(f"[INFO] Updated {len(documents)} documents in vector store.")
                retriever = vectorstore.as_retriever()

            last_updated = latest_update
            print("[INFO] Successfully updated vector store.")
            print(
                f"[DEBUG] Current total documents in vectorstore: {vectorstore._collection.count()}"
            )
        else:
            print("[INFO] No changes detected in the first_aid_guides table.")
    except Exception as e:
        print(f"[ERROR] Unable to check or update vector store: {str(e)}")


def run_scheduler():
    """Check every 4 hours for high-priority emergency system."""
    schedule.every().day.at("02:00").do(check_and_update_vector_store)
    schedule.every().day.at("06:00").do(check_and_update_vector_store)
    schedule.every().day.at("10:00").do(check_and_update_vector_store)
    schedule.every().day.at("14:00").do(check_and_update_vector_store)
    schedule.every().day.at("18:00").do(check_and_update_vector_store)
    schedule.every().day.at("22:00").do(check_and_update_vector_store)

    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


# Start scheduler on startup
@app.on_event("startup")
async def startup_event():
    threading.Thread(target=run_scheduler, daemon=True).start()
    print("[INFO] Started cron-style scheduler to check for database changes.")


# Processing logic
def build_prompt_with_context(user_input, retriever):
    docs = retriever.invoke(user_input)
    if not docs:
        context = "No relevant information found in the current knowledge base. Please use the base model to answer the question."
    else:
        sorted_docs = sorted(docs, key=lambda d: d.metadata.get("score", 1.0))
        top_docs = sorted_docs[: min(3, len(sorted_docs))]
        context = "\n\n".join([doc.page_content for doc in top_docs])

    prompt = f"""
Context (may be empty if no relevant documents are found):
{context}

User question:
{user_input}

You are an emergency AI assistant. The user may be in a medical emergency.
Please provide clear, direct, and helpful instructions based on the following context.
If the context is insufficient, use general emergency knowledge to provide first aid instructions for the user's situation.
"""
    return prompt


def safe_send_message(prompt):
    global ai_call_count
    ai_call_count += 1
    print(f"[AI CALL LOG] Gemini called {ai_call_count} times.")
    return chat.send_message(prompt)


def handle_user_input(user_input: str, lat: float = None, lon: float = None):
    intent = classify_intent_with_gemini(user_input)
    if intent.startswith("ras_"):
        ras_data = read_ras_info_md()
        return {
            "category": intent,
            "content": ras_data.get(intent, "No relevant content found."),
        }

    if intent == "rescue-team":
        if lat is not None and lon is not None:
            try:
                rescue_teams = find_nearest_rescue_team(lat, lon)
                formatted_text = format_rescue_teams_text(rescue_teams)
                return {
                    "category": intent,
                    "content": formatted_text,
                }
            except Exception as e:
                return {
                    "category": intent,
                    "error": f"Error processing location or finding rescue team: {str(e)}",
                }
        else:
            return {
                "category": intent,
                "error": "Location information missing. Please include lat= and lon= in the message.",
            }

    if intent == "weather":
        if lat is not None and lon is not None:
            try:
                weather_info = get_weather_by_location(lat, lon)
                return {
                    "category": intent,
                    "content": weather_info,
                }
            except Exception as e:
                return {
                    "category": intent,
                    "content": f"❌ Error processing location: {str(e)}",
                }
        else:
            return {
                "category": intent,
                "content": "❌ Please provide location with lat= and lon=.",
            }

    docs = retriever.invoke(user_input)
    print(f"[DEBUG] User input: {user_input}")
    print(f"[DEBUG] Found {len(docs)} documents")

    for i, doc in enumerate(docs):
        print(f"[DEBUG] Document {i+1}:")
        print(f"  - Title: {doc.metadata.get('title', 'N/A')}")
        print(f"  - Score: {doc.metadata.get('score', 'N/A')}")
        print(f"  - Content preview: {doc.page_content[:100]}...")

    if docs:
        if len(docs) == 1:
            guide = docs[0]
            formatted = format_guide_for_victims(
                {
                    "title": guide.metadata["title"],
                    "category": intent,
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
            response = safe_send_message(prompt).text.strip()
            return {
                "category": intent,
                "content": response,
            }
    else:
        context = (
            f"✅ No emergency instructions found in the knowledge base.\n"
            f"Please provide coordinates for weather.\n"
            f"Continuing with general advice..."
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


# API Route
@app.post("/chat")
async def chat_with_ai(request: ChatRequest):
    try:
        result = handle_user_input(request.user_input, request.lat, request.lon)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
