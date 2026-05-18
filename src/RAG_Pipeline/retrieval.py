from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vector_store = None
def get_vector_store():
    global vector_store
    if vector_store:
        return 
    
    vector_store = Chroma(
        collection_name= os.getenv("COLLECTION_NAME"),
        embedding_function=embeddings,
        persist_directory= os.getenv("PERSIST_DIR"),
        collection_metadata={"hnsw:space": "cosine"},
    )


get_vector_store()

def retrieve_function(query: str, k: int = 5) -> str:
    
    global vector_store
    results = vector_store.similarity_search(query, k=k)
    if not results:
        return "No relevant documents found."

    chunks = []
    for doc in results:
        source = doc.metadata.get("source", "unknown")
        heading = doc.metadata.get("heading_trail", "")
        chunks.append(
            f"[Source: {source} | Section: {heading} \n"
            f"{doc.page_content}"
        )

    return "\n\n---\n\n".join(chunks)