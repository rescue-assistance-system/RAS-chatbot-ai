from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from services.weather import get_weather_by_location
from services.vectorstore import initialize_vector_store
from services.gemini_model import chat
from utils.formatter import format_guide_for_victims
from utils.prompt_templates import default_response_template
from langchain.schema.runnable import RunnablePassthrough

# Khởi tạo FastAPI app
app = FastAPI()

# Cho phép CORS để FE có thể gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Bạn nên giới hạn domain thật sự trong production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dữ liệu truyền lên từ FE
class ChatRequest(BaseModel):
    user_input: str

# Khởi tạo vectorstore
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
    location_info = None
    if "lat=" in user_input and "lon=" in user_input:
        try:
            lat = float(user_input.split("lat=")[1].split()[0])
            lon = float(user_input.split("lon=")[1].split()[0])
            location_info = get_weather_by_location(lat, lon)
        except:
            location_info = "Unable to extract location from your input."

    docs = retriever.invoke(user_input)
    if docs:
        if len(docs) == 1:
            guide = docs[0]
            formatted = format_guide_for_victims({
                "title": guide.metadata["title"],
                "content": guide.page_content,
            })
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
