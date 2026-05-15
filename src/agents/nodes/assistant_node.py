from src.agents.graph_state import AgentState
from src.models.models_with_tools import gpt_5_nano_model_with_tools, groq_gpt_model_with_tools, deepseek_flash_model_with_tools
from src.agents.sys_prompts.asistant_sys_prompt import AGENT_SYS_PROMPT
from langchain_core.messages import SystemMessage




# Assistant Node
async def assistant_node(State: AgentState) -> AgentState:
    response = await gpt_5_nano_model_with_tools.ainvoke([SystemMessage(AGENT_SYS_PROMPT), *State["messages"]])
    context_tokens = response.usage_metadata["input_tokens"]
    return {
        "messages": response,
        "input_tokens":context_tokens
    }