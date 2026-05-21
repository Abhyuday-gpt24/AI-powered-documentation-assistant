from src.agents.graph_state import AgentState
from src.models.models import gpt_5_nano_model, groq_gpt_model, deepseek_flash_model
from src.agents.sys_prompts.asistant_sys_prompt import QUERY_ANALYZER_SYS_PROMPT, SYNTHESIZER_AGENT_SYS_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import json
from pydantic import BaseModel, Field
from typing import Literal

# Define the structure
class QueryAnalyzerInterface(BaseModel):
    intent: Literal["direct", "kb_retrieve", "web_search"] = Field(description="""Specify the intent "direct", "kb_retrieve", "web_search" """)
    reframed_query: str = Field(description="Corrected / Reframed user's query for friendly search.")
    direct_reply: str = Field(description="actual reply if intent is direct, else empty.")

gpt_5_nano_structured_output = gpt_5_nano_model.with_structured_output(QueryAnalyzerInterface, include_raw = True)


# Query Analyzer Node
async def query_analyzer_node(state: AgentState) -> AgentState:
    summary = state.get("summary", "")
    system_prompt = QUERY_ANALYZER_SYS_PROMPT
    if summary:
        system_prompt += f"\n\nPrevious conversation summary:\n{summary}"
    response = await gpt_5_nano_structured_output.ainvoke([SystemMessage(system_prompt), *state["messages"]])

    result = response["parsed"]
    print("Result : " , result)

    token_count = response["raw"].usage_metadata.get("total_tokens", 0) if hasattr(response["raw"], "usage_metadata") else 0
    if result.intent == "direct" and result.direct_reply:
        msgs = [AIMessage(content=result.direct_reply)]
    else:
        msgs = [*state["messages"]]

    return {
        "messages": msgs,
        "intent": result.intent,
        "reframed_query": result.reframed_query,
        "retrieval_result": "",
        "web_search_result": "",
        "input_tokens": token_count
    }


async def synthesizer_agent_node(state: AgentState) -> AgentState:
    kb = state.get("retrieval_result", "")
    web = state.get("web_search_result", "")



    summary = state.get("summary", "")

    sys_prompt = SYNTHESIZER_AGENT_SYS_PROMPT
    sys_prompt += f"\n\nRetrieved context:\n{kb}\n\nWeb search results:\n{web}"
    if summary:
        sys_prompt += f"\n\nPrevious conversation summary:\n{summary}"

    response = await deepseek_flash_model.ainvoke([
        SystemMessage(sys_prompt),
        *state["messages"],
    ])
    return {"messages": [response]}


    