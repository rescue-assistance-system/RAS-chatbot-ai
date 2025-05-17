from langchain_community.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from services.supabase_client import supabase

embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def initialize_vector_store():
    response = supabase.table("first_aid_guides").select("*").execute()
    guides = response.data
    documents = [
        Document(
            page_content=f"{guide['title']}\n{guide['content']}",
            metadata={
                "title": guide["title"],
                "image_url": guide.get("image_url", "No image available."),
            },
        )
        for guide in guides
    ]
    vectorstore = Chroma.from_documents(documents, embedding_model)
    return vectorstore
