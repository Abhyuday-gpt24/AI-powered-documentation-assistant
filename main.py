from dotenv import load_dotenv
load_dotenv()
from src.chatbot_ui.chatbot import ai_powered_documentation_assistant
from src.rag_pipeline.data_ingestion.data_ingeston import runpipe


def main():
    print("Hello from ai-powered-documentation-assistant!")
    # ai_powered_documentation_assistant.launch()
    runpipe()
    


if __name__ == "__main__":
    main()
