# Using Context with your Agent in ADK

In the previous lab, you gave an agent a long-term memory. Now, you'll learn to manage its short-term, "working" memory within a single conversation using **Context** objects. These objects—`ToolContext` and `CallbackContext`—are your direct link to the session's runtime, allowing you to read and write data on the fly.

In this lab, you will build a "Smart Shopping List" agent. This agent will use `ToolContext` within custom tools to add items to a list and view it. Then, it will use `CallbackContext` in a lifecycle callback to save the final list to a file, demonstrating a powerful combination of state and artifact management.

## What you'll learn

- What `ToolContext` and `CallbackContext` are and why they are essential.
- The correct way to **read** session state from within a custom tool (`tool_context.state`).
- The correct way to **write** to session state to track information (`tool_context.state['key'] = value`).
- How to use `CallbackContext` to perform actions after an agent has run.
- How to bridge state and artifacts by saving session data using `context.save_artifact()`.

## Prerequisites & Setup

This lab assumes you have completed the previous "Giving Your AI Agent a Memory" lab and have a working ADK environment.

We will start with a basic agent and build out its capabilities step by step.

#### **Project Setup**

1.  In a new directory, create a folder named `shopping_agent`.
2.  Inside `shopping_agent`, create an empty `__init__.py` file to make it a Python package and type `from . import agent`
3.  Copy the .env file from lab 1 of module 1.
4.  Inside `shopping_agent`, create a file named `agent.py`.
5.  Copy the following starter code into `agent.py`. This defines our agent but with no tools or callbacks yet.

```python
# shopping_agent/agent.py (Starter Code)

from google.adk.agents import LlmAgent, Agent
from google.adk.tools import FunctionTool
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.tool_context import ToolContext
import google.genai.types as types
import json

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# We will define our tool functions here
# def view_shopping_list(...):
#     pass
#
# def add_to_shopping_list(...):
#     pass

# We will define our callback function here
# async def save_list_as_artifact(...):
#     pass


# Agent Definition
root_agent: Agent = LlmAgent(
    model="gemini-2.5-flash",
    name="ShoppingListAgent",
    instruction="""You are a shopping list assistant.
    - Use the 'add_to_shopping_list' tool to add items.
    - Use the 'view_shopping_list' tool to see the current list.
    - Acknowledge when an item has been added.
    - When the user asks to "save the list", respond with "OK, saving your list."
    """,
    # We will add tools and callbacks here
    tools=[],
    # after_agent_callback=...
)
```

> This lab uses the `adk web` command for interactive testing. It provides a simple chat interface in your browser to talk to your agent.

## Reading State with `ToolContext`

Let's give our agent the ability to see what's on the shopping list. We'll create a custom tool that reads a value from the session `state`. The `ToolContext` object, passed automatically to every tool function, is our gateway to this state.

#### **1. Implement the `view_shopping_list` Tool**

In `agent.py`, uncomment and implement the `view_shopping_list` function. This function accesses `tool_context.state` to get the list. The `.get()` method is used to safely retrieve the value, providing an empty list `[]` as a default if the key doesn't exist yet.

```python
# shopping_agent/agent.py

# ... (imports) ...

def view_shopping_list(tool_context: ToolContext) -> str:
    """Displays the items currently on the shopping list."""
    print("Executing tool: view_shopping_list")

    # Read from the state using the context object.
    # Provide a default value `[]` in case the list hasn't been created yet.
    current_list = tool_context.state.get("shopping_list", [])

    if not current_list:
        return "The shopping list is currently empty."

    # Format the list for display to the user.
    return "Here is your shopping list:\n- " + "\n- ".join(current_list)

# ... (rest of the code) ...
```

#### **2. Add the Tool to the Agent**

Now, update the `LlmAgent` definition to include your new tool.

```python
# shopping_agent/agent.py

# ...

root_agent: Agent = LlmAgent(
    # ... (name, model, instruction)
    tools=[
        FunctionTool(func=view_shopping_list),
    ],
    # after_agent_callback=...
)
```

