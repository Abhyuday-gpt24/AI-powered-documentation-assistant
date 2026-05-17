from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from src.agents.tools.retrieval_tool import retrieve_tool
from langgraph.checkpoint.memory import MemorySaver
from src.agents.nodes.agent_nodes import query_analyzer_node, synthesizer_agent_node
from src.agents.nodes.token_check_summarization_node import token_check_node
from src.agents.mcp.tavily_search import web_search
from src.agents.graph_state import AgentState
from src.agents.nodes.router_nodes import route_after_analysis


def graph_build():
    graph = StateGraph(AgentState)
    graph.add_node("query_analyzer_node", query_analyzer_node)
    graph.add_node("kb_retrieval", retrieve_tool)
    graph.add_node("web_search", web_search)
    graph.add_node("synthesizer_agent_node", synthesizer_agent_node)
    graph.add_node("token_check", token_check_node)

    graph.add_edge(START, "query_analyzer_node")
    graph.add_conditional_edges(
        "query_analyzer_node",
        route_after_analysis,
        # explicit map so LangGraph knows all possible targets
        {
            "token_check": "token_check",
            "web_search": "web_search",
            "kb_retrieval": "kb_retrieval",
        },
    )
    graph.add_edge("kb_retrieval", "synthesizer_agent_node")
    graph.add_edge("web_search", "synthesizer_agent_node")
    graph.add_edge("synthesizer_agent_node", "token_check")  # then check tokens
    graph.add_edge("token_check", END)

    return graph.compile(checkpointer=MemorySaver())