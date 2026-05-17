
# For MCP Server
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from src.models.models import groq_gpt_model
from src.agents.graph_state import AgentState
import os
from dotenv import load_dotenv
from langsmith import traceable
load_dotenv()


# Tavily MCP Handshake
TAVILY_MCP_LINK = os.environ.get("TAVILY_MCP_LINK")
if not TAVILY_MCP_LINK:
    raise RuntimeError("Set TAVILY_MCP_LINK in your environment first.")
 
web_search_mcp_client = MultiServerMCPClient(
    {
        "tavily": {
            "url": f"{TAVILY_MCP_LINK}",
            "transport": "streamable_http",
        }
    }
)

web_search_tavily_tool = None
async def load_search_tool():
    global web_search_tavily_tool
    if web_search_tavily_tool is None:
        tools = await web_search_mcp_client.get_tools()
        web_search_tavily_tool = next(t for t in tools if t.name == "tavily_search")



async def web_search(query: str) -> AgentState:
    
    await load_search_tool()
    result = await web_search_tavily_tool.ainvoke({"query": query})

    if hasattr(result, "content"):
        content = result.content
    else:
        content = str(result)

    return {"web_search_result": content[:3000]}

