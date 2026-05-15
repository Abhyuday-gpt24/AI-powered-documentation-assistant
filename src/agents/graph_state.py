

from typing_extensions import TypedDict, Annotated
from langgraph.graph import add_messages
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    input_tokens: int
    summary: str
