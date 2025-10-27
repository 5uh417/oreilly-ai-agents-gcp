from dotenv import load_dotenv
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

# Load environment variables from .env file
load_dotenv()

# Define the Agent's Core Skill
def add(a: int, b: int) -> int:
    """Adds two integers together."""
    print(f"[math_agent] Executing add({a}, {b})")
    return a + b

# Define the ADK Agent
math_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='math_agent',
    instruction="You are a math expert. You use the 'add' tool to perform addition.",
    tools=[
        FunctionTool(add)
    ],
)

# Expose the Agent via A2A
# The to_a2a() function wraps our agent in a web server application (FastAPI)
# that speaks the A2A protocol. It also auto-generates the required
# agent card so other agents know how to talk to it.
a2a_app = to_a2a(math_agent, port=8001)
