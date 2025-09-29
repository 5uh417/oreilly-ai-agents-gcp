# Lab #1: Building Multi-Agent Systems with ADK Design Patterns

Welcome to Module 4 of the AI Agents with Google's Agent Development Kit (ADK) Bootcamp! You've learned to build individual agents with tools and integrations. Now, you'll discover the power of multi-agent systems—orchestrating multiple specialized agents to solve complex problems that require coordination, parallel processing, and sophisticated workflows.

Multi-agent systems represent the next evolution in AI applications. Instead of building one monolithic agent that tries to do everything, you'll learn to create teams of focused agents that collaborate, each bringing their own expertise to the table. This modular approach leads to more reliable, maintainable, and scalable AI solutions.

### **What You'll Learn**

- How to implement Sequential Agent patterns for step-by-step workflows.
- How to use Parallel Agent patterns for concurrent processing and research.
- How to create Loop Agent patterns for iterative refinement and reflection.
- How to build Coordinator-Dispatcher patterns for intelligent routing and delegation.
- How to design Hierarchical Task Decomposition for complex organizational structures.
- How to integrate Human-in-the-Loop patterns for quality control and oversight.
- Best practices for multi-agent coordination and state management.

### **What You'll Need**

- A computer with Python 3.10 or higher installed.
- A code editor like Visual Studio Code.
- Access to a command line/terminal.
- Completion of previous ADK labs (understanding of agents, tools, and basic patterns).
- A Google account with access to Google AI Studio or Vertex AI.

Let's dive into the world of collaborative AI agents.

## 1. Set Up Your Multi-Agent Laboratory

Let's create a comprehensive environment for experimenting with different multi-agent patterns.

1. Open your terminal and create a new directory for this lab:

    ```console
    mkdir adk-multiagent-lab
    cd adk-multiagent-lab
    ```

2. Create and activate a Python virtual environment:

    ```console
    python3 -m venv .venv
    source .venv/bin/activate
    # On Windows: .venv\Scripts\activate
    ```

3. Install the required dependencies:

    ```console
    pip install google-adk
    ```

4. Create a structured project layout for different patterns:

    ```console
    mkdir sequential_pattern
    mkdir parallel_pattern
    mkdir loop_pattern
    mkdir coordinator_pattern
    mkdir hierarchical_pattern
    mkdir human_loop_pattern
    touch sequential_pattern/__init__.py
    touch parallel_pattern/__init__.py
    touch loop_pattern/__init__.py
    touch coordinator_pattern/__init__.py
    touch hierarchical_pattern/__init__.py
    touch human_loop_pattern/__init__.py
    touch .env
    ```

5. Add the required import to each `__init__.py` file:

    ```python
    # For each pattern directory: pattern_name/__init__.py
    from . import agent
    ```

6. Set up your environment variables in `.env`:

    ```
    GOOGLE_GENAI_USE_VERTEXAI=0
    GOOGLE_API_KEY=your-google-ai-studio-api-key-here
    ```

## 2. Understanding Multi-Agent Architecture Patterns

Before we implement specific patterns, let's understand the fundamental concepts that make multi-agent systems powerful:

### **Key Concepts**

- **Agent Specialization**: Each agent has a focused role and expertise
- **Coordination**: Agents work together toward common goals
- **Communication**: Agents share information and results
- **State Management**: Maintaining context across agent interactions
- **Flow Control**: Determining execution order and conditions

### **When to Use Multi-Agent Patterns**

- **Complex Workflows**: Breaking down large tasks into manageable steps
- **Parallel Processing**: Handling multiple independent tasks simultaneously
- **Quality Assurance**: Having agents review and refine each other's work
- **Domain Expertise**: Routing requests to specialized knowledge agents
- **Scalability**: Distributing workload across multiple processing units

## 3. Pattern 1: Sequential Agent for Step-by-Step Workflows

Sequential agents execute tasks in a specific order, with each agent building upon the previous agent's output. This pattern is perfect for workflows like code development pipelines.

### **Create the Sequential Pattern**

Create `sequential_pattern/agent.py` with the following code:

