from typing_extensions import TypedDict, Annotated
from langgraph.graph import add_messages
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    reframed_query: str   # Cleaned / Reframed version of query.
    intent: str       # "direct" || "tools_needed"
    retrieval_result: str
    web_search_result: str
    input_tokens: int 
