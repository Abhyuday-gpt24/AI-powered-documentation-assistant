from langchain_chroma import Chroma
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings

embedding_model = "text-embedding-3-small"
embeddings = OpenAIEmbeddings(model=embedding_model)

# Define all your collection names
COLLECTION_NAMES = ["hf_transformers", "nextjs"]

# Initialize all vector stores in a dict
vector_stores: dict[str, Chroma] = {
    name: Chroma(
        collection_name=name,
        embedding_function=embeddings,
        persist_directory="vectorstore",
    )
    for name in COLLECTION_NAMES
}


@tool()
def retrieve_tool(
    query: str,
    collection: str | None = None,
    project: str | None = None,
) -> str:
    """Retrieve relevant chunks from the knowledge base based on user query.

    Args:
        query: The user's search query to find matching documents.
        collection: Which knowledge base collection to search.
                    Must be one of: hf_transformers, nextjs.
                    If not specified, searches ALL collections.
        project: Project name will be same as the collection.
    """

    k = 10
    min_similarity = 0.20
    fallback_k = 3

    search_kwargs = {"k": k}
    if project:
        search_kwargs["filter"] = {"project": project.lower()}

    # Decide which stores to search
    if collection and collection.lower() in vector_stores:
        stores_to_search = {collection.lower(): vector_stores[collection.lower()]}
    elif collection:
        return f"Unknown collection '{collection}'. Available: {', '.join(COLLECTION_NAMES)}"
    else:
        # Search all collections
        stores_to_search = vector_stores

    # Gather results from all target stores
    scored = []
    for store_name, store in stores_to_search.items():
        raw = store.similarity_search_with_score(query, **search_kwargs)
        for doc, distance in raw:
            similarity = 1 - distance
            doc.metadata = {
                **doc.metadata,
                "similarity": similarity,
                "below_threshold": False,
                "collection": store_name,  # track which collection it came from
            }
            scored.append((doc, similarity))

    scored.sort(key=lambda x: x[1], reverse=True)

    # Apply threshold
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
        coll = doc.metadata.get("collection", "unknown")

        results.append(
            f"[Collection: {coll} | Source: {source} | Section: {heading} | "
            f"Similarity: {similarity:.2f} | Below threshold: {below_flag}]\n"
            f"{doc.page_content}"
        )

    return "\n\n---\n\n".join(results) if results else "No relevant documents found."