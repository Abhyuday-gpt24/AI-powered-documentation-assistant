from langchain_chroma import Chroma
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings

embedding_model = "text-embedding-3-small"
embeddings = OpenAIEmbeddings(model=embedding_model)
vector_store = Chroma(
    collection_name="fastapi",
    embedding_function=embeddings,
    persist_directory="vectorstore"
)


@tool
def search_with_threshold(
    query: str,
    project: str | None = None,
) -> str:
    """Retrieve relevant chunks from the knowledge base based on user query.

    Args:
        query: The user's search query to find matching documents.
        project: Project name if user specified a specific project.
    """

    k = 10
    min_similarity = 0.20
    fallback_k = 3

    search_kwargs = {"k": k}
    if project:
        search_kwargs["filter"] = {"project": project}

    raw = vector_store.similarity_search_with_score(query, **search_kwargs)

    scored = []
    for doc, distance in raw:
        similarity = 1 - distance
        doc.metadata = {
            **doc.metadata,
            "similarity": similarity,
            "below_threshold": False,
        }
        scored.append((doc, similarity))

    scored.sort(key=lambda x: x[1], reverse=True)

    passing = [(doc, False) for doc, sim in scored if sim >= min_similarity]

    if not passing:
        passing = [(doc, True) for doc, _ in scored[:fallback_k]]
        for doc, _ in passing:
            doc.metadata["below_threshold"] = True

    # Format for LLM
    results = []
    for doc, below in passing:
        source = doc.metadata.get("source", "unknown")
        heading = doc.metadata.get("heading_trail", "")
        similarity = doc.metadata.get("similarity", 0)
        below_flag = doc.metadata.get("below_threshold", False)

        results.append(
            f"[Source: {source} | Section: {heading} | "
            f"Similarity: {similarity:.2f} | Below threshold: {below_flag}]\n"
            f"{doc.page_content}"
        )

    return "\n\n---\n\n".join(results) if results else "No relevant documents found."