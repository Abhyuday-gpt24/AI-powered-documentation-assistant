from langchain_chroma import Chroma
import chromadb
import os
from dotenv import load_dotenv
from langchain_openai.embeddings import OpenAIEmbeddings

load_dotenv()

vector_store = None 
retriever = None

def get_vector_store(collection: str):
    global vector_store
    if vector_store is None:
        client = chromadb.CloudClient(
            tenant= os.getenv("CHROMADB_TENANT"),
            database= os.getenv("CHROMADB"),
            api_key= os.getenv("CHROMADB_API_KEY")
        )

        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        vector_store = Chroma(
            client=client,
            embedding_function= embeddings,
            collection_name=collection,
            collection_metadata={"hnsw:space": "cosine"}
        )
    return vector_store


def get_retriever(k=5):
    global retriever
    if retriever is None:
        retriever = get_vector_store().as_retriever(
            search_type="mmr",
            search_kwargs={"k": 5, "fetch_k": 25, "lambda_mult": 0.8}
        )
    return retriever