from src.rag_pipeline.retrieval import retrieve_function
from src.agents.graph_state import AgentState
from langsmith import traceable

def retrieve_tool(state: AgentState)-> AgentState:
    query = state.get("reframed_query") or state["query"]
    result = retrieve_function(query)
    return {"retrieval_result": result}