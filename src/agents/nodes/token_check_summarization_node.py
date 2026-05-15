from src.agents.graph_state import AgentState
from src.models.models_with_tools import gpt_5_nano_model, groq_gpt_model_with_tools, deepseek_flash_model_with_tools
from src.agents.sys_prompts.conv_summarizer_sys_prompt import CONV_SUMMARIZER_SYS_PROMPT
from langchain_core.messages import HumanMessage, SystemMessage, RemoveMessage



# Tokens checking for summarization
async def token_check_node(State: AgentState) -> AgentState:
    input_tokens = State["input_tokens"]
    print("Context_used : ------", input_tokens)
    if input_tokens > 12500:
        print("----------------------------------- ALERT TOKEN LIMIT REACHED ----------------------------------")
        print("Summarizing History.")

        messages = State["messages"]
        existing_summary = State.get("summary", "")

        # Reverse loop
        cut = None
        for i in range(len(messages) - 1, -1, -1):
            msg = messages[i]
            has_tool_calls = hasattr(msg, "tool_calls") and msg.tool_calls
            has_tool_call_id = hasattr(msg, "tool_call_id") and msg.tool_call_id

            if not has_tool_calls and not has_tool_call_id:
                cut = i
                break

        if cut is None or cut <= 0:
            return {}

        msg_to_summarize = messages[:cut]

        if existing_summary:
            user_prompt = (
                f"Previous conversation summary:\n{existing_summary}\n\n"
                "Extend the previous summary with this new chat history. "
                "Summarize the whole conversation in 700-1000 words only. "
                "Keep it concise."
            )
        else:
            user_prompt = (
                "I have given you chat history of the user. "
                "Summarize the whole conversation in 700-1000 words only. "
                "Keep it concise."
            )

        response = await gpt_5_nano_model.ainvoke([
            SystemMessage(CONV_SUMMARIZER_SYS_PROMPT),
            *msg_to_summarize,
            HumanMessage(user_prompt),
        ])

        snapshot_ids = {m.id for m in msg_to_summarize}
        delete_ops = [
            RemoveMessage(id=m.id)
            for m in messages
            if m.id in snapshot_ids
        ]
        print("SUMMARY : --------------------- :", response.content)
        return {
            "messages": delete_ops,
            "summary": response.content,
        }
    return {}