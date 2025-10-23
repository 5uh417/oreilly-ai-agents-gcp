from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Level 4: Technical Experts (Lowest level)
circuit_designer = LlmAgent(
    name="CircuitDesigner",
    model="gemini-2.0-flash",
    description="Designs electrical circuits for construction projects.",
    instruction="""You are a circuit design expert. Create detailed electrical circuit plans
    including load calculations, safety considerations, and code compliance.""",
    output_key="circuit_design"
)

wiring_sizer = LlmAgent(
    name="WiringSizer",
    model="gemini-2.0-flash",
    description="Calculates appropriate wire sizes and specifications.",
    instruction="""You are a wiring specification expert. Based on the circuit design: '{circuit_design}'
    calculate appropriate wire gauges, conduit sizes, and material specifications.""",
    output_key="wiring_specs"
)

safety_inspector = LlmAgent(
    name="SafetyInspector",
    model="gemini-2.0-flash",
    description="Reviews electrical plans for safety and code compliance.",
    instruction="""You are a safety inspector. Review the circuit design: '{circuit_design}'
    and wiring specs: '{wiring_specs}' for safety compliance and building code adherence.""",
    output_key="safety_review"
)

# Level 3: Component Specialists (Sequential team)
wiring_specialist = SequentialAgent(
    name="WiringTeam",
    description="Handles all electrical wiring design and specification.",
    sub_agents=[circuit_designer, wiring_sizer, safety_inspector]
)

# Level 2: System Directors
electrical_director = LlmAgent(
    name="ElectricalDirector",
    model="gemini-2.0-flash",
    description="Coordinates electrical systems installation and planning.",
    instruction="""You are the electrical systems director. Coordinate electrical work
    including power distribution, lighting, and safety systems. Delegate technical
    details to your wiring team and ensure overall project integration.""",
    sub_agents=[wiring_specialist]
)

# Additional directors would be defined here (plumbing, HVAC, etc.)
plumbing_director = LlmAgent(
    name="PlumbingDirector",
    model="gemini-2.0-flash",
    description="Coordinates plumbing systems installation.",
    instruction="You are the plumbing systems director. Handle water supply, drainage, and fixtures."
)

# Level 1: Project Manager (Highest level)
root_agent = LlmAgent(
    name="ProjectManager",
    model="gemini-2.0-flash",
    description="Oversees entire construction project and delegates to system directors.",
    instruction="""You are the project manager for a construction project.

    Coordinate between different system directors:
    - Electrical systems (electrical_director)
    - Plumbing systems (plumbing_director)

    Ensure all systems work together and meet project requirements.
    Delegate technical work to appropriate directors.""",
    sub_agents=[electrical_director, plumbing_director]
)
