from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from src.agents.tools.tools import all_tools
from langgraph.checkpoint.memory import MemorySaver
from src.agents.nodes.assistant_node import assistant_node
from src.agents.nodes.token_check_summarization_node import token_check_node
from src.agents.nodes.structured_response_node import structured_response
from src.agents.graph_state import AgentState






def graph_build():
    graph = StateGraph(AgentState)
    graph.add_node("assistant_node", assistant_node)
    graph.add_node("tools", ToolNode(all_tools))
    graph.add_node("structured_response", structured_response)
    graph.add_node("token_check", token_check_node)

    graph.add_edge(START, "assistant_node")

    graph.add_conditional_edges(
        "assistant_node",
        tools_condition,
        {
            "tools": "tools",
            "__end__": "structured_response",  # format first, not token_check
        }
    )
    graph.add_edge("tools", "assistant_node")
    graph.add_edge("structured_response", "token_check")  # then check tokens
    graph.add_edge("token_check", END)

    return graph.compile(checkpointer=MemorySaver())