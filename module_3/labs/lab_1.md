# Giving Your AI Agent a Memory with ADK

In this lab, you'll learn one of the most powerful concepts in building advanced AI agents: **memory**. Just like humans, agents need to recall past interactions to hold meaningful, context-aware conversations. You will enhance a basic agent by giving it a short-term, in-memory store, allowing it to remember information from one conversation and use it in the next.

This lab focuses on `InMemoryMemoryService`, the perfect tool for local development and prototyping. You will see firsthand how an agent can store information and then recall it later to answer questions, making its responses smarter and more relevant.

## What you'll learn

- The difference between short-term (`Session`) and long-term (`Memory`) context.
- How to configure a `Runner` with `InMemoryMemoryService`.
- How to equip an agent with a `Tool` to search its memory.
- The workflow for adding a completed conversation to memory.
- How to run a multi-turn scenario where an agent recalls previously stored information.
- The conceptual difference between `Memory` (for searchable context) and `Artifacts` (for binary data).

## Prerequisites & Setup

Before we begin, ensure you have your environment set up as outlined in the course prerequisites: a computer with Python, a code editor, and the ADK library installed.

We'll start with a basic Python script that defines two agents but has no memory capabilities.

#### **Project Setup**

1.  Create a new directory for this lab called `my_agent_with_memory`.
2.  Inside that directory, create a single Python file named `memory_lab.py`, the `__init__.py` and `.env` files
3.  Copy the `__init__.py` and `.env` files from module_1.
4.  Copy the following starter code into `run_agent.py`. This code defines our two agents: one to capture information and one that will eventually recall it.

```python
# run_agent.py (Starter Code)

import asyncio
from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai.types import Content, Part
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# 1. Define Constants
APP_NAME = "memory_lab_app"
USER_ID = "test_user_123"
MODEL = "gemini-2.5-flash"

# 2. Define Agents

# This agent's only job is to have a conversation where the user provides a piece of information.
info_capture_agent = LlmAgent(
    model=MODEL,
    name="InfoCaptureAgent",
    instruction="You are an assistant. Acknowledge the user's statement in a friendly tone.",
)

# This agent will eventually be able to recall information from memory.
memory_recall_agent = LlmAgent(
    model=MODEL,
    name="MemoryRecallAgent",
    instruction="Answer the user's question. If you don't know the answer, say so.",
)

# 3. Define the Main Scenario Logic
async def run_memory_scenario():
    """Runs a two-turn scenario to demonstrate memory."""
    print("Scenario starting... (Memory NOT IMPLEMENTED yet)")

    # This is where we will add the memory service and run our scenario.

# 4. Run the Script
if __name__ == "__main__":
    asyncio.run(run_memory_scenario())

```

## Implement the InMemoryMemoryService

Now, let's add memory to our application. The `InMemoryMemoryService` stores conversational history in your computer's RAM. It's fast and requires no setup, but remember: all stored memory is lost when the script ends.

#### **1. Import the Memory Service and Memory Tool**

Add the following imports to the top of `run_agent.py`:

```python
from google.adk.memory import InMemoryMemoryService # Import the memory service
from google.adk.tools import load_memory          # Import the built-in tool for searching memory
```

#### **2. Equip the `memory_recall_agent` with the `load_memory` Tool**

For an agent to be able to search the memory, it needs the right tool. Update the definition of `memory_recall_agent` to include the `load_memory` tool and adjust its instructions to encourage using it.

```python
# run_agent.py

# ... (previous code) ...

# This agent will eventually be able to recall information from memory.
memory_recall_agent = LlmAgent(
    model=MODEL,
    name="MemoryRecallAgent",
    instruction="Answer the user's question. Use the 'load_memory' tool "
                "if the answer might be in past conversations.",
    tools=[load_memory] # <-- ADD THIS LINE
)

# ... (rest of the code) ...
```

#### **3. Instantiate the Services**

Inside the `run_memory_scenario` function, we need to create instances of our services. We'll create a single `InMemorySessionService` and a single `InMemoryMemoryService` to be shared across both conversational turns. This is the key to sharing context.

Update the `run_memory_scenario` function like this:

