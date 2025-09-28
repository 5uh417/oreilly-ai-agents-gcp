# Building a Multimodal Agent: Handling Images, Audio, and Files

In the previous labs, you gave an agent memory and learned to manage its state. Now, you'll unlock its senses. This lab dives into the exciting world of multimodality, where agents can process more than just text.

You will build a "Digital Field Notebook" agent. This agent will be able to:

1.  **Natively understand images**: You'll see how Gemini can "see" and describe a picture you upload without any special tools.
2.  **Store any file**: You'll build a tool that can take any uploaded file—an audio memo, a video clip, a PDF—and save it as an artifact.
3.  **List all saved files**: You'll create a tool to see a catalog of all the artifacts you've stored in your session.

This lab showcases the elegant interplay between the Gemini model's built-in vision capabilities and the ADK's flexible artifact management system.

## What you'll learn

- How to interact with the file upload feature in the `adk web` interface.
- How an `LlmAgent` can process images and text in a single prompt (native multimodality).
- How to write a generic tool to save any uploaded file as a named artifact using `ToolContext`.
- How to write a tool to list all currently stored artifacts in the session.
- The crucial difference between files Gemini understands directly (images) and files ADK stores as opaque data (audio, PDFs, etc.).

## Prerequisites & Setup

Please ensure you have completed the previous labs and are comfortable with the basics of ADK tools and `adk web`. You will also need a few sample files on your computer to upload: an image file (`.jpg` or `.png`) and any other file type, such as an audio file (`.mp3`, `.wav`) or even just a simple text file (`.txt`).

#### **Project Setup**

1.  Create a new directory named `field_notebook`.
2.  Inside `field_notebook`, create an `__init__.py` file with `from . import agent`.
3.  Copy the .env file from lab 1 of module 1.
4.  Inside `field_notebook`, create a file named `agent.py`.
5.  Copy the following starter code into `agent.py`. It contains the agent's core definition and instructions.

```python
# field_notebook/agent.py (Starter Code)

from google.adk.agents import LlmAgent, Agent
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
import google.genai.types as types
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# We will implement the tool functions here.

# --- Agent Definition ---
root_agent: Agent = LlmAgent(
    model="gemini-2.5-flash",
    name="FieldNotebookAgent",
    instruction="""You are a digital field notebook assistant.

    - If the user provides an image, describe what you see in the image.
    - Use the 'save_file_as_artifact' tool to store any provided files with a given filename.
    - Use the 'list_saved_files' tool to show the user all the files they have stored.
    - If the user wants to save a file but doesn't provide a filename, you MUST ask them for one.
    """,
    tools=[], # We will add our tools here
)
```

## Listing Stored Artifacts

First, let's build the simplest tool: one that shows us what's already been saved. This tool will use `tool_context.list_artifacts()` to get a list of all artifact filenames stored in the current session.

#### **1. Implement the `list_saved_files` Tool**

Add the following function to `agent.py` above the agent definition.

```python
# field_notebook/agent.py

# ... (imports) ...

async def list_saved_files(tool_context: ToolContext) -> str:
    """Lists the filenames of all artifacts saved in the current session."""
    print("Executing tool: list_saved_files")
    try:
        # The context object gives us direct access to the artifact service.
        artifact_filenames = await tool_context.list_artifacts()

        if not artifact_filenames:
            return "There are no files saved in your notebook yet."

        return "Here are your saved files:\n- " + "\n- ".join(artifact_filenames)
    except ValueError as e:
        print(f"🔴 Error listing artifacts: {e}. Is an ArtifactService configured?")
        return "Error: Could not list artifacts. The system may not be configured correctly."

# ... (Agent Definition) ...
```

#### **2. Add the Tool to the Agent**

Now, register this new tool with your agent.

```python
# field_notebook/agent.py

# ...

root_agent: Agent = LlmAgent(
    # ... (model, name, instruction) ...
    tools=[
        FunctionTool(func=list_saved_files),
    ],
)
```

## Saving Any File as an Artifact

This is the core of our lab. We'll create a single, powerful tool that can take _any_ file uploaded by the user and save it.

When a user uploads a file along with a text prompt, the ADK packages it all into a `Content` object. This object contains a list of `Part`s. Our tool will inspect this request, find the file `Part`, and save it using `tool_context.save_artifact()`.

#### **1. Implement the `save_file_as_artifact` Tool**

Add this function to `agent.py`. It's designed to be generic. It doesn't care if the file is an audio clip, a video, or a spreadsheet; it simply saves the binary data it receives.

```python
# field_notebook/agent.py

# ...

async def save_file_as_artifact(filename: str, tool_context: ToolContext) -> str:
    """Saves a file provided by the user as a named artifact."""
    print(f"Executing tool: save_file_as_artifact with filename '{filename}'")

    # Get the original user content from the context
    user_content = tool_context.user_content

    file_part_to_save = None
    # Find the first part in the content that is a file (not text)
    for part in user_content.parts:
        if part.text is None and part.inline_data is not None:
            file_part_to_save = part
            break # Save the first file found

    if file_part_to_save is None:
        return "Error: You asked me to save a file, but I couldn't find a file in your message."

    try:
        version = await tool_context.save_artifact(
            filename=filename, artifact=file_part_to_save
        )
        print(f"✅ File '{filename}' saved as version {version}.")
        return f"Successfully saved '{filename}' to your notebook."
    except ValueError as e:
        print(f"🔴 Error saving artifact: {e}. Is an ArtifactService configured?")
        return "Error: Could not save the file. The system may not be configured correctly."

# ...
```

#### **2. Add the Tool to the Agent**

Update the agent's tool list again.

