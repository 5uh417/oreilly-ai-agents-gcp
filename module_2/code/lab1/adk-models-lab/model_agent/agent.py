from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

root_agent = LlmAgent(
    name="weather_time_agent",
    model=LiteLlm(model="anthropic/claude-3-haiku-20240307"),
    description=(
        "Agent to answer questions about the time and weather in a city."
    ),
    instruction=(
        "You are a helpful agent who can answer user questions about the time and weather in a city. "
        "Be friendly and informative in your responses. If you don't have access to real-time data, "
        "let the user know and suggest how they can get current information."
    ),
)
