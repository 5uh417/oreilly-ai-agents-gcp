# Lab #2: Building Custom Multi-Agent Orchestrators

Welcome to Module 4, Lab 2! You've learned the fundamental multi-agent patterns and built complex production systems. Now it's time to master the ultimate ADK pattern: **Custom Agents**.

Custom Agents allow you to create sophisticated orchestrators that combine multiple workflow patterns with custom logic, conditional flows, and complex decision-making. Instead of using pre-built patterns like Sequential or Parallel agents, you'll build your own agent class that inherits from `BaseAgent` and implements exactly the workflow logic your application needs.

This lab demonstrates how to build a **Creative Writing Assistant** that orchestrates story generation, critique, revision, and quality checks with conditional logic based on tone analysis. It's a perfect example of when you need more control than standard patterns provide.

### **What You'll Learn**

- How to create Custom Agent classes by inheriting from `BaseAgent`
- How to implement custom orchestration logic with `_run_async_impl`
- How to combine multiple workflow patterns within a single custom agent
- How to add conditional logic and decision-making to agent workflows
- How to manage state and data flow between multiple internal agents
- How to handle complex business logic that doesn't fit standard patterns
- Best practices for building maintainable custom agent architectures

### **What You'll Need**

- A computer with Python 3.10 or higher installed
- A code editor like Visual Studio Code
- Access to a command line/terminal
- A Google account with access to Google AI Studio or Vertex AI

Let's build a sophisticated custom orchestrator!

## 1. Understanding Custom Agents in ADK

Before diving into implementation, let's understand why and when you need Custom Agents.

### **When Standard Patterns Aren't Enough**

The built-in ADK patterns are powerful but have limitations:

- **Sequential Agent**: Great for linear workflows, but can't handle conditional branching
- **Parallel Agent**: Perfect for concurrent tasks, but doesn't support complex decision trees
- **Loop Agent**: Excellent for iterative refinement, but limited to simple iteration logic
- **Coordinator Agent**: Good for routing, but can't orchestrate complex multi-step workflows

### **Custom Agent Capabilities**

Custom Agents give you complete control over:

- **Conditional Logic**: "If tone is negative, regenerate; otherwise, proceed"
- **Complex Orchestration**: Combining Sequential, Parallel, and Loop patterns in one workflow
- **Business Rules**: Implementing domain-specific decision-making logic
- **State Management**: Custom handling of data flow between workflow steps
- **Error Handling**: Sophisticated error recovery and fallback mechanisms

### **The Creative Writing Use Case**

**Goal:** Create a system that generates a story, iteratively refines it through critique and revision, performs final checks, and crucially, regenerates the story if the final tone check fails.

**Why Custom?** The core requirement driving the need for a custom agent here is the conditional regeneration based on the tone check. Standard workflow agents don't have built-in conditional branching based on the outcome of a sub-agent's task. We need custom logic (if tone == "negative": ...) within the orchestrator.

Our Creative Writing Assistant demonstrates these capabilities:

1. **Story Generation**: Create initial story based on user topic
2. **Critique Loop**: Iteratively improve the story through critic-reviser cycles
3. **Quality Checks**: Grammar and tone analysis in parallel
4. **Conditional Logic**: Regenerate if tone is negative, otherwise keep story
5. **State Management**: Maintain story versions and analysis results throughout

This workflow requires conditional logic and complex orchestration that no single built-in pattern can handle.

## 2. Set Up Your Custom Agent Laboratory

Let's create a dedicated environment for building sophisticated custom agents.

