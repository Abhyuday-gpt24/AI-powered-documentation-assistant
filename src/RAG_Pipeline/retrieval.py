

from langchain_chroma import Chroma
from langchain_core.documents import Document


def search_with_threshold(
    vector_store: Chroma,
    query: str,
    project: str | None = None,
    k: int = 10,
    min_similarity: float = 0.20,
    fallback_k: int = 3,
) -> list[Document]:
    """
    Retrieve chunks above a similarity threshold, with a fallback.

    Strategy:
      1. Pull top-k candidates from Chroma (filtered by project if given).
      2. Convert distance -> similarity (1 - distance).
      3. Keep everything >= min_similarity.
      4. If nothing clears the threshold, fall back to top-`fallback_k`
         candidates marked with below_threshold=True so the caller knows.

    Each returned Document carries:
      - metadata["similarity"]      float in roughly [0, 1]
      - metadata["below_threshold"] True only when fallback was used
    """

    # Optional project filter — Chroma's `where` clause, exact-match metadata
    search_kwargs = {"k": k}
    if project:
        search_kwargs["filter"] = {"project": project}

    raw = vector_store.similarity_search_with_score(query, **search_kwargs)

    # Convert distance -> similarity for every candidate
    scored = []
    for doc, distance in raw:
        similarity = 1 - distance
        # Mutate a copy of metadata to avoid surprising other callers
        doc.metadata = {
            **doc.metadata,
            "similarity": similarity,
            "below_threshold": False,
        }
        scored.append((doc, similarity))

    # Sort high-to-low (Chroma usually does this, but make it explicit)
    scored.sort(key=lambda x: x[1], reverse=True)

    # Apply threshold
    passing = [doc for doc, sim in scored if sim >= min_similarity]

    if passing:
        return passing

    # Fallback: nothing cleared the bar — return top few, flagged
    fallback = []
    for doc, sim in scored[:fallback_k]:
        doc.metadata = {**doc.metadata, "below_threshold": True}
        fallback.append(doc)

    return fallback