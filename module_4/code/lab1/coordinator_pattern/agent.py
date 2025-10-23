from google.adk.agents import LlmAgent
from google.adk.tools.tool_context import ToolContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define specialist agents
billing_agent = LlmAgent(
    name="billing_agent",
    model="gemini-2.0-flash",
    description="Handles billing inquiries and payment issues.",
    instruction="""You are a billing specialist. Help customers with:
    - Payment processing issues
    - Invoice questions
    - Billing disputes
    - Account balance inquiries
    - Subscription management

    Be helpful and provide clear solutions."""
)

support_agent = LlmAgent(
    name="support_agent",
    model="gemini-2.0-flash",
    description="Handles technical support requests.",
    instruction="""You are a technical support specialist. Help customers with:
    - Software troubleshooting
    - Configuration issues
    - Performance problems
    - Feature questions
    - Integration support

    Provide step-by-step solutions and ask clarifying questions when needed."""
)

def check_and_transfer(query: str, tool_context: ToolContext) -> str:
    """Checks if the query requires escalation and transfers to another agent."""
    # Analyze the query for routing signals
    query_lower = query.lower()

    # Check for billing-related keywords
    billing_keywords = ['bill', 'payment', 'invoice', 'charge', 'subscription', 'refund', 'price']
    if any(keyword in query_lower for keyword in billing_keywords):
        print("Tool: Detected billing query, transferring to the billing agent.")
        tool_context.actions.transfer_to_agent = "billing_agent"
        return "Transferring to our billing specialist who can help with payment and account issues..."

    # Check for technical keywords
    tech_keywords = ['error', 'bug', 'install', 'configure', 'troubleshoot', 'performance']
    if any(keyword in query_lower for keyword in tech_keywords):
        print("Tool: Detected technical query, transferring to support agent.")
        tool_context.actions.transfer_to_agent = "support_agent"
        return "Transferring to our technical support team for assistance..."

    return f"I've analyzed your query: '{query}'. Let me help you directly."

# Coordinator agent that routes requests
root_agent = LlmAgent(
    name="HelpDeskCoordinator",
    model="gemini-2.0-flash",
    instruction="""You are a help desk coordinator. Analyze user requests and route them appropriately:

    For payment, billing, or financial issues → use check_and_transfer tool to route to billing
    For technical problems, errors, or configuration → use check_and_transfer tool to route to support
    For general questions → provide direct assistance

    Always be helpful and explain what you're doing.""",
    description="Main help desk router that intelligently directs customer inquiries.",
    tools=[check_and_transfer],
    sub_agents=[billing_agent, support_agent]
)
