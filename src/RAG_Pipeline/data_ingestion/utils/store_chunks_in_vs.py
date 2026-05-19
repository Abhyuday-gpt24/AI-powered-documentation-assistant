from langchain_core.documents import Document
from langchain_chroma import Chroma

# Store chunks in ChromaDB
def store_chunks(chunks: list[dict], vector_store: Chroma):
    """Convert chunk dicts to LangChain Documents and add to chromaDB"""
    documents = []
    ids = []

    for chunk in chunks:
        documents.append(
            Document(
                page_content=chunk["text"],
                metadata = {
                    "source": chunk["source"],
                    "heading_trail": chunk["heading_trail"],
                },
            )
        )
        ids.append(chunk["chunk_id"])

    vector_store.add_documents(documents, ids = ids)
