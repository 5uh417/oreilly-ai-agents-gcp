# Lab #1: Understanding and Running an Advanced Image Generation & Scoring System with Loop Agents

Welcome to Module 5 of the AI Agents with Google's Agent Development Kit (ADK) Bootcamp! You've mastered building sophisticated multi-agent systems. Now you'll learn to understand and operate one of the most advanced ADK patterns: **iterative, self-improving agent systems** using the powerful LoopAgent pattern.

In this lab, you'll explore and run a complete image generation and quality scoring system that automatically creates lockscreen images, evaluates them against detailed policy criteria, and iteratively improves them until they meet quality standards. This demonstrates real-world AI systems that must meet strict quality gates and compliance requirements.

This system combines Google's Imagen 3.0 for high-quality image generation with intelligent multi-criteria evaluation, all orchestrated through a sophisticated loop-based workflow that continues until quality standards are achieved.

### **What You'll Learn**

- How LoopAgent systems work for iterative improvement workflows
- How complex multi-agent systems orchestrate Sequential and Loop patterns
- How Google's Imagen 3.0 integrates for professional image generation
- How multi-criteria quality scoring and evaluation systems operate
- How policy-driven content validation works for enterprise compliance
- How state persistence works across loop iterations and agent calls
- How production-ready content generation systems ensure quality assurance
- Best practices for termination conditions and loop control in real systems

### **What You'll Need**

- A computer with Python 3.10 or higher installed
- A code editor like Visual Studio Code
- Access to a command line/terminal
- Completion of Module 4 (understanding of multi-agent patterns)
- A Google AI Studio account with API access (free tier available)
- Understanding of basic image generation concepts
- Access to the `module_5/solution/` directory in this course

## 1. Quick Start: See It In Action

Let's run the system first to see what we're working with, then understand how it works.

### **Setup (2 minutes)**

1. Navigate to the solution directory:
   ```console
   cd oreilly-ai-agents-gcp/module_5/solution
   ```

2. Set up your environment:
   ```console
   python3 -m venv .venv
   source .venv/bin/activate
   pip install google-adk python-dotenv
   ```

3. Update your Google AI Studio API key to `.env`:
   ```console
   vi .env  # Update: GOOGLE_API_KEY=your-key-here
   ```

4. Start the system:
   ```console
   adk web
   ```

5. Open `http://127.0.0.1:8080` and select `solution` from the dropdown.

### **Try It Now**

Paste this prompt and watch the magic happen:
```
Create a stunning mountain landscape at golden hour for a mobile lockscreen
```

**What you'll see:**
- The system automatically enhances your prompt
- Generates a professional-quality image
- Scores it against 10 quality criteria (0-50 points)
- Either approves it (45+ points) or tries again (up to 3 attempts)

**Why this matters:** This is a production pattern used by content platforms that need automated quality control.

## 2. Understanding the System Architecture

Now that you've seen it work, let's understand the sophisticated orchestration behind it.

### **The Core Challenge**

Production content generation needs:
- **Quality Assurance**: Automated evaluation against standards
- **Policy Compliance**: Enterprise guidelines and brand safety
- **Iterative Improvement**: Ability to refine content that doesn't meet criteria
- **Resource Management**: Prevent infinite loops while maximizing quality

### **The Solution: Two-Level Agent Orchestration**

```
🔄 LoopAgent (Root)
   ├── 📋 SequentialAgent (Workflow)
   │   ├── 1. Prompt Agent (Enhance prompts)
   │   ├── 2. Image Agent (Generate with Imagen 3.0)
   │   └── 3. Scoring Agent (Evaluate quality)
   └── ✅ Checker Agent (Continue or stop?)
```

**The Workflow:**
1. **Generate**: Create optimized prompt → Generate image → Score quality
2. **Evaluate**: Check if score ≥ 45 OR reached 3 attempts
3. **Decide**: Stop if criteria met, otherwise loop again

The system critiques and improves its own work automatically.

## 2. Exploring the Project Structure

Let's explore the sophisticated codebase you just ran. Each component has a specific role in the iterative workflow.

### **Project Overview**

