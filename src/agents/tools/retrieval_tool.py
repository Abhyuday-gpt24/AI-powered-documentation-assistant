from src.rag_pipeline.vector_store import get_retriever
from src.agents.graph_state import AgentState
from langsmith import traceable

def retrieve_tool(state: AgentState)-> AgentState:
    retriever = get_retriever()
    query = state.get("reframed_query") or state["query"]
    result = retriever.invoke(query)
    return {"retrieval_result": result}