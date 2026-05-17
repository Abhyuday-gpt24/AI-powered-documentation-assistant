from src.rag_pipeline.retrieval import retrieve_function
from src.agents.graph_state import AgentState


def retrieve_tool(State: AgentState)-> AgentState:
    result = retrieve_function(State["query"])
    return {"retrieval_result": result}