```console
ls -la  # See the main files
```

**Key Files:**
- `agent.py` - Main orchestration (LoopAgent + SequentialAgent)
- `config.py` - Quality thresholds and model settings
- `policy.json` - 10 evaluation criteria for image quality
- `subagents/` - Four specialized agents with their tools

### **The Agent Hierarchy**

```console
tree subagents/  # Or: find subagents/ -type f
```

You'll see four specialized agent modules:

```
subagents/
├── prompt/     → Enhances user prompts for Imagen 3.0
├── image/      → Generates images with optimal parameters
├── scoring/    → Evaluates against 10 quality criteria
└── checker/    → Decides to continue or stop the loop
```

**Why This Structure?** Each agent is autonomous but specialized, enabling clean orchestration and easy testing.

## 3. The Core LoopAgent Pattern

Now let's understand the key innovation here - how the system automatically improves its own work.

### **The Quality Control System**

```console
cat config.py
```

The system has two key controls:
- **Quality Threshold**: Score must be ≥ 45 points (out of 50) for approval
- **Iteration Limit**: Maximum 3 attempts to prevent infinite loops

### **How Quality Evaluation Works**

The system evaluates generated images against multiple criteria (defined in `policy.json`) and assigns a total score. If the score is too low, it tries again with an improved approach.

**Key Pattern**: This is how production AI systems ensure output quality while managing computational resources.

## 4. The Four Specialized Agents

The system uses four specialized agents that work together in the loop:

### **1. Prompt Enhancement Agent**
- **Input**: Your basic prompt ("mountain landscape")
- **Output**: Detailed, optimized prompt for Imagen 3.0
- **Why**: Transforms simple requests into professional-quality generation prompts

### **2. Image Generation Agent**
- **Input**: Enhanced prompt from Agent 1
- **Output**: Generated image saved as an artifact
- **Integration**: Uses Google's Imagen 3.0 with mobile-optimized parameters

### **3. Quality Scoring Agent**
- **Input**: Generated image
- **Output**: Quality score (0-50 points based on multiple criteria)
- **Role**: Acts like an AI art director evaluating the work

### **4. Loop Control Agent**
- **Input**: Quality score and iteration count
- **Decision Logic**:
  - Score ≥ 45? → **Stop** (success!)
  - 3 attempts used? → **Stop** (resource limit)
  - Otherwise → **Continue** improving
- **Critical Function**: Uses `tool_context.actions.escalate = True` to control the loop

**Key Insight**: Each agent has a single, focused responsibility but they work together to create an intelligent, self-improving system.

## 5. The Orchestration Magic

Now let's examine the sophisticated two-level orchestration system that coordinates the entire workflow.

Examine the complete orchestration logic:

```console
cat agent.py
```

This file demonstrates **advanced multi-level agent orchestration**:

### **Level 1: Sequential Agent (Workflow Orchestrator)**

```python
image_generation_scoring_agent = SequentialAgent(
    name="image_generation_scoring_agent",
    description="Analyzes input text and creates...",
    sub_agents=[
        image_generation_prompt_agent,  # Step 1: Enhance prompts
        image_generation_agent,         # Step 2: Generate images
        scoring_agent,                  # Step 3: Evaluate quality
    ],
)
```

**Sequential Pattern Benefits:**
- **Ordered Execution**: Each step builds on the previous
- **State Flow**: Data flows seamlessly between agents
- **Focused Responsibility**: Each agent has a single, clear purpose

### **Level 2: Loop Agent (Root Orchestrator)**

```python
image_scoring = LoopAgent(
    name="image_scoring",
    description="Repeatedly runs a sequential process...",
    sub_agents=[
        image_generation_scoring_agent,  # Execute the 3-step workflow
        checker_agent_instance,          # Evaluate and control loop
    ],
    max_iterations=3,
)
```

**Loop Pattern Benefits:**
- **Iterative Improvement**: Continues until quality threshold met
- **Resource Management**: Respects maximum iteration limits
- **Intelligent Termination**: Uses escalation mechanism for control

### **Two-Level Architecture Benefits**