1. Open your terminal and create a new directory for this lab:

    ```console
    mkdir adk-custom-agent-lab
    cd adk-custom-agent-lab
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

4. Create the project structure:

    ```console
    mkdir creative_writing_agent
    touch creative_writing_agent/__init__.py
    touch creative_writing_agent/agent.py
    touch .env
    ```

5. Add the required import to the `__init__.py` file:

    ```python
    # creative_writing_agent/__init__.py
    from . import agent
    ```

6. Set up your environment variables in `.env`:

    ```
    GOOGLE_GENAI_USE_VERTEXAI=0
    GOOGLE_API_KEY=your-google-ai-studio-api-key-here
    ```

## 3. Understanding the Custom Agent Architecture

Let's break down the key components of our Custom Agent before implementation.

### **Custom Agent Class Structure**

```python
class StoryFlowAgent(BaseAgent):
    """Custom agent that orchestrates creative writing workflow"""

    # Pydantic field declarations for type safety
    story_generator: LlmAgent
    critic: LlmAgent
    reviser: LlmAgent
    # ... other agents

    def __init__(self, name: str, **agents):
        # Initialize internal workflow agents
        # Call super().__init__ with all required parameters

    @override
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        # Custom orchestration logic goes here
```

### **Key Concepts**

- **BaseAgent Inheritance**: Provides the foundation for custom behavior
- **Pydantic Integration**: Type-safe field declarations for internal agents
- **InvocationContext**: Provides access to session state and configuration
- **AsyncGenerator[Event, None]**: Stream events back to the ADK framework
- **Custom Orchestration**: Complete control over workflow execution order

### **State Management in Custom Agents**

```python
# Reading from session state
story = ctx.session.state.get("current_story")

# Writing to session state (done by agents with output_key)
# Each internal agent can set its output_key to save results

# Conditional logic based on state
if ctx.session.state.get("tone_check_result") == "negative":
    # Regenerate story
```

## 4. Build the Individual Specialist Agents

First, let's create the individual LLM agents that will be orchestrated by our custom agent.

Create `creative_writing_agent/agent.py` with the following code:

```python
import logging
from typing import AsyncGenerator
from typing_extensions import override

from google.adk.agents import LlmAgent, BaseAgent, LoopAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.genai import types
from google.adk.events import Event
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
GEMINI_2_FLASH = "gemini-2.0-flash"

# --- Individual Specialist Agents ---

story_generator = LlmAgent(
    name="StoryGenerator",
    model=GEMINI_2_FLASH,
    description="Creates original short stories based on given topics.",
    instruction="""You are a creative story writer. Write a compelling short story (around 100-150 words)
    based on the following topic: {topic}

    Make the story engaging with:
    - Clear characters and setting
    - An interesting conflict or challenge
    - A satisfying resolution

    Focus on creativity and emotional impact.""",
    output_key="current_story"  # Saves output to session state
)

critic = LlmAgent(
    name="StoryCritic",
    model=GEMINI_2_FLASH,
    description="Provides constructive criticism to improve stories.",
    instruction="""You are an expert story critic. Review this story: {current_story}

    Provide 1-2 sentences of constructive criticism focusing on:
    - Character development
    - Plot structure
    - Emotional impact
    - Clarity and flow

    Be specific and actionable in your feedback.""",
    output_key="criticism"
)

reviser = LlmAgent(
    name="StoryReviser",
    model=GEMINI_2_FLASH,
    description="Revises stories based on critical feedback.",
    instruction="""You are a story editor. Revise this story: {current_story}

    Apply this criticism: {criticism}

    Improve the story while maintaining its core essence. Output only the revised story.""",
    output_key="current_story"  # Overwrites the original story
)

grammar_check = LlmAgent(
    name="GrammarChecker",
    model=GEMINI_2_FLASH,
    description="Analyzes grammar and writing quality.",
    instruction="""You are a grammar and style checker. Analyze this story: {current_story}

    Check for:
    - Grammar errors
    - Sentence structure
    - Word choice
    - Clarity issues

    If the grammar is good, respond with 'Grammar is excellent!'
    Otherwise, provide a brief list of specific improvements needed.""",
    output_key="grammar_suggestions"
)

