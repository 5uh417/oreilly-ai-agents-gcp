from google.adk.agents import Agent
from ...config import GENAI_MODEL
from .prompt import CHECKER_PROMPT
from .tools.loop_condition_tool import check_tool_condition


# This agent is responsible for checking conditions and validating the scoring process
# It uses the check_tool_condition tool to evaluate whether the scoring process should continue
# The agent's output is stored in the "checker_output" key
checker_agent_instance = Agent(
    name="checker_agent",
    model=GENAI_MODEL,
    instruction=CHECKER_PROMPT,
    tools=[check_tool_condition],
    output_key="checker_output",
)