With this in place, the agent can now understand a request like "show me my list," call your Python function, and your function will read the session state to provide the answer.

## Writing State with `ToolContext`

Reading state is useful, but writing to it is what makes an agent truly dynamic. We'll now implement the `add_to_shopping_list` tool.

#### **The Correct Way to Modify State**

> **Critical Concept:** You should **only** modify session state by assigning values to the `state` dictionary on the `Context` object (e.g., `tool_context.state['my_key'] = 'new_value'`). This signals the change to the ADK framework, which then correctly records the update in the conversation history. Never modify a `Session` object directly.

#### **1. Implement the `add_to_shopping_list` Tool**

Uncomment and implement the function in `agent.py`. The logic is simple: read the current list, append the new item, and then write the entire list back to the state.

```python
# shopping_agent/agent.py

# ...

def add_to_shopping_list(item: str, tool_context: ToolContext) -> str:
    """Adds a single item to the shopping list."""
    print(f"Executing tool: add_to_shopping_list with item '{item}'")

    # Read the current list from state
    current_list = tool_context.state.get("shopping_list", [])

    # Modify the list in memory
    if item.lower() not in [i.lower() for i in current_list]:
        current_list.append(item)

    # Write the entire updated list back to the state
    tool_context.state["shopping_list"] = current_list

    return f"'{item}' has been added to the list."

# ...
```

#### **2. Add the New Tool to the Agent**

Update the agent's tool list to include the add function.

```python
# shopping_agent/agent.py

# ...

root_agent: Agent = LlmAgent(
    # ... (name, model, instruction)
    tools=[
        FunctionTool(func=view_shopping_list),
        FunctionTool(func=add_to_shopping_list), # <-- ADD THIS
    ],
    # after_agent_callback=...
)
```

Your agent can now manage a list within a single conversation!

## Saving State as an Artifact with `CallbackContext`

What if the user wants a permanent copy of their list? We can combine our state management with the **Artifacts** concept. We'll use a callback, `after_agent_callback`, to check if the user wants to save their list. Callbacks receive a `CallbackContext`, which also has access to `state` and artifact methods.

#### **1. Implement the `save_list_as_artifact` Callback**

This function will run _after_ the agent generates its final response. It inspects the user's last message and, if it matches our trigger phrase, it retrieves the list from the state and saves it as a text file artifact.

```python
# shopping_agent/agent.py

# ...

async def save_list_as_artifact(callback_context: CallbackContext):
    """After the agent runs, check if the user asked to save the list."""
    user_last_message = callback_context.user_content.parts[0].text

    if "save the list" in user_last_message.lower():
        print("Callback triggered: save_list_as_artifact")
        shopping_list = callback_context.state.get("shopping_list", [])

        if not shopping_list:
            print("List is empty, not saving artifact.")
            return

        # Prepare the artifact content
        file_content = "My Shopping List:\n\n- " + "\n- ".join(shopping_list)
        artifact_part = types.Part(text=file_content)

        # Use the context to save the artifact
        try:
            version = await callback_context.save_artifact(
                filename="shopping_list.txt",
                artifact=artifact_part
            )
            print(f"✅ Successfully saved shopping_list.txt as version {version}")
        except ValueError as e:
            print(f"🔴 Error saving artifact: {e}. Is an ArtifactService configured in your runner?")

# ...
```

#### **2. Add the Callback to the Agent**

Finally, hook this function into the agent's lifecycle.

```python
# shopping_agent/agent.py

# ...

root_agent: Agent = LlmAgent(
    # ... (name, model, instruction, tools)
    after_agent_callback=save_list_as_artifact, # <-- ADD THIS
)
```

## Run and Observe

Everything is now in place. We just need to run our agent using `adk web`.

#### **Final `agent.py` Code**

Here is the complete code for `shopping_agent/agent.py`.

