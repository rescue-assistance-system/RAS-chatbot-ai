from langchain_community.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document

from services.supabase_client import supabase

embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def initialize_vector_store():
    response = supabase.table("first_aid_guides").select("*").execute()
    guides = response.data
    documents = []

    for guide in guides:
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
            },
        )
        documents.append(doc)

    vectorstore = Chroma.from_documents(documents, embedding_model)
    # Debug: Log số lượng documents
    print(f"[DEBUG] Total documents in vectorstore: {vectorstore._collection.count()}")

    # Debug: Log một vài vector samples
    if hasattr(vectorstore, "_collection"):
        sample_data = vectorstore._collection.peek(limit=3)
        print(f"[DEBUG] Sample vectors: {sample_data}")

    return vectorstore