```python
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
```

### **Understanding Sequential Flow**

In this pattern:
1. **Code Writer** creates initial code and saves it to `state['initial_code']`
2. **Code Reviewer** reads the initial code and provides feedback in `state['review_feedback']`
3. **Code Refactorer** reads both the code and feedback to produce the final result

The `output_key` parameter ensures each agent's output is saved to session state and available to subsequent agents through template variables like `{initial_code}`.

## 4. Pattern 2: Parallel Agent for Concurrent Processing

Parallel agents execute multiple tasks simultaneously, perfect for research, data gathering, or any scenario where independent tasks can be processed concurrently.

### **Create the Parallel Pattern**

Create `parallel_pattern/agent.py` with the following code:

```python
from google.adk.agents import LlmAgent, ParallelAgent
from google.adk.tools import google_search
from dotenv import load_dotenv

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
```

### **Understanding Parallel Execution**

In this pattern:
- All three research agents execute **simultaneously**
- Each agent focuses on a different research angle
- Results are collected from all agents: `tech_research`, `market_research`, `academic_research`
- Total execution time is determined by the slowest agent, not the sum of all agents

## 5. Pattern 3: Loop Agent for Iterative Refinement

Loop agents implement iterative workflows where agents repeatedly refine their work based on feedback. This pattern is excellent for quality improvement and reflection.

### **Create the Loop Pattern**

Create `loop_pattern/agent.py` with the following code:

```python
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
```

### **Understanding Loop Dynamics**

The loop pattern creates a **feedback cycle**:
1. **Critic** evaluates the current output and provides feedback
2. **Refiner** improves the content based on feedback
3. Loop continues until quality standards are met or max iterations reached
4. The `max_iterations` parameter prevents infinite loops

### **How Loop Termination Works**

The LoopAgent stops execution when **either** condition is met:

1. **Max Iterations Reached**: The `max_iterations` limit is hit (5 iterations in this example)
2. **Agent Escalation**: Any sub-agent sets `tool_context.actions.escalate = True` in a tool function

**💡 Pro Tip**: To implement content-based termination, you can modify the critic agent to use a tool that sets `tool_context.actions.escalate = True` when content meets quality standards. This allows for intelligent early termination rather than always running the maximum iterations.

**Note**: Reflection is a loop pattern executed just once (`max_iterations=1`).

## 6. Pattern 4: Coordinator-Dispatcher for Intelligent Routing

This pattern implements a smart routing system where a coordinator agent analyzes requests and dispatches them to appropriate specialist agents.

### **Create the Coordinator Pattern**

Create `coordinator_pattern/agent.py` with the following code:

```python
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
```

### **Understanding Coordinator Architecture**

This pattern implements **intelligent routing**:
- **Coordinator** analyzes incoming requests
- **Transfer Tool** determines appropriate specialist
- **Specialist Agents** handle domain-specific requests
- The `transfer_to_agent` mechanism seamlessly hands off conversations

## 7. Pattern 5: Hierarchical Task Decomposition

This pattern creates multi-level organizational structures where higher-level agents delegate to specialized teams, which in turn coordinate their own sub-agents.

### **Create the Hierarchical Pattern**

Create `hierarchical_pattern/agent.py` with the following code:

```python
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
```

### **Understanding Hierarchical Structure**

This pattern creates a **multi-level organization**:
- **Level 1**: Project Manager (strategic oversight)
- **Level 2**: System Directors (domain coordination)
- **Level 3**: Specialist Teams (tactical execution)
- **Level 4**: Technical Experts (implementation details)

Each level has appropriate scope and delegates details to subordinates.

## 8. Pattern 6: Human-in-the-Loop for Quality Control

This pattern integrates human decision-making and oversight into automated workflows, perfect for content creation, approval processes, and quality assurance.

### **Create the Human-in-the-Loop Pattern**

Create `human_loop_pattern/agent.py` with the following code:

```python
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
```

### **Understanding Human Integration**

This pattern demonstrates **human-AI collaboration**:
1. **AI Agent** creates initial content
2. **Human Review** provides expert feedback and quality control
3. **AI Revision** applies human insights for improvement

In production systems, the human review would integrate with:
- Approval workflow systems
- Slack/Teams notifications
- Web-based review interfaces
- Quality assurance processes

## 9. Testing Your Multi-Agent Patterns

### **Run Individual Patterns**

To test each pattern, you'll run `adk web` from the main directory and then select the specific pattern agent in the web interface:

```console
# From the main adk-multiagent-lab directory
adk web
```

Then in your browser at `http://127.0.0.1:8080`, you'll see a dropdown to select between:
- `sequential_pattern.CodePipelineAgent`
- `parallel_pattern.ParallelWebResearchAgent`
- `loop_pattern.ContentRefinementSystem`
- `coordinator_pattern.HelpDeskCoordinator`
- `hierarchical_pattern.ProjectManager`
- `human_loop_pattern.BookPublishingFlow`

### **Example Prompts for Each Pattern**

**Sequential Agent**:
- `"Create a Python function to calculate the factorial of a number"`

**Parallel Agent**:
- `"Research artificial intelligence trends"`

**Loop Agent**:
- `"Write a brief explanation of quantum computing"`

**Coordinator Agent**:
- `"I'm having trouble with my monthly billing statement"`
- `"The software keeps crashing when I try to upload files"`

**Hierarchical Agent**:
- `"Plan the electrical systems for a new office building"`

**Human-in-the-Loop Agent**:
- `"Write the opening chapter of a science fiction novel about space exploration"`

## 10. Best Practices for Multi-Agent Systems

### **Design Principles**

- **Single Responsibility**: Each agent should have one clear purpose
- **Clear Communication**: Use descriptive `output_key` values for state sharing
- **Error Handling**: Include fallback mechanisms for agent failures
- **Resource Management**: Consider computational costs of parallel operations

### **State Management**

- **Consistent Naming**: Use descriptive state keys like `circuit_design` not `output1`
- **State Flow**: Design clear data flow between agents
- **State Cleanup**: Consider when to clear intermediate state

### **Performance Optimization**

- **Parallel Where Possible**: Use parallel agents for independent tasks
- **Sequential Where Necessary**: Use sequential agents for dependent tasks
- **Timeout Management**: Set appropriate timeouts for long-running agents
- **Resource Pooling**: Share expensive resources (like search tools) across agents

## 11. Congratulations!

You've successfully mastered the fundamental multi-agent patterns in ADK!

In this lab, you learned to:

✅ **Design Sequential Workflows** for step-by-step processing

✅ **Implement Parallel Processing** for concurrent task execution

✅ **Create Iterative Loops** for refinement and quality improvement

✅ **Build Routing Systems** for intelligent request dispatch

✅ **Structure Hierarchical Organizations** for complex coordination

✅ **Integrate Human Oversight** for quality control and decision-making

### **Key Takeaways**

- **Pattern Selection**: Choose the right pattern based on your workflow requirements
- **Agent Specialization**: Design focused agents with clear responsibilities
- **State Coordination**: Manage information flow between agents effectively
- **Human Integration**: Blend AI automation with human expertise strategically

### **What's Next?**

Now that you understand multi-agent patterns, you're ready to explore:
- **Advanced Orchestration**: Complex workflow engines and state machines
- **Error Recovery**: Building resilient multi-agent systems
- **Performance Optimization**: Scaling multi-agent systems for production
- **Monitoring and Observability**: Tracking multi-agent system performance

### **Frequently Asked Questions**

- **When should I use parallel vs sequential agents?**
  Use parallel for independent tasks that can run simultaneously. Use sequential when tasks depend on previous results.

- **How do I handle errors in multi-agent workflows?**
  Implement error handling in individual agents and consider circuit breaker patterns for critical failures.

- **Can I mix different patterns in one system?**
  Absolutely! Real systems often combine patterns—for example, a hierarchical system might use parallel agents at each level.

- **How do I debug multi-agent workflows?**
  Use the ADK trace functionality and add logging to track state changes and agent handoffs.