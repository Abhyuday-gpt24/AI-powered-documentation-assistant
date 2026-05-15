from src.agents.mcp.tavily_search import load_tool
from src.rag_pipeline.retrieval import retrieve_tool
from langchain_core.documents import Document
import asyncio


# All tools 
retrieve_tool = retrieve_tool
web_search_tools = asyncio.run(load_tool())


all_tools = [retrieve_tool,*web_search_tools]



