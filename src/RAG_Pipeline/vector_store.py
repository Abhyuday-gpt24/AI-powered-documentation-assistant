from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
import os
from dotenv import load_dotenv
from langchain_openai.embeddings import OpenAIEmbeddings

load_dotenv()

vector_stores = {}
retrievers = {}
index_initialized = False


def get_vector_store():
    global index_initialized
    collection = os.getenv("NAMESPACE_METADATA")
    if collection in vector_stores:
        return vector_stores[collection]

    pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")

    # Index creation only needs to happen once
    if not index_initialized:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        existing = [idx.name for idx in pc.list_indexes()]
        if pinecone_index_name not in existing:
            pc.create_index(
                name=pinecone_index_name,
                dimension=1536,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
        index_initialized = True

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    store = PineconeVectorStore(
        index_name=pinecone_index_name,
        embedding=embeddings,
        namespace=collection,
    )
    vector_stores[collection] = store
    return store


def get_retriever(k=5):
    collection = os.getenv("NAMESPACE_METADATA")
    if collection in retrievers:
        return retrievers[collection]

    retriever = get_vector_store(collection).as_retriever(
        search_type="mmr",
        search_kwargs={"k": k, "fetch_k": 25, "lambda_mult": 0.8},
    )
    retrievers[collection] = retriever
    return retriever