```python
# field_notebook/agent.py

# ...

root_agent: Agent = LlmAgent(
    # ... (model, name, instruction) ...
    tools=[
        FunctionTool(func=list_saved_files),
        FunctionTool(func=save_file_as_artifact), # <-- ADD THIS
    ],
)
```

## Gemini's Native Vision: No Tool Required

This is the most fascinating part. How do we get the agent to _describe_ an image? **We don't need to write a tool for it.**

The Gemini family of models is natively multimodal. When the `LlmAgent` receives a prompt containing both text and an image, it sends both directly to the model. The model can "see" the image and reason about it in the context of the text.

Our agent's instruction, _"If the user provides an image, describe what you see in the image,"_ is all that's needed to unlock this capability. The ADK framework handles the rest.

## Run and Observe

Let's put it all together and interact with our multimodal agent.

#### **Final `agent.py` Code**

Here is the complete, final code for your `field_notebook/agent.py`.

```python
# field_notebook/agent.py (Final Code)

from google.adk.agents import LlmAgent, Agent
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
import google.genai.types as types

async def list_saved_files(tool_context: ToolContext) -> str:
    """Lists the filenames of all artifacts saved in the current session."""
    print("Executing tool: list_saved_files")
    try:
        artifact_filenames = await tool_context.list_artifacts()
        if not artifact_filenames:
            return "There are no files saved in your notebook yet."
        return "Here are your saved files:\n- " + "\n- ".join(artifact_filenames)
    except ValueError as e:
        print(f"🔴 Error listing artifacts: {e}. Is an ArtifactService configured?")
        return "Error: Could not list artifacts. The system may not be configured correctly."

async def save_file_as_artifact(filename: str, tool_context: ToolContext) -> str:
    """Saves a file provided by the user as a named artifact."""
    print(f"Executing tool: save_file_as_artifact with filename '{filename}'")
    user_content = tool_context.user_content
    file_part_to_save = None
    for part in user_content.parts:
        if part.text is None and part.inline_data is not None:
            file_part_to_save = part
            break
    if file_part_to_save is None:
        return "Error: You asked me to save a file, but I couldn't find a file in your message."
    try:
        version = await tool_context.save_artifact(filename=filename, artifact=file_part_to_save)
        print(f"✅ File '{filename}' saved as version {version}.")
        return f"Successfully saved '{filename}' to your notebook."
    except ValueError as e:
        print(f"🔴 Error saving artifact: {e}. Is an ArtifactService configured?")
        return "Error: Could not save the file. The system may not be configured correctly."

# --- Agent Definition ---
root_agent: Agent = LlmAgent(
    model="gemini-2.5-flash",
    name="FieldNotebookAgent",
    instruction="""You are a digital field notebook assistant.

    - If the user provides an image, describe what you see in the image.
    - Use the 'save_file_as_artifact' tool to store any provided files with a given filename.
    - Use the 'list_saved_files' tool to show the user all the files they have stored.
    - If the user wants to save a file but doesn't provide a filename, you MUST ask them for one.
    """,
    tools=[
        FunctionTool(func=list_saved_files),
        FunctionTool(func=save_file_as_artifact),
    ],
)
```

#### **Execute the Agent**

1.  In your terminal, navigate to the directory that contains your `field_notebook` folder.
2.  Run the `adk web` command.

```console
adk web
```

3.  Open your web browser to `http://127.0.0.1:8080`.

#### **Sample Interaction**

Follow these steps in the web UI.

1.  **Test Native Vision:**

    - Click the paperclip icon and upload an **image** from your computer.
    - In the text box, type: `What is this a picture of?`
    - Press Send.
    - **Observe:** The agent will describe the image directly. No tool is called! This is Gemini's native vision at work.

2.  **Test Saving an Artifact:**

    - Click the paperclip icon and upload a different file type, like an **audio file (`.mp3`)** or a simple **text file (`.txt`)**.
    - In the text box, type: `Please save this file as "audio_memo.mp3"` (or `"note.txt"`).
    - Press Send.
    - **Observe:** The agent will confirm that it has saved the file. Check your terminal—you will see the log from your `save_file_as_artifact` tool.

3.  **Test Listing Artifacts:**
    - In the text box, type: `list my saved files`
    - Press Send.
    - **Observe:** The agent will respond with a list that includes `"audio_memo.mp3"`. Check your terminal to see the log from `list_saved_files`.

Your interaction should look something like this:

> **You:** (uploads image of a cat) `What is this a picture of?`
>
> **Agent:** This is a picture of a tabby cat sitting on a windowsill, looking outside.
>
> **You:** (uploads an audio file) `Please save this file as "field_report_May_10.wav"`
>
> **Agent:** Successfully saved 'field_report_May_10.wav' to your notebook.
>
> **You:** `what files do i have?`
>
> **Agent:** Here are your saved files:
>
> - field_report_May_10.wav

## Tying It All Together: A Recap

Congratulations! You've built a truly multimodal agent. Let's recap the key principles you've just put into practice:

1.  **Native Multimodality:** For common media types like images, the `LlmAgent` and Gemini model handle analysis automatically. You don't need to write custom tools for simple description or recognition tasks. Your prompt is the key to unlocking this power.

2.  **Generic Artifacts:** For all other file types, or when you simply need to store a file without analyzing it, the ADK's `ArtifactService` is the perfect tool. Your `save_file_as_artifact` function works for any file because it treats everything as a binary blob, identified by a filename.

3.  **Context is the Bridge:** The `ToolContext` object was the critical link. It gave your Python tool code (`save_file_as_artifact`) access to the raw file data uploaded by the user (`tool_context.user_content`) and the mechanism to store it (`tool_context.save_artifact()`).

You are now equipped with the core patterns for building sophisticated agents that can interact with users and their data in rich, new ways.
