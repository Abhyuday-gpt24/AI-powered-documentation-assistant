from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vector_store = Chroma(
    collection_name="nextjs",
    embedding_function=embeddings,
    persist_directory="vectorstore",
)


def retrieve_function(query: str, k: int = 5) -> str:
    search_kwargs = {"k": k}
    search_kwargs["filter"] = {"project": "nextjs"}
    results = vector_store.similarity_search_with_score(query, **search_kwargs)

    if not results:
        return "No relevant documents found."

    chunks = []
    for doc, distance in results:
        similarity = 1 / (1 + distance)  # L2 → [0, 1]
        source = doc.metadata.get("source", "unknown")
        heading = doc.metadata.get("heading_trail", "")
        chunks.append(
            f"[Source: {source} | Section: {heading} | Score: {similarity:.2f}]\n"
            f"{doc.page_content}"
        )

    return "\n\n---\n\n".join(chunks)