```python
# run_agent.py

# ... (previous code) ...

async def run_memory_scenario():
    """Runs a two-turn scenario to demonstrate memory."""
    print("🚀 Scenario starting with InMemoryMemoryService!")

    # Instantiate the services that will be shared.
    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()

    # The rest of our logic will go here.
```

Now our application is configured to use memory. In the next step, we'll implement the logic to store and retrieve it.

## The "Memory" Workflow: Storing and Recalling

The core workflow for using memory in ADK involves two distinct steps:

1.  **Ingesting:** After a conversation is complete, you explicitly add its `Session` object to the `MemoryService`.
2.  **Recalling:** In a future conversation, an agent equipped with the `load_memory` tool can search that `MemoryService` for relevant information.

Let's implement this flow.

#### **Part 1: The First Conversation (Storing Information)**

Add the following code inside `run_memory_scenario`, right after you instantiate the services. This code block will run our `info_capture_agent`, get the user's favorite color, and then save that entire conversation to our `memory_service`.

```python
# memory_lab.py -> inside run_memory_scenario()

    # TURN 1: CAPTURE AND STORE INFORMATION
    print("\n--- Turn 1: Capturing Information ---")
    runner1 = Runner(
        agent=info_capture_agent,
        app_name=APP_NAME,
        session_service=session_service,
        memory_service=memory_service # Provide the memory service to the Runner
    )
    session1_id = "session_for_storing"
    await runner1.session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session1_id
    )
    user_input1 = Content(parts=[Part(text="My favorite color is blue.")], role="user")

    print(f"👤 User Input: {user_input1.parts[0].text}")

    # Run the agent and print its response
    async for event in runner1.run_async(
        user_id=USER_ID, session_id=session1_id, new_message=user_input1
    ):
        if event.is_final_response() and event.content and event.content.parts:
            print(f"🤖 Agent 1 Response: {event.content.parts[0].text}")

    # CRITICAL STEP: Add the completed session to the memory service
    print("\n--- Adding Session 1 to Memory ---")
    completed_session1 = await runner1.session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session1_id
    )
    await memory_service.add_session_to_memory(completed_session1)
    print("✅ Session added to memory.")

```

#### **Part 2: The Second Conversation (Recalling Information)**

Now, add the final block of code to `run_memory_scenario`. This part simulates a completely new conversation. We'll use our `memory_recall_agent` and ask it about our favorite color. Because its `Runner` is connected to the _same_ `memory_service`, the `load_memory` tool will find the context from Turn 1.

```python
# run_agent.py -> inside run_memory_scenario()

    # TURN 2: RECALL INFORMATION IN A NEW SESSION
    print("\n--- Turn 2: Recalling Information ---")
    runner2 = Runner(
        agent=memory_recall_agent, # Use the second agent
        app_name=APP_NAME,
        session_service=session_service, # Reuse the same services
        memory_service=memory_service
    )
    session2_id = "session_for_recalling"
    await runner2.session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session2_id
    )
    user_input2 = Content(parts=[Part(text="What is my favorite color?")], role="user")

    print(f"👤 User Input: {user_input2.parts[0].text}")

    # Run the second agent and print its response
    async for event in runner2.run_async(
        user_id=USER_ID, session_id=session2_id, new_message=user_input2
    ):
        if event.is_final_response() and event.content and event.content.parts:
            print(f"🤖 Agent 2 Response: {event.content.parts[0].text}")
```

## Run and Observe

Your `run_agent.py` file should now be complete. It's time to run it and see the memory in action!

#### **Final Code**

For your reference, here is the complete code for `run_agent.py`:

