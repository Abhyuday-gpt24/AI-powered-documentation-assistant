from dotenv import load_dotenv
load_dotenv()
from src.chatbot_ui.chatbot import ai_powered_documentation_assistant


def main():
    print("Hello from ai-powered-documentation-assistant!")
    ai_powered_documentation_assistant.launch()


if __name__ == "__main__":
    main()
