import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create a test directory for the agent to access
# Get the absolute path of the directory containing this script
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Define the path for the agent's workspace
AGENT_WORKSPACE_PATH = os.path.join(_CURRENT_DIR, "agent_workspace")

# Create the directory if it doesn't exist
if not os.path.exists(AGENT_WORKSPACE_PATH):
    os.makedirs(AGENT_WORKSPACE_PATH)
    # Create a dummy file inside for the agent to find
    with open(os.path.join(AGENT_WORKSPACE_PATH, "welcome.txt"), "w") as f:
        f.write("Hello from your ADK agent's workspace!")

# Define the Filesystem Agent
root_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='filesystem_agent',
    instruction=f"""
    You are a helpful assistant that can interact with a user's local file system.
    You are restricted to operate ONLY within the following directory: {AGENT_WORKSPACE_PATH}.
    Never attempt to access files or directories outside of this path.
    When a user asks you to list files, use the 'list_directory' tool.
    When a user asks you to read a file, use the 'read_file' tool.
    """,
    tools=[
        MCPToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command='npx',
                    args=[
                        "-y",  # Auto-confirm npx installation prompts
                        "@modelcontextprotocol/server-filesystem",
                        # IMPORTANT: This MUST be an absolute path.
                        AGENT_WORKSPACE_PATH,
                    ],
                ),
            ),
            # Optional: Explicitly filter which tools are exposed to the agent
            tool_filter=['list_directory', 'read_file']
        )
    ],
)
