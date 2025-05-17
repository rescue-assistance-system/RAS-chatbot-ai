from langchain.prompts import PromptTemplate

default_response_template = PromptTemplate(
    template="""
{context}
User said: {question}
→ Respond in a clear, follow steps, not long, concise, helpful, and friendly manner.
""",
    input_variables=["context", "question"],
)
