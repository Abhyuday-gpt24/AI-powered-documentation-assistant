from src.models.models import groq_gpt_model, gpt_5_nano_model, deepseek_flash_model
from src.agents.tools.tools import all_tools

# Models with tools 
gpt_5_nano_model_with_tools = gpt_5_nano_model.bind_tools(all_tools)
groq_gpt_model_with_tools = groq_gpt_model.bind_tools(all_tools)
deepseek_flash_model_with_tools = deepseek_flash_model.bind_tools(all_tools)