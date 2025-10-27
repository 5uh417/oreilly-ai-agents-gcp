# agents/orchestrator_agent.py
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import (
                                                AGENT_CARD_WELL_KNOWN_PATH,
                                                RemoteA2aAgent,
)

# Load environment variables from .env file
load_dotenv()

# Configure the Remote Agent Client
# RemoteA2aAgent is the client-side component that knows how to talk to
# an A2A server. We configure it with the URL of our math_agent.
math_service = RemoteA2aAgent(
    name="math_service",
    description="A service that can perform mathematical calculations like addition.",
    agent_card=(
        f"http://localhost:8001{AGENT_CARD_WELL_KNOWN_PATH}"
    ),
)

# Define the Orchestrator Agent
root_agent = LlmAgent(
    model='gemini-2.5-pro',
    name='orchestrator_agent',
    instruction="""
    You are an orchestrator. You solve problems by delegating tasks to
    specialized services.
    If the user asks for an addition or a sum, you MUST use the 'math_service'.
    Do not perform the addition yourself.
    """,
    # The remote agent is treated just like a sub-agent
    sub_agents=[
        math_service
    ],
)