1. **Separation of Concerns**: Workflow logic separate from loop control
2. **Reusability**: Sequential agent could be used in non-loop contexts
3. **Maintainability**: Clear boundaries between different orchestration levels
4. **Testability**: Each level can be tested independently

### **Environment Integration**

```python
from dotenv import load_dotenv
load_dotenv()  # Loads configuration from .env file
```

This ensures all environment variables are available to the agent system.

## 6. Observing the System in Action

### **Test Different Scenarios**

Try these prompts to see different iteration patterns:

#### **Detailed Prompt (Usually 1 iteration)**
```
Create a stunning mountain landscape at golden hour for a mobile lockscreen
```

#### **Vague Prompt (Usually multiple iterations)**
```
A simple landscape photo
```

#### **Very Vague Prompt (Tests the limits)**
```
Design something beautiful
```

### **What to Watch For**

**In the Console Output:**
- Current iteration count (1/3, 2/3, etc.)
- Quality scores after each attempt
- Decision messages ("Quality threshold met" or "Continuing to next iteration")

**In the Web Interface:**
- **State Panel**: Watch `total_score` and `loop_iteration` update
- **Generated Images**: Notice improvements across iterations

**Key Patterns:**
- More detailed prompts → Higher initial scores → Fewer iterations
- Vague prompts → Lower initial scores → More iterations needed
- System always respects the 3-iteration limit

## 7. Experimenting with the System

### **Experimenting with Quality Thresholds**

Try modifying the threshold in the `.env` file to see different behaviors:
```console
# Edit .env to experiment with different thresholds
nano .env
```

```
SCORE_THRESHOLD=40  # Lower threshold - observe more first-iteration approvals
SCORE_THRESHOLD=48  # Higher threshold - observe more iteration cycles
```

### **Experimenting with Iteration Limits**

Observe how different limits affect the process:
```
MAX_ITERATIONS=1  # Single attempt only - no improvement cycles
MAX_ITERATIONS=5  # More improvement opportunities - extended iteration observation
```

**After making changes**: Restart the `adk web` command to see the effects.

### **Observe Real-Time State**

In the ADK web interface **State** panel, watch these values update:
- `total_score` - Quality score from the scoring agent
- `loop_iteration` - Current iteration number
- `checker_output` - Loop control decisions

**Key Insight**: You can see the "thinking" process of the system in real-time.

## 8. Production Patterns You've Learned

### **LoopAgent Best Practices**

This system demonstrates enterprise patterns:

**Quality Gates:**
- Automated evaluation with configurable thresholds
- Multi-criteria scoring for objective assessment
- Clear pass/fail decisions

**Resource Management:**
- Iteration limits prevent infinite loops
- Early termination when quality is achieved
- Transparent decision-making process

**State Orchestration:**
- Data flows seamlessly between agents
- State persists across iterations
- Each agent has access to what it needs

**Real-World Applications:**
- Content moderation systems
- Creative AI tools with quality control
- Automated workflow optimization
- Brand compliance checking

## 9. Key Takeaways

🎉 **Congratulations!** You've mastered the LoopAgent pattern - one of the most powerful ADK orchestration techniques.

### **What You've Learned**

✅ **LoopAgent Pattern** - How to build AI systems that iteratively improve their output
✅ **Quality Control** - Automated evaluation and decision-making
✅ **Two-Level Orchestration** - Separating workflow logic from iteration control
✅ **Production Integration** - Connecting external AI services with ADK state management

### **Why This Matters**

Loop-based agent systems power:
- **Content Creation Platforms** - Automated quality gates
- **Creative AI Tools** - Iterative refinement processes
- **Compliance Systems** - Ensuring output meets standards
- **Optimization Engines** - Continuous improvement workflows

### **Your Next Steps**

**Build Your Own:**
- Create LoopAgent systems for your specific use cases
- Experiment with different quality frameworks
- Integrate other AI services using these patterns

**Go Production:**
- Scale these patterns for enterprise use
- Add monitoring and cost optimization
- Build custom quality evaluation systems

**You now understand how to architect self-improving AI systems!** 🚀

These patterns are the foundation of enterprise-grade AI that can maintain quality standards while operating autonomously.