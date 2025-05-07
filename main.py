from fastapi import FastAPI, Request
from pydantic import BaseModel
from chatbot import ask_chatbot

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    sos_status: bool = False

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    reply = ask_chatbot(req.message, sos_mode=req.sos_status)
    return {"reply": reply}
