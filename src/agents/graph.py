from langgraph.graph import add_messages
from typing_extensions import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage,RemoveMessage
from src.models.models import gpt_5_nano_model, groq_gpt_model, deepseek_flash_model
from src.agents.prompts import AGENT_SYS_PROMPT, CON_SUMMARIZER_SYS_PROMPT
from langgraph.prebuilt import ToolNode, tools_condition
from src.agents.tools.tools import all_tools
from langgraph.checkpoint.memory import MemorySaver
import asyncio
from src.agents.tools.format_response_regex import format_response

# Models with tools 
gpt_5_nano_model_with_tools = gpt_5_nano_model.bind_tools(all_tools)
groq_gpt_model_with_tools = groq_gpt_model.bind_tools(all_tools)
deepseek_flash_model_with_tools = deepseek_flash_model.bind_tools(all_tools)


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    input_tokens: int
    summary: str


# Agent Node
async def agent_node(State: AgentState) -> AgentState:
    response = await gpt_5_nano_model_with_tools.ainvoke([SystemMessage(AGENT_SYS_PROMPT), *State["messages"]])
    context_tokens = response.usage_metadata["input_tokens"]
    return {
        "messages": response,
        "input_tokens":context_tokens
    }


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


    
# Token Check Node
async def token_check_node(State: AgentState) -> AgentState:
    input_tokens = State["input_tokens"]
    print("Context_used : ------", input_tokens)
    if input_tokens > 10000:
        print("----------------------------------- ALERT TOKEN LIMIT REACHED ----------------------------------")
        print("Summarizing History.")

        messages = AgentState["messages"]
        existing_summary = AgentState.get("summary", "")
        msg_to_summarize = messages[:-2]

        if existing_summary:
            user_prompt = (
                f"""Previous conversation summary:\n{existing_summary}\n\n
                Extend the previous summary with this new chat history.
                Summarize the whole conversation in 700-1000 words only. 
                Keep it concise."""
            )
        else:
            user_prompt = """I have given you chat history of the user. 
            Summarize the whole conversation in 700-1000 words only. 
            Keep it concise."""

        response = await gpt_5_nano_model.ainvoke([
            SystemMessage(CON_SUMMARIZER_SYS_PROMPT),
            *msg_to_summarize,
            HumanMessage(user_prompt),
        ])

        snapshot_ids = {m.id for m in msg_to_summarize}
        delete_ops = [
            RemoveMessage(id=m.id)
            for m in messages
            if m.id in snapshot_ids
        ]

        return {
            "messages": delete_ops,
            "summary": response.content,
        }
    return {}


def graph_build():
    graph = StateGraph(AgentState)
    graph.add_node("agent_node", agent_node)
    graph.add_node("tools", ToolNode(all_tools))
    graph.add_node("structured_response", structured_response)
    graph.add_node("token_check", token_check_node)

    graph.add_edge(START, "agent_node")

    graph.add_conditional_edges(
        "agent_node",
        tools_condition,
        {
            "tools": "tools",
            "__end__": "structured_response",  # format first, not token_check
        }
    )
    graph.add_edge("tools", "agent_node")
    graph.add_edge("structured_response", "token_check")  # then check tokens
    graph.add_edge("token_check", END)

    return graph.compile(checkpointer=MemorySaver())