```python
# shopping_agent/agent.py (Final Code)

from google.adk.agents import LlmAgent, Agent
from google.adk.tools import FunctionTool
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.tool_context import ToolContext
import google.genai.types as types
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def view_shopping_list(tool_context: ToolContext) -> str:
    """Displays the items currently on the shopping list."""
    print("Executing tool: view_shopping_list")
    current_list = tool_context.state.get("shopping_list", [])
    if not current_list:
        return "The shopping list is currently empty."
    return "Here is your shopping list:\n- " + "\n- ".join(current_list)

def add_to_shopping_list(item: str, tool_context: ToolContext) -> str:
    """Adds a single item to the shopping list."""
    print(f"Executing tool: add_to_shopping_list with item '{item}'")
    current_list = tool_context.state.get("shopping_list", [])
    if item.lower() not in [i.lower() for i in current_list]:
        current_list.append(item)
    tool_context.state["shopping_list"] = current_list
    return f"'{item}' has been added to the list."

async def save_list_as_artifact(callback_context: CallbackContext):
    """After the agent runs, check if the user asked to save the list."""
    user_last_message = callback_context.user_content.parts[0].text
    if "save the list" in user_last_message.lower():
        print("Callback triggered: save_list_as_artifact")
        shopping_list = callback_context.state.get("shopping_list", [])
        if not shopping_list:
            print("List is empty, not saving artifact.")
            return
        file_content = "My Shopping List:\n\n- " + "\n- ".join(shopping_list)
        artifact_part = types.Part(text=file_content)
        try:
            version = await callback_context.save_artifact(
                filename="shopping_list.txt",
                artifact=artifact_part
            )
            print(f"✅ Successfully saved shopping_list.txt as version {version}")
        except ValueError as e:
            print(f"🔴 Error saving artifact: {e}. Is an ArtifactService configured in your runner?")

# Agent Definition
root_agent: Agent = LlmAgent(
    model="gemini-2.5-flash",
    name="ShoppingListAgent",
    instruction="""You are a shopping list assistant.
    - Use the 'add_to_shopping_list' tool to add items.
    - Use the 'view_shopping_list' tool to see the current list.
    - Acknowledge when an item has been added.
    - When the user asks to "save the list", respond with "OK, saving your list."
    """,
    tools=[
        FunctionTool(func=view_shopping_list),
        FunctionTool(func=add_to_shopping_list),
    ],
    after_agent_callback=save_list_as_artifact,
)
```

#### **Execute the Agent**

1.  From your terminal, navigate to the directory that _contains_ your `shopping_agent` folder.
2.  Run the `adk web` command.

```console
adk web
```

3.  Open your web browser to `http://127.0.0.1:8080`.

#### **Sample Interaction**

Talk to your agent in the web UI. Try the following conversation:

> **You:** add milk to my list
>
> **Agent:** 'milk' has been added to the list.
>
> **You:** add bread and eggs
>
> **Agent:** 'bread' has been added to the list. 'eggs' has been added to the list.
>
> **You:** show me my list
>
> **Agent:** Here is your shopping list:
>
> - milk
> - bread
> - eggs
>
> **You:** ok please save the list now
>
> **Agent:** OK, saving your list.

Now, check your terminal where you ran `adk web`. You should see the log messages from your tools and, most importantly, the confirmation that the artifact was saved!

```console
Executing tool: add_to_shopping_list with item 'milk'
Executing tool: add_to_shopping_list with item 'bread'
Executing tool: add_to_shopping_list with item 'eggs'
Executing tool: view_shopping_list
Callback triggered: save_list_as_artifact
✅ Successfully saved shopping_list.txt as version 0
```

## Congratulations!

You've just mastered one of the most powerful and essential concepts in ADK for building complex, interactive agents.

You now know how to use `ToolContext` and `CallbackContext` to read and write session state, enabling your agent to track information dynamically. You've also built a bridge between runtime state and persistent data by using a callback to save your session data as an artifact. This pattern of using tools to modify state and callbacks to perform final actions is a cornerstone of advanced agent design.
