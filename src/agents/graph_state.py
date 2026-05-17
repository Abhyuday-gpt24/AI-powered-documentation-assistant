from typing_extensions import TypedDict, Annotated
from langgraph.graph import add_messages
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    summary: str
    query: str
    reframed_query: str   # Cleaned / Reframed version of query.
    intent: str       # "direct" || "tools_needed"
    direct_reply: str
    retrieval_result: str
    web_search_result: str
    input_tokens: int 

