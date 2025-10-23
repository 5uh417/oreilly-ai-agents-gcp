from google.adk.agents import LlmAgent, LoopAgent, SequentialAgent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the critic agent that evaluates work
critic_agent_in_loop = LlmAgent(
    name="QualityCritic",
    model="gemini-2.0-flash",
    description="Evaluates content quality and provides improvement suggestions.",
    instruction="""You are a quality critic. Evaluate the current work: '{current_output}'

    Assess:
    - Clarity and coherence
    - Completeness and accuracy
    - Areas for improvement

    If the work meets high standards, respond with "APPROVED: [brief praise]"
    If it needs improvement, provide specific, actionable feedback.""",
    output_key="critique_feedback"
)

# Define the refiner agent that improves work based on critique
refiner_agent_in_loop = LlmAgent(
    name="ContentRefiner",
    model="gemini-2.0-flash",
    description="Refines and improves content based on critique feedback.",
    instruction="""You are a content refiner. Take the previous work: '{current_output}'
    and the critique: '{critique_feedback}' to create an improved version.

    If the critique says "APPROVED", keep the content as-is.
    Otherwise, address all the feedback points and enhance the quality.""",
    output_key="current_output"
)

# Create an initial content creator for the loop
initial_writer = LlmAgent(
    name="InitialWriter",
    model="gemini-2.0-flash",
    description="Creates initial content for the refinement loop.",
    instruction="""You are a content creator. Write initial content based on the user's request.
    This will be the starting point for an iterative refinement process.""",
    output_key="current_output"
)

# Create the refinement loop
refinement_loop = LoopAgent(
    name="RefinementLoop",
    # Agent order is crucial: Critique first, then Refine/Exit
    sub_agents=[critic_agent_in_loop, refiner_agent_in_loop],
    max_iterations=5,  # Limit loops to prevent infinite execution
    description="Iteratively refines content until it meets quality standards."
)

# Create the root agent that combines initial writing with refinement
root_agent = SequentialAgent(
    name="ContentRefinementSystem",
    description="Creates initial content and then refines it iteratively.",
    sub_agents=[initial_writer, refinement_loop]
)
