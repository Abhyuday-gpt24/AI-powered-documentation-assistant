
from src.agents.graph_state import AgentState
from langgraph.graph import END


def route_after_analysis(state: AgentState) -> str | list[str]:
    intent = state.get("intent", "direct")
    if intent == "direct":
        return "token_check"            
    if intent == "web_search":
        return "web_search"
    if intent == "kb_retrieve":
        return ["kb_retrieval", "web_search"]
    return "token_check"                