tone_check = LlmAgent(
    name="ToneAnalyzer",
    model=GEMINI_2_FLASH,
    description="Analyzes the emotional tone of stories.",
    instruction="""You are a tone analyzer. Analyze the overall emotional tone of this story: {current_story}

    Consider the story's mood, atmosphere, and emotional impact.

    Respond with exactly one word:
    - 'positive' if the tone is uplifting, hopeful, or joyful
    - 'negative' if the tone is dark, sad, or depressing
    - 'neutral' if the tone is balanced or neither strongly positive nor negative""",
    output_key="tone_check_result"  # This determines conditional flow
)
```

## 5. Build the Custom Orchestrator Agent

Now let's create the main Custom Agent that orchestrates our creative writing workflow.

Add the following to `creative_writing_agent/agent.py`:

```python
# --- Custom Orchestrator Agent ---

class StoryFlowAgent(BaseAgent):
    """
    Custom agent for a story generation and refinement workflow.

    This agent demonstrates advanced orchestration by combining:
    - Initial story generation
    - Iterative critic-reviser loop (LoopAgent pattern)
    - Parallel quality checks (SequentialAgent pattern)
    - Conditional logic based on tone analysis
    """

    # Pydantic field declarations for type safety
    story_generator: LlmAgent
    critic: LlmAgent
    reviser: LlmAgent
    grammar_check: LlmAgent
    tone_check: LlmAgent

    # Internal workflow agents
    loop_agent: LoopAgent
    sequential_agent: SequentialAgent

    # Allow arbitrary types for Pydantic
    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self,
        name: str,
        story_generator: LlmAgent,
        critic: LlmAgent,
        reviser: LlmAgent,
        grammar_check: LlmAgent,
        tone_check: LlmAgent,
    ):
        """
        Initialize the StoryFlowAgent with all required specialist agents.

        Args:
            name: The name of the custom agent
            story_generator: Agent to create initial stories
            critic: Agent to provide story criticism
            reviser: Agent to revise stories based on criticism
            grammar_check: Agent to check grammar and style
            tone_check: Agent to analyze story tone
        """
        # Create internal workflow agents BEFORE calling super().__init__
        loop_agent = LoopAgent(
            name="CriticReviserLoop",
            sub_agents=[critic, reviser],
            max_iterations=2,  # Limit iterations to prevent infinite loops
            description="Iteratively improves story through critic-reviser cycles"
        )

        sequential_agent = SequentialAgent(
            name="QualityChecks",
            sub_agents=[grammar_check, tone_check],
            description="Performs grammar and tone analysis in sequence"
        )

        # Define sub_agents for the framework
        sub_agents_list = [
            story_generator,
            loop_agent,
            sequential_agent,
        ]

        # Call parent constructor with all required parameters
        super().__init__(
            name=name,
            story_generator=story_generator,
            critic=critic,
            reviser=reviser,
            grammar_check=grammar_check,
            tone_check=tone_check,
            loop_agent=loop_agent,
            sequential_agent=sequential_agent,
            sub_agents=sub_agents_list,
            description="Custom orchestrator for creative writing workflow with conditional logic"
        )

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Implements the custom orchestration logic for the story workflow.

        Workflow:
        1. Generate initial story
        2. Run critic-reviser loop for iterative improvement
        3. Perform quality checks (grammar and tone)
        4. Conditionally regenerate if tone is negative
        """
        logger.info(f"[{self.name}] Starting creative writing workflow")

        # Extract topic from user message or session state
        topic = ctx.session.state.get("topic")

        # If no topic in state, extract from the user's current message
        if not topic and ctx.user_content and ctx.user_content.parts:
            topic = ctx.user_content.parts[0].text.strip()
            # Store the topic in session state for consistency
            ctx.session.state["topic"] = topic
            logger.info(f"[{self.name}] Extracted topic from user message: {topic}")

        if not topic:
            logger.error(f"[{self.name}] No topic provided in user message or session state")
            return

        logger.info(f"[{self.name}] Working on topic: {topic}")

        # 1. Initial Story Generation
        logger.info(f"[{self.name}] Step 1: Generating initial story")
        async for event in self.story_generator.run_async(ctx):
            logger.info(f"[{self.name}] StoryGenerator event: {event.model_dump_json(exclude_none=True)}")
            yield event

        # Verify story was generated
        if "current_story" not in ctx.session.state or not ctx.session.state["current_story"]:
            logger.error(f"[{self.name}] Failed to generate initial story. Aborting workflow.")
            return

        initial_story = ctx.session.state["current_story"]
        logger.info(f"[{self.name}] Generated story: {initial_story[:100]}...")

        # 2. Critic-Reviser Loop for Iterative Improvement
        logger.info(f"[{self.name}] Step 2: Running critic-reviser improvement loop")
        async for event in self.loop_agent.run_async(ctx):
            logger.info(f"[{self.name}] CriticReviserLoop event: {event.model_dump_json(exclude_none=True)}")
            yield event

        improved_story = ctx.session.state.get("current_story", initial_story)
        logger.info(f"[{self.name}] Story after improvement: {improved_story[:100]}...")

        # 3. Quality Checks (Grammar and Tone Analysis)
        logger.info(f"[{self.name}] Step 3: Performing quality checks")
        async for event in self.sequential_agent.run_async(ctx):
            logger.info(f"[{self.name}] QualityChecks event: {event.model_dump_json(exclude_none=True)}")
            yield event

        # 4. Conditional Logic Based on Tone Analysis
        tone_result = ctx.session.state.get("tone_check_result", "").lower()
        grammar_result = ctx.session.state.get("grammar_suggestions", "")

        logger.info(f"[{self.name}] Quality check results:")
        logger.info(f"[{self.name}] - Tone: {tone_result}")
        logger.info(f"[{self.name}] - Grammar: {grammar_result}")

        # Conditional regeneration for negative tone
        if tone_result == "negative":
            logger.info(f"[{self.name}] Step 4: Tone is negative, regenerating with more positive approach")

            # Modify the topic to encourage positive tone
            original_topic = ctx.session.state.get("topic", "")
            positive_topic = f"{original_topic} (focus on hope, resilience, and positive outcomes)"
            ctx.session.state["topic"] = positive_topic

            # Regenerate the story
            async for event in self.story_generator.run_async(ctx):
                logger.info(f"[{self.name}] StoryGenerator (regen) event: {event.model_dump_json(exclude_none=True)}")
                yield event

            # Restore original topic
            ctx.session.state["topic"] = original_topic

            final_story = ctx.session.state.get("current_story", improved_story)
            logger.info(f"[{self.name}] Regenerated story: {final_story[:100]}...")
        else:
            logger.info(f"[{self.name}] Step 4: Tone is acceptable ({tone_result}), keeping current story")

        logger.info(f"[{self.name}] Creative writing workflow completed successfully")


# --- Create the Custom Agent Instance ---

# Instantiate the custom orchestrator
root_agent = StoryFlowAgent(
    name="CreativeWritingAssistant",
    story_generator=story_generator,
    critic=critic,
    reviser=reviser,
    grammar_check=grammar_check,
    tone_check=tone_check,
)
```

## 6. Testing Your Custom Agent

Let's test your sophisticated custom orchestrator with various creative writing scenarios.

### **Start the Agent**

1. From your project root directory, start the ADK web interface:

    ```console
    adk web
    ```

2. Open your browser to `http://127.0.0.1:8080` and select `creative_writing_agent.CreativeWritingAssistant` from the dropdown.

### **Test Scenarios**

Try these creative writing prompts to see different workflow paths:

#### **Scenario 1: Positive Story Flow**
```
Write a story about a young inventor who creates a device that brings happiness to their community
```

Expected workflow:
1.  Generate initial uplifting story
2.  Critic-reviser loop improves the story
3.  Grammar and tone checks pass
4.  Tone is positive, no regeneration needed

#### **Scenario 2: Negative Tone Triggers Regeneration**
```
Write a story about a person who loses everything they care about
```

Expected workflow:
1.  Generate initial (likely dark) story
2.  Critic-reviser loop refines the story
3.  Tone check detects negative tone
4.  Story regenerated with positive focus

#### **Scenario 3: Adventure with Complex Elements**
```
Write a story about a lonely robot finding a friend in a junkyard
```

Expected workflow:
1.  Generate story with potential for either positive or neutral tone
2.  Iterative improvement through critic feedback
3.  Quality checks analyze final result
4.  Conditional logic based on detected tone

#### **Scenario 4: Fantasy with Emotional Depth**
```
Write a story about a brave kitten exploring a haunted house
```

Expected workflow:
1.  Generate initial story (could be scary or cute)
2.  Critic provides feedback on character development
3.  Reviser improves emotional impact
4.  Decision logic based on final tone assessment

### **Understanding the Custom Workflow**

Watch the console logs to see your custom orchestration in action:

1. **Story Generation**: Initial creative content creation
2. **Iterative Improvement**: Critic-reviser loop (up to 2 iterations)
3. **Quality Analysis**: Grammar check followed by tone analysis
4. **Conditional Logic**: Decision to keep or regenerate based on tone
5. **State Management**: Story versions and analysis results preserved

## 7. Advanced Custom Agent Patterns

### **Understanding the Custom Orchestration Logic**

Your custom agent demonstrates several advanced patterns:

#### **Conditional Workflow Branching**
```python
# Conditional logic based on analysis results
if tone_result == "negative":
    # Regenerate with positive instructions
    positive_topic = f"{original_topic} (focus on hope and positive outcomes)"
    # Run generator again with modified context
else:
    # Keep current story
    pass
```

#### **Dynamic Context Modification**
```python
# Temporarily modify the topic for regeneration
original_topic = ctx.session.state.get("topic", "")
positive_topic = f"{original_topic} (focus on hope, resilience, and positive outcomes)"
ctx.session.state["topic"] = positive_topic

# Restore original context after regeneration
ctx.session.state["topic"] = original_topic
```

#### **Combining Multiple Workflow Patterns**
```python
# Create internal agents that use different patterns
loop_agent = LoopAgent(...)        # For iterative improvement
sequential_agent = SequentialAgent(...)  # For quality checks

# Orchestrate them in custom order
async for event in self.story_generator.run_async(ctx):
    yield event  # Initial generation

async for event in self.loop_agent.run_async(ctx):
    yield event  # Iterative improvement

async for event in self.sequential_agent.run_async(ctx):
    yield event  # Quality checks
```

#### **State-Driven Decision Making**
```python
# Make decisions based on accumulated state
tone_result = ctx.session.state.get("tone_check_result", "").lower()
grammar_result = ctx.session.state.get("grammar_suggestions", "")

# Complex business logic
if tone_result == "negative":
    # Custom regeneration logic
elif grammar_result != "Grammar is excellent!":
    # Could add grammar correction workflow
else:
    # Story is acceptable as-is
```

### **Error Handling in Custom Agents**

Add robust error handling to your custom workflows:

```python
# Verify preconditions
if "current_story" not in ctx.session.state:
    logger.error("Story generation failed")
    return  # Stop workflow

# Handle partial failures gracefully
try:
    async for event in self.loop_agent.run_async(ctx):
        yield event
except Exception as e:
    logger.error(f"Loop agent failed: {e}")
    # Continue with original story
```

### **Performance Optimization**

Custom agents allow fine-tuned performance optimization:

```python
# Early termination conditions
if ctx.session.state.get("story_quality_score", 0) > 0.9:
    logger.info("Story quality already excellent, skipping improvement loop")
    return

# Parallel execution for independent analysis
# (Could be implemented with custom async logic)
```

## 8. When to Use Custom Agents

### **Perfect Use Cases**

- **Complex Business Logic**: Multi-step workflows with conditional branches
- **Domain-Specific Orchestration**: Workflows that combine multiple patterns
- **Quality Control Systems**: Multi-stage validation and improvement processes
- **Adaptive Workflows**: Systems that change behavior based on intermediate results

### **Design Decision Framework**

Ask yourself:
1. Do I need conditional logic based on intermediate results? � Custom Agent
2. Do I need to combine multiple workflow patterns? � Custom Agent
3. Is my workflow just linear steps? � Sequential Agent
4. Is my workflow just parallel tasks? � Parallel Agent
5. Is my workflow just iteration? � Loop Agent

## 9. Congratulations!

You've successfully mastered Custom Agents - the most advanced pattern in ADK!