from langgraph.graph import add_messages
from typing_extensions import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from src.models.models import gpt_5_nano_model, groq_gpt_model, deepseek_flash_model
from src.agents.prompts import AGENT_SYS_PROMPT
from langgraph.prebuilt import ToolNode, tools_condition
from src.agents.tools.tools import all_tools
from langgraph.checkpoint.memory import MemorySaver

# -------------------- Models with tools ---------------------

gpt_5_nano_model_with_tools = gpt_5_nano_model.bind_tools(all_tools)
groq_gpt_model_with_tools = groq_gpt_model.bind_tools(all_tools)
deepseek_flash_model_with_tools = deepseek_flash_model.bind_tools(all_tools)


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


# Agent Node
async def agent_node(AgentState: AgentState) -> AgentState:
    response = await gpt_5_nano_model_with_tools.ainvoke([SystemMessage(AGENT_SYS_PROMPT), *AgentState["messages"]])
    return {"messages": [response]}



def graph_build():
    graph = StateGraph(AgentState)
    graph.add_node("agent_node", agent_node)
    graph.add_node("tools",ToolNode(all_tools))
    graph.add_edge(START, "agent_node")
    graph.add_conditional_edges("agent_node",tools_condition)
    graph.add_edge("tools","agent_node")
    return graph.compile(checkpointer=MemorySaver())




