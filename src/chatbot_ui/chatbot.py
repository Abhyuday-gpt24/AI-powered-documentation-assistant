# Gradio chat function
import gradio as chatbox
from langchain_core.messages import HumanMessage
import uuid
from src.agents.graph import graph_build
from datetime import datetime

def current_time()-> datetime:
    now = datetime.now()
    return now

graph = graph_build()
def new_thread_id() -> str:
    return str(uuid.uuid4())

async def chatbot_func(message: str, history: list[dict], thread_id: str) :
    config = {"configurable": {"thread_id": thread_id}}
    input_data = {
        "messages": [HumanMessage(content=(message))],
        "retrieval_result": "",
        "web_search_result": "",
        "intent": ""
    }

    full_response = ""
    async for event in graph.astream_events(input_data, config=config, version="v2"):
        kind = event["event"]
        # Stream tokens from the final synthesizer node only
        if kind == "on_chat_model_stream":
            node = event.get("metadata", {}).get("langgraph_node", "")
            if node == "synthesizer_agent_node":  # only this node
                chunk = event["data"]["chunk"]
                if hasattr(chunk, "content") and chunk.content:
                    full_response += chunk.content
                    yield full_response

    # Direct replies don't go through synthesizer — fetch from final state
    if not full_response:
        state = await graph.aget_state(config)
        last_msg = state.values["messages"][-1]
        yield last_msg.content


# UI
with chatbox.Blocks(title="AI-powered documentation assistant") as ai_powered_documentation_assistant:
    chatbox.Markdown("# AI-powered documentation assistant v0")
 
    thread_id = chatbox.State(value=new_thread_id)
 
    chatbot = chatbox.ChatInterface(
        fn=chatbot_func,
        additional_inputs=[thread_id]
    )
 
    clear = chatbox.Button("Start new conversation")
    clear.click(fn=new_thread_id, outputs=thread_id)

