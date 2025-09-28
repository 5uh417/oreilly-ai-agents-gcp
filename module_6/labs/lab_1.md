# Enabling Your ADK Agent with MCP Tools

In this codelab, you'll learn how to extend the capabilities of your Google ADK agents by connecting them to external tools and services using the Model Context Protocol (MCP). MCP acts as a universal adapter, allowing your agent to communicate with a wide range of pre-built tools without needing to write custom integration code for each one.

We will build two distinct agent capabilities: one that interacts with your local filesystem and another that uses Google Maps to provide directions.

### **What you'll learn**

- The core concepts of the Model Context Protocol (MCP).
- How to use the `MCPToolset` in ADK to connect to an MCP server.
- How to integrate a local, file-based MCP server into your agent.

### **What you'll need**

- A computer with Python 3.9+ installed.
- A code editor like VS Code.
- Internet access.
- Basic proficiency in Python and comfort using the command-line terminal.
- Node.js and `npx` installed (many community MCP servers are distributed this way). You can install it from [nodejs.org](https://nodejs.org/en).

## Understanding the Model Context Protocol (MCP)

Before we write code, let's understand what MCP is.

The **Model Context Protocol (MCP)** is an open standard designed to create a common language between Large Language Models (LLMs) and external tools. Think of it as a universal plug that lets an LLM (or an AI agent built on one) connect to various services like databases, APIs, or local applications.

It works on a simple client-server model:

- **MCP Server:** An application that "exposes" a set of tools (e.g., `list_files`, `get_directions`). It advertises what tools it has and knows how to execute them.
- **MCP Client:** An application (like our ADK agent) that connects to an MCP server, discovers its tools, and calls them when needed.

In ADK, the `MCPToolset` class is the key component that acts as the MCP client. It handles all the complex parts of connecting to an MCP server, discovering its tools, and making them available to your agent as if they were native ADK tools.

```text
+-----------------+      1. Discover Tools      +---------------------+
|                 | --------------------------> |                     |
|    ADK Agent    |                             |      MCP Server     |
| (with MCPToolset)|      2. Call Tool("list")   | (e.g., Filesystem)  |
|                 | --------------------------> |                     |
|                 |                             |                     |
|                 |      3. Return Result       |                     |
|                 | <-------------------------- |                     |
+-----------------+                             +---------------------+
```

This architecture is powerful because it decouples your agent's logic from the tool's implementation. You can swap out MCP servers or add new ones without changing your core agent code.

## Setting Up Your Project

First, let's set up our project directory and install the necessary dependencies.

1.  Create a new project folder and navigate into it.

    ```console
    mkdir adk-mcp-lab
    cd adk-mcp-lab
    ```

2.  Create and activate a Python virtual environment. This is a best practice to keep your project dependencies isolated.

    ```console
    python3 -m venv .venv
    source .venv/bin/activate
    # On Windows, use: .venv\Scripts\activate
    ```

3.  Install the Google ADK library with the optional `mcp` dependencies.

    ```console
    pip install "google-adk[mcp]"
    ```

4.  Verify that `npx` (which comes with Node.js) is installed correctly.

    ```console
    which npx
    # On Windows, use: where npx
    ```

    If this command doesn't return a path, please [install Node.js](https://nodejs.org/en).

5.  Create a directory for your agent code. ADK discovers agents in Python packages, so we'll set it up correctly from the start.

    ```console
    mkdir adk_mcp_agent
    touch adk_mcp_agent/__init__.py
    ```

Your project structure should now look like this:

```text
adk-mcp-lab/
├── .venv/
└── adk_mcp_agent/
    └── __init__.py
```

Finally copy the `env` from the lab 1 of module 1.

## Lab 1: Building a Filesystem Agent

Our first agent will use a local MCP server that provides tools for interacting with the filesystem. This is a perfect "hello world" for MCP because it runs entirely on your machine and requires no API keys.

### Create the Agent Code

Create a new file named `adk_mcp_agent/agent.py` and add the following code.

```python
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
```

### Understanding the Code

- **`AGENT_WORKSPACE_PATH`**: We programmatically create an absolute path to a new directory named `agent_workspace`. This is crucial because the MCP server runs as a separate process and needs an absolute path to know where to operate. We also create a sample file inside for testing.
- **`LlmAgent`**: This is the standard ADK agent definition.
- **`MCPToolset`**: This is the magic part. We add it to our agent's `tools` list.
- **`StdioConnectionParams`**: This tells the `MCPToolset` to communicate with a local process using its standard input (`stdin`) and standard output (`stdout`).
- **`StdioServerParameters`**: This defines the command to start the MCP server.
  - `command='npx'`: We use `npx` to run the MCP server package.
  - `args=[...]`: We pass the package name (`@modelcontextprotocol/server-filesystem`) and the `AGENT_WORKSPACE_PATH` as arguments. The server will be sandboxed to this directory.

> **Security Best Practice:** By providing an absolute path to a specific `agent_workspace` directory and instructing the LLM to only operate within it, we are sandboxing the agent to prevent it from accessing sensitive files elsewhere on your system.

### Run and Test the Agent

1.  From your project's root directory (`adk-mcp-lab`), run the ADK web interface.

    ```console
    adk web
    ```

    The `adk web` command will automatically discover the `filesystem_agent` inside the `agents` package.

2.  Open your web browser to `http://127.0.0.1:8000`.

3.  Try the following prompts in the chat interface:
    - `Can you list the files in your directory?`
    - `Please read the contents of welcome.txt`

You should see the agent correctly list the file and then read its content, demonstrating that it's successfully using the tools provided by the filesystem MCP server.

## Congratulations!

You have successfully enabled your ADK agents with powerful external tools using the Model Context Protocol.

You have learned to connect to and use a local MCP server for filesystem operations.

This pattern of using `MCPToolset` is incredibly powerful. It allows you to tap into a growing ecosystem of open-source and third-party tools, dramatically accelerating your agent development and expanding the scope of what your agents can accomplish.

In the next part of this course, you will learn how to enable your own agents to communicate with each other using the Agent-to-Agent (A2A) protocol.
