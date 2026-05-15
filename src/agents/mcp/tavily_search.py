
# For MCP Server
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.interceptors import MCPToolCallRequest
from langchain_core.messages import ToolMessage
from src.models.models import groq_gpt_model
import os
from dotenv import load_dotenv
load_dotenv()


MAX_CONTENT_SIZE = 2000

web_summerisation_sys_prompt = """You are an content  summeriser.
You need to  summerise the given data.
You will be provided the web search scrapped data and you need to  summerise it in a concise manner.
Make sure to  summerise the content in 1200 words.
And make sure the metadata is there as well like source of the content etc.
Here is the web search content: """


async def truncate_interceptor(request: MCPToolCallRequest, handler):
    result = await handler(request)
    # If it's a ToolMessage, truncate its content
    if isinstance(result, ToolMessage) and len(result.content) > MAX_CONTENT_SIZE:
        # result.content = result.content[:MAX_CONTENT_SIZE] + "… [TRUNCATED]"
        result.content = await groq_gpt_model.ainvoke(web_summerisation_sys_prompt + result.content)
        print("NEW WEB SEARCH: ")
        print(result.content)

    return result

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

async def load_tool():
    return await web_search_mcp_client.get_tools()


# print(f"Loaded {len(web_search_tools)} tools from Tavily MCP: {[t.name for t in web_search_tools]}")
