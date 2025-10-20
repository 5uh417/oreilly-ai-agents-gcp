from dotenv import load_dotenv
from google.adk.agents import LlmAgent

# Load environment variables
load_dotenv()

root_agent = LlmAgent(
    name="weather_time_agent",
    model="gemini-2.0-flash",
    description=(
        "Agent to answer questions about the time and weather in a city."
    ),
    instruction=(
        "You are a helpful agent who can answer user questions about the time and weather in a city. "
        "Be friendly and informative in your responses. If you don't have access to real-time data, "
        "let the user know and suggest how they can get current information."
    ),
)
