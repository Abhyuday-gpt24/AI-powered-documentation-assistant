from src.agents.graph_state import AgentState
from langchain_core.messages import RemoveMessage, AIMessage
from src.agents.utils.format_response_regex import format_response



# Structured Response node
def structured_response(State: AgentState) -> AgentState:
    ai_res = State["messages"][-1]
    formated_res = format_response(ai_res.content)
    return {
        "messages": [
            RemoveMessage(id=ai_res.id),        
            AIMessage(content=formated_res)         
        ]
    }