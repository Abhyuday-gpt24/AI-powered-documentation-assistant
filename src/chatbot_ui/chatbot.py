# Gradio chat function
import gradio as chatbox
from langchain_core.messages import HumanMessage
import uuid
from src.agents.graph import graph_build

graph = graph_build()
def new_thread_id() -> str:
    return str(uuid.uuid4())

async def chatbot_func(message: str, history: list[dict], thread_id: str) -> str:
    config = {"configurable": {"thread_id": thread_id}}
    result = await graph.ainvoke(
        {
            "messages": [HumanMessage(content=message)],
            "query": message,
            "retrieval_result": "",
            "web_search_result": "",
            "summary": "",
            "direct_reply": "",
        },
        config=config,
    )
    return result["messages"][-1].content


# UI
with chatbox.Blocks(title="AI-powered documentation assistant") as ai_powered_documentation_assistant:
    chatbox.Markdown("# AI-powered documentation assistant v0")
 
    thread_id = chatbox.State(value=new_thread_id)
 
    chatbot = chatbox.ChatInterface(
        fn=chatbot_func,
        additional_inputs=[thread_id],
    )
 
    clear = chatbox.Button("Start new conversation")
    clear.click(fn=new_thread_id, outputs=thread_id)

