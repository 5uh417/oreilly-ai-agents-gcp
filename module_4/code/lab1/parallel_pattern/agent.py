from dotenv import load_dotenv
from google.adk.agents import LlmAgent, ParallelAgent
from google.adk.tools import google_search

# Load environment variables
load_dotenv()

# Define parallel research agents
researcher_agent_1 = LlmAgent(
    name="TechResearcher",
    model="gemini-2.0-flash",
    description="Researches technology trends and innovations.",
    instruction="""You are a technology research specialist. When given a topic,
    research the latest technological developments, innovations, and trends.
    Focus on cutting-edge technologies and their implications.""",
    tools=[google_search],
    output_key="tech_research"
)

researcher_agent_2 = LlmAgent(
    name="MarketResearcher",
    model="gemini-2.0-flash",
    description="Researches market trends and business implications.",
    instruction="""You are a market research analyst. When given a topic,
    research market trends, business opportunities, and economic impacts.
    Focus on market size, growth potential, and competitive landscape.""",
    tools=[google_search],
    output_key="market_research"
)

researcher_agent_3 = LlmAgent(
    name="AcademicResearcher",
    model="gemini-2.0-flash",
    description="Researches academic literature and scientific developments.",
    instruction="""You are an academic researcher. When given a topic,
    research recent academic papers, scientific studies, and scholarly insights.
    Focus on peer-reviewed research and evidence-based findings.""",
    tools=[google_search],
    output_key="academic_research"
)

# Create the parallel research agent
root_agent = ParallelAgent(
    name="ParallelWebResearchAgent",
    sub_agents=[researcher_agent_1, researcher_agent_2, researcher_agent_3],
    description="Runs multiple research agents in parallel to gather comprehensive information.",
    # The agents will run simultaneously and independently
)
