from google.adk.agents import SequentialAgent, LlmAgent
from google.adk.tools.tool_context import ToolContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Step 1: Define the Agents

# The author agent - writes first draft
author = LlmAgent(
    name="ManuscriptWriter",
    model="gemini-2.0-flash",
    description="Creates initial content drafts for review.",
    instruction="""You are a creative author. Write engaging, well-structured content
    based on the given requirements. Focus on clarity, creativity, and audience engagement.
    Your draft will be reviewed by human editors.""",
    output_key="draft_chapter"  # Saves output to session state
)

# The revision agent - improves based on human feedback
reviser = LlmAgent(
    name="ManuscriptReviser",
    model="gemini-2.0-flash",
    description="Revises content based on human feedback.",
    instruction="""You are a meticulous editor. Revise the following draft: '{draft_chapter}'
    based on this feedback: '{review_feedback}'

    Apply all suggested improvements while maintaining the original intent and voice.
    Make the content more engaging, accurate, and polished.""",
    output_key="revised_chapter"  # Saves final version to state
)

# Step 2: Define the Human-in-the-Loop Tool

def request_human_review(draft: str, tool_context: ToolContext) -> str:
    """
    Pauses the workflow and requests human editor review.
    In production, this would integrate with approval systems or APIs.

    Args:
        draft: The content draft to be reviewed
        tool_context: ADK tool context for state management

    Returns:
        Human feedback as a string
    """
    print("\n" + "="*50)
    print("🔄 HUMAN REVIEW REQUIRED")
    print("="*50)
    print(f"📄 Draft to review:\n{draft[:300]}...")
    print("\n" + "-"*50)

    # In production, this would:
    # 1. Save the state to a database
    # 2. Send notification to human reviewer
    # 3. Wait for API callback with feedback
    # 4. Resume the workflow

    feedback = input("\n✏️  Please provide your editorial feedback: ")

    print("✅ Review completed. Continuing workflow...\n")
    return feedback

# Step 3: Create Review Management Agent

# This agent manages the human review process
reviewer = LlmAgent(
    name="EditorialReviewer",
    model="gemini-2.0-flash",
    description="Manages human review process for content quality assurance.",
    instruction="""You are a project manager coordinating the editorial review process.

    Use the request_human_review tool to get feedback on the draft: '{draft_chapter}'

    Facilitate the review process and ensure feedback is collected properly.""",
    tools=[request_human_review],
    output_key="review_feedback"  # Saves human feedback to state
)

# Step 4: Assemble the Complete Workflow

root_agent = SequentialAgent(
    name="BookPublishingFlow",
    description="Complete content creation workflow with human oversight.",
    sub_agents=[
        author,      # 1. AI writes initial draft
        reviewer,    # 2. Human reviews and provides feedback
        reviser      # 3. AI revises based on human feedback
    ]
)
