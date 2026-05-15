from langchain_openai import ChatOpenAI
from langchain_deepseek import  ChatDeepSeek
from langchain_groq import ChatGroq
import os


#--------------------- Models wihout tools -------------------------

# Deepseek Flash
deepseek_flash_model = ChatDeepSeek(
    model="deepseek-v4-flash", 
    temperature=0, 
    max_tokens=2048,  
    api_key=os.getenv("DEEPSEEK_API_KEY"))

# Groq GPT OSS 20B
groq_gpt_model = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    max_tokens=2048,
    api_key=os.getenv("GROQ_API_KEY")
)

# OpenAI GPT 5 Nano
gpt_5_nano_model = ChatOpenAI(
    model="gpt-5-nano",
    temperature=0,
    max_tokens=2048,
    api_key=os.getenv("OPENAI_API_KEY")
)




