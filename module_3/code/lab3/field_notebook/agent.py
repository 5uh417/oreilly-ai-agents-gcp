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
