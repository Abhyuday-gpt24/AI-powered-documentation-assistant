from src.agents.graph_state import AgentState
from src.models.models_with_tools import gpt_5_nano_model, groq_gpt_model, deepseek_flash_model
from src.agents.sys_prompts.asistant_sys_prompt import get_query_analyzer_prompt, SYNTHESIZER_AGENT_SYS_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import json
from pydantic import BaseModel, Field
from typing import Literal

# Define the structure
class QueryAnalyzerInterface(BaseModel):
    intent: Literal["direct", "kb_retrieve", "web_search"] = Field(description="Requires searching a knowledge-base and the web or replied directly")
    reframed_query: str = Field(description="Corrected / Reframed user's query")
    direct_reply: str = Field(description="actual reply if intent is direct, else empty")



gpt_5_nano_str_output = gpt_5_nano_model.with_structured_output(QueryAnalyzerInterface, include_raw = True)
# Query Analyzer Node
async def query_analyzer_node(State: AgentState) -> AgentState:
    response = await gpt_5_nano_str_output.ainvoke([SystemMessage(get_query_analyzer_prompt()), *State["messages"]])
    result = response["parsed"]
    print("Analyzer Returned ------------->>>>>>>>>> \n", result)
    token_count = response["raw"].usage_metadata.get("total_tokens", 0) if hasattr(response["raw"], "usage_metadata") else 0
   
    if result.intent == "direct" and result.direct_reply:
        msgs = [AIMessage(content=result.direct_reply)]
    else:
        msgs = [response["raw"]]

    return {
        "messages": msgs,              # always a list
        "intent": result.intent,
        "reframed_query": result.reframed_query,
        "direct_reply": result.direct_reply,
        "retrieval_result": "",        # reset stale state from previous turn
        "web_search_result": "",       # reset stale state from previous turn
        "input_tokens": token_count
    }


async def synthesizer_agent_node(state: AgentState) -> dict:
    kb = state.get("retrieval_result", "")
    web = state.get("web_search_result", "")

    context_msg = SystemMessage(
        f"{SYNTHESIZER_AGENT_SYS_PROMPT}\n\n"
        f"Retrieved context:\n{kb}\n\nWeb search results:\n{web}"
    )

    response = await gpt_5_nano_model.ainvoke([
        context_msg,
        HumanMessage(state["query"]),
    ])
    return {"messages": [response]}