```python
# run_agent.py (Final Code)

import asyncio
from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.memory import InMemoryMemoryService
from google.adk.tools import load_memory
from google.genai.types import Content, Part
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# 1. Define Constants
APP_NAME = "memory_lab_app"
USER_ID = "test_user_123"
MODEL = "gemini-1.5-flash"

# 2. Define Agents
info_capture_agent = LlmAgent(
    model=MODEL,
    name="InfoCaptureAgent",
    instruction="You are an assistant. Acknowledge the user's statement in a friendly tone.",
)

memory_recall_agent = LlmAgent(
    model=MODEL,
    name="MemoryRecallAgent",
    instruction="Answer the user's question. Use the 'load_memory' tool "
                "if the answer might be in past conversations.",
    tools=[load_memory]
)

# 3. Define the Main Scenario Logic
async def run_memory_scenario():
    """Runs a two-turn scenario to demonstrate memory."""
    print("🚀 Scenario starting with InMemoryMemoryService!")

    # Instantiate the services that will be shared.
    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()

    # TURN 1: CAPTURE AND STORE INFORMATION
    print("\n--- Turn 1: Capturing Information ---")
    runner1 = Runner(
        agent=info_capture_agent,
        app_name=APP_NAME,
        session_service=session_service,
        memory_service=memory_service
    )
    session1_id = "session_for_storing"
    await runner1.session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session1_id
    )
    user_input1 = Content(parts=[Part(text="My favorite color is blue.")], role="user")

    print(f"👤 User Input: {user_input1.parts[0].text}")

    async for event in runner1.run_async(
        user_id=USER_ID, session_id=session1_id, new_message=user_input1
    ):
        if event.is_final_response() and event.content and event.content.parts:
            print(f"🤖 Agent 1 Response: {event.content.parts[0].text}")

    print("\n--- Adding Session 1 to Memory ---")
    completed_session1 = await runner1.session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session1_id
    )
    await memory_service.add_session_to_memory(completed_session1)
    print("✅ Session added to memory.")

    # TURN 2: RECALL INFORMATION IN A NEW SESSION
    print("\n--- Turn 2: Recalling Information ---")
    runner2 = Runner(
        agent=memory_recall_agent,
        app_name=APP_NAME,
        session_service=session_service,
        memory_service=memory_service
    )
    session2_id = "session_for_recalling"
    await runner2.session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session2_id
    )
    user_input2 = Content(parts=[Part(text="What is my favorite color?")], role="user")

    print(f"👤 User Input: {user_input2.parts[0].text}")

    async for event in runner2.run_async(
        user_id=USER_ID, session_id=session2_id, new_message=user_input2
    ):
        if event.is_final_response() and event.content and event.content.parts:
            print(f"🤖 Agent 2 Response: {event.content.parts[0].text}")

# --- 4. Run the Script ---
if __name__ == "__main__":
    # NOTE: You may need to set your GOOGLE_API_KEY environment variable.
    asyncio.run(run_memory_scenario())
```

#### **Execute the Script**

Open your terminal, navigate to the `adk_memory_lab` directory, and run the file:

```console
python run_agent.py
```

#### **Expected Output**

You should see output similar to the following. The key is that Agent 2 correctly identifies the favorite color without being told in the second conversation.

```console
🚀 Scenario starting with InMemoryMemoryService!

--- Turn 1: Capturing Information ---
🤖 Agent 1 Response: That's a great choice! Blue is a very calming color.

--- Adding Session 1 to Memory ---
✅ Session added to memory.

--- Turn 2: Recalling Information ---
🤖 Agent 2 Response: Your favorite color is blue.
```

## Memory vs. Artifacts: A Conceptual Bridge

You've successfully used **Memory**. But what about multimodal agents? What if the user had sent an image instead of text? This is where another ADK concept, **Artifacts**, becomes important.

> **Memory vs. Artifacts**
>
> - **Memory (`MemoryService`)** is for storing and searching **conversational context**. Think of it as a searchable log of things that were said. The information is primarily textual and is used by the LLM to understand history.
>
> - **Artifacts (`ArtifactService`)** are for storing and retrieving named, versioned **binary data**. Think of these as files: images, PDFs, audio clips, etc. They are not directly searchable by the `load_memory` tool but can be loaded by filename to be processed by other tools.

## Congratulations!

You have successfully implemented a core component of intelligent agents: memory!

You learned how to use `InMemoryMemoryService` to allow an agent to recall information across different sessions. You also saw the complete workflow from capturing information, adding it to memory, and finally recalling it with a different agent. Finally, you understand the conceptual difference between storing conversational context in `Memory` and storing binary data as `Artifacts`.

In the next modules, we will build upon these concepts to explore persistent memory solutions that work in production environments, such as `VertexAiMemoryBankService`.
