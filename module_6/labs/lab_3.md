# Building a Multi-Agent System with A2A in ADK

Welcome to the final lab on multi-agent collaboration. So far, you have built agents that can use external tools via MCP. Now, you will learn how to make your ADK agents talk directly to _each other_.

The Agent-to-Agent (A2A) protocol is an open standard that enables this communication. It allows you to build systems composed of multiple, specialized agents that can delegate tasks and collaborate. Think of it like building a team of experts: one agent might orchestrate tasks, another might be an expert in calculations, and a third could specialize in data retrieval.

In this lab, you will build a complete, two-agent system from scratch:

1.  A **Specialist Agent** (`math_agent`) that is an expert at performing addition. We will **expose** this agent as a network service.
2.  An **Orchestrator Agent** that knows how to delegate math problems to the specialist. We will teach this agent to **consume** the `math_agent`.

### **What you'll learn**

- The core concepts of Agent-to-Agent (A2A) communication.
- How to **expose** an ADK agent as an A2A service using the `to_a2a()` utility.
- How to **consume** an A2A service in another agent using the `RemoteA2aAgent` class.
- The client-server model as it applies to multi-agent systems.

### **What you'll need**

- All prerequisites from the previous labs. You should be comfortable with the basic ADK project structure and the `adk web` interface.

## Step 1: Setting Up the Project Structure

First, make sure you have the necessary dependencies installed:

    ```console
    pip install google-adk[a2a]```

Let's organize our code. We will create separate files for each agent within our existing directory.

Create the two new empty files:

    ```console
    mkdir a2a_adk
    touch .env
    touch a2a_adk/__init__.py
    touch a2a_adk/math_agent.py
    touch a2a_adk/orchestrator_agent.py
    ```

**IMPORTANT**: Don't forget to activate venv in all terminals.

## Step 2: Create and Expose the Specialist Math Agent

Our first task is to build the `math_agent`. This agent will have one simple skill: adding two numbers. We will then expose this skill to the world (or at least our local network) using ADK's A2A utilities.

1.  Open the file `a2a_adk/math_agent.py` and add the following code:

    ```python
    from google.adk.agents import LlmAgent
    from google.adk.tools import FunctionTool
    from google.adk.a2a.utils.agent_to_a2a import to_a2a
    from dotenv import load_dotenv

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
    ```

### Understanding the Code

- **Skill (`add` function)**: This is a standard Python function that will serve as our agent's tool. We've added a `print` statement to make it clear when this agent is doing its work.
- **Agent Definition (`math_agent`)**: This is a standard `LlmAgent` that is equipped with the `add` tool.
- **Exposing (`to_a2a`)**: This is the key step. The `to_a2a()` function from the ADK library is a powerful utility. It takes a standard ADK agent and wraps it in a fully compliant A2A web server. We specify `port=8001` so it doesn't conflict with the `adk web` UI, which uses port 8000. This server will automatically provide an "agent card" at a well-known URL, which is like a business card describing the agent's capabilities.

## Step 3: Create and Configure the Orchestrator Agent

Now we build the `orchestrator_agent`. Its job is not to do math itself, but to recognize when math is needed and delegate the task to the `math_agent`. It will do this by "consuming" the A2A service we just created.

1.  Open the file `agents/orchestrator_agent.py` and add the following code:

    ```python
    # agents/orchestrator_agent.py
    from google.adk.agents import LlmAgent
    from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
    from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH
    from dotenv import load_dotenv

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
    ```

### Understanding the Code

- **`RemoteA2aAgent`**: This is the ADK class used to consume another A2A agent. It acts as a proxy or a client for the remote service.
- `name` and `description`: We give the remote agent a local name and description. This is crucial context that the `orchestrator_agent`'s LLM will use to decide when to delegate a task.
- `agent_card`: This is the most important parameter. We point it to the URL of the `math_agent`'s auto-generated agent card. The `AGENT_CARD_WELL_KNOWN_PATH` constant conveniently provides the standard `/`.well-known/agent-card.json`path. The`RemoteA2aAgent`will fetch this card to learn what tools the`math_agent` offers.
- `sub_agents=[math_service]`: From the `orchestrator_agent`'s perspective, the remote math service is just another sub-agent. The ADK abstracts away all the underlying network communication, making the developer experience simple and elegant.

## Step 4: Run the Multi-Agent System

This is the final step where everything comes together. To run our system, we need two separate processes running in two separate terminals.

> **Action Required:** You must use **two terminal windows** for this step. One for the A2A server (the specialist) and one for the `adk web` UI (the orchestrator).

**Terminal 1: Run the Specialist `math_agent` Server**

1.  Open your first terminal and make sure you are in the project root.
2.  Activate your virtual environment: `source .venv/bin/activate`.
3.  Run the `math_agent`'s A2A server using `uvicorn`, a standard Python web server.

        ````console
        uvicorn a2a_adk.math_agent:a2a_app --host localhost --port 8001
        ```

    This command tells `uvicorn` to run the `a2a_app` object found inside the `agents/math_agent.py` file. You should see output indicating the server is running on `http://127.0.0.1:8001`. Keep this terminal running.

**Terminal 2: Run the Orchestrator Agent UI**

1.  Open your second terminal. Navigate to the `adk-mcp-lab` project root.
2.  Activate your virtual environment: `source .venv/bin/activate`.
3.  Run the `adk web` interface as usual. It will automatically pick up our new `orchestrator_agent`.

    ```console
    adk web
    ```

**Interact with the System**

1.  Open your browser to `http://127.0.0.1:8000`.
2.  Select **`orchestrator_agent`** from the agent dropdown menu.
3.  Now, give it a math problem:
    - `What is 123 plus 456?`

**Observe the Magic!**

- In your browser, the `orchestrator_agent` will respond with the correct answer: `579`.
- Now, look at **Terminal 1** (the `uvicorn` server). You will see the log message we added: `[math_agent] Executing add(123, 456)`.

This confirms the entire workflow:

1.  You talked to the `orchestrator_agent`.
2.  It understood it needed to do addition and delegated the task to its `math_service` sub-agent.
3.  The `RemoteA2aAgent` (acting as a client) made a network call to the `math_agent` server running on port 8001.
4.  The `math_agent` server received the request, executed its `add` tool, and returned the result.
5.  The `orchestrator_agent` received the result and presented it to you.

## Congratulations!

You have successfully built and orchestrated a complete multi-agent system using the Agent-to-Agent protocol in ADK! This is a powerful paradigm that unlocks the ability to build complex, maintainable, and highly specialized AI applications.

You have mastered the two fundamental A2A operations:

- **Exposing** an agent as a service with `to_a2a`.
- **Consuming** that service in another agent with `RemoteA2aAgent`.

By understanding this pattern, you can now design systems where different agents, potentially maintained by different teams or even written in different frameworks (as long as they speak A2A), can collaborate to achieve a common goal.
