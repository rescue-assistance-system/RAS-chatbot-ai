from services.weather import get_weather_by_location
from services.vectorstore import initialize_vector_store
from services.gemini_model import chat
from utils.formatter import format_guide_for_victims
from utils.followup import generate_followup_questions
from utils.prompt_templates import default_response_template
from langchain.schema.runnable import RunnablePassthrough

vectorstore = initialize_vector_store()
retriever = vectorstore.as_retriever()


def build_prompt_with_context(user_input, retriever):
    print("Building prompt with context...")
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


def search_first_aid_guide_rag(user_input):
    docs = retriever.invoke(user_input)
    if not docs:
        return None
    guide = docs[0]
    formatted = format_guide_for_victims(
        {
            "title": guide.metadata["title"],
            "content": guide.page_content,
        }
    )
    return f"📌 **{guide.metadata['title']}**\n\n{guide.page_content}\n\n🖼️ {guide.metadata['image_url']}\n\n{formatted}"


def handle_user_input(user_input):
    location_info = None
    if "lat=" in user_input and "lon=" in user_input:
        try:
            lat = float(user_input.split("lat=")[1].split()[0])
            lon = float(user_input.split("lon=")[1].split()[0])
            location_info = get_weather_by_location(lat, lon)
        except:
            location_info = "Unable to extract location from your input."

    # Step 1: RAG search
    docs = retriever.invoke(user_input)
    # docs = ""
    print(f"Found {len(docs)} relevant documents for user input.")
    # print(docs)
    # Step 2: Check if any documents were found

    if docs:
        if len(docs) == 1:
            print("Only one document found.")
            # Case where only one document is found → use it directly
            # and send to Gemini
            guide = docs[0]
            formatted = format_guide_for_victims(
                {
                    "title": guide.metadata["title"],
                    "content": guide.page_content,
                }
            )
            return (
                f"🚨 Emergency detected. Please stay calm. Here's a relevant first aid guide:\n\n"
                f"📌 **{guide.metadata['title']}**\n\n{guide.page_content}\n\n🖼️ {guide.metadata['image_url']}\n\n{formatted}"
            )
        else:
            print("Multiple documents found.")
            # Case where multiple documents are found → use RAG to summarize
            # and send to Gemini
            prompt = build_prompt_with_context(user_input, retriever)

            # print(prompt)
            response = chat.send_message(prompt).text.strip()
            return (
                f"🚨 Emergency detected. Here's an AI-assisted summary:\n\n{response}"
            )
    else:
        print("No relevant documents found.")
        # Not found any first aid guide → use default response template
        # and send to Gemini
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
        return rag_chain.invoke(user_input)


def chat_terminal():
    print("🚨 AI SOS Chatbot (CLI mode) 🚨")
    print("Type 'exit' to quit.")
    while True:
        user_input = input("👤 You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        try:
            reply = handle_user_input(user_input)
            print("🤖 AI:", reply)
        except Exception as e:
            print("❌ Error:", str(e))


if __name__ == "__main__":
    chat_terminal()
