from google.adk.agents import LlmAgent, SequentialAgent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define individual specialist agents
code_writer_agent = LlmAgent(
    name="CodeWriter",
    model="gemini-2.0-flash",
    description="Writes initial code based on requirements.",
    instruction="""You are an expert software developer. When given requirements,
    write clean, well-structured code. Focus on functionality and clarity.
    Always include basic error handling and comments.""",
    output_key="initial_code"
)

code_reviewer_agent = LlmAgent(
    name="CodeReviewer",
    model="gemini-2.0-flash",
    description="Reviews code for quality, bugs, and best practices.",
    instruction="""You are a senior code reviewer. Review the following code: '{initial_code}'

    Check for:
    - Code quality and readability
    - Potential bugs or issues
    - Adherence to best practices
    - Security considerations

    Provide specific feedback and suggestions for improvement.""",
    output_key="review_feedback"
)

code_refactorer_agent = LlmAgent(
    name="CodeRefactorer",
    model="gemini-2.0-flash",
    description="Refactors code based on review feedback.",
    instruction="""You are a refactoring expert. Take the original code: '{initial_code}'
    and the review feedback: '{review_feedback}' to produce improved code.

    Apply the suggested improvements while maintaining functionality.
    Make the code more maintainable, efficient, and robust.""",
    output_key="refactored_code"
)

# Create the sequential pipeline
root_agent = SequentialAgent(
    name="CodePipelineAgent",
    sub_agents=[code_writer_agent, code_reviewer_agent, code_refactorer_agent],
    description="Executes a sequence of code writing, reviewing, and refactoring.",
    # The agents will run in the order provided: Writer -> Reviewer -> Refactorer
)
