# AI Agents with Google's Agent Development Kit (ADK) Bootcamp

## Course Overview

This repository contains materials for the **O'Reilly Live Training: AI Agents with Google's Agent Development Kit (ADK) Bootcamp** - a comprehensive 2-day course on building AI agents with Gemini, Agent Protocols, and AgentOps.

**Duration**: 10 hours (2 days, 5 hours per day)

**Level**: Beginner to Intermediate

**Instructors**:

- Ivan Nardini
- Sita Lakshmi Sangameswaran

## Course Description

Start building AI agents with Google's Agent Development Kit (ADK). Learn the core concepts, tools, and patterns needed to create agents that can reason, use tools, and interact with the world, all within Vertex AI. This course guides you through the ADK setup, agent development, integration with language models like Gemini, custom tools, conversational memory, and important agentic patterns.

## What You'll Learn

By the end of this course, you will be able to:

- Understand the core concepts and workflow of building AI agents with ADK
- Run and test simple agents using ADK command-line tools
- Connect agents to Google's foundational LLMs (e.g., Gemini) and other open models and tools
- Grasp the fundamentals of Multi-agent systems and design patterns
- Adopt agents protocols or standards with MCP and A2A
- Evaluate, deploy and secure your agents for production

## Repository Structure

```
oreilly-ai-agents-gcp/
      module_1/               # Introduction to Agents and ADK
      module_3/               # Models and Tools
      module_6/               # MCP and A2A Integration
      module_7/               # Agent Evaluation, Deployment and Ops
```

## Prerequisites

### Technical Requirements

- Basic proficiency in Python programming
- Familiarity with fundamental cloud computing concepts (APIs, services)
- Understanding of core LLMs concepts (LLMs, Prompting, RAG)
- Comfort using the command line/terminal

### System Setup

- Python installed
- Docker installation (optional, for specific examples)
- Code editor (VS Code recommended)
- Internet access
- Google Cloud Platform account with billing enabled (free credits available)

## Getting Started

1. **Clone this repository**

   ```bash
   git clone https://github.com/inardini/oreilly-ai-agents-gcp
   cd oreilly-ai-agents-gcp
   ```

2. **Set up your GCP account**

   - Create a GCP account if you don't have one
   - Enable billing (free credits available)
   - Enable required APIs for Vertex AI

3. **Install ADK**

   - Follow the ADK installation guide in the documentation
   - Run `adk init` to verify installation

4. **Follow the labs**
   - Start with `module_1`
   - Complete modules in sequential order

## Course Schedule

### Day 1

- **Module 1** (70 min): Introduction to Agents and ADK
- **Module 2** (70 min): Models and Tools
- **Module 3** (70 min): Multimodal agents and Memory Persistence
- **Module 4** (75 min): Agentic Design Patterns

### Day 2

- **Recap** (70 min): Review and Daily Briefing Agent exercise
- **Module 5** (70 min): MCP and A2A
- **Module 6** (70 min): Agent Evaluation, Deployment and AgentOps
- **Module 7** (75 min): Agentic Security

## Key Technologies

- **Google Cloud Platform**: Cloud infrastructure and services
- **Vertex AI**: Google's AI platform
- **Agent Development Kit (ADK)**: Framework for building AI agents
- **Gemini**: Google's foundational LLM
- **Model Context Protocol (MCP)**: Agent communication protocol
- **Agent-to-Agent (A2A)**: Multi-agent collaboration framework

## Resources

- [ADK Documentation](https://google.github.io/adk-docs/)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/generative-ai/docs)

## Support

For questions or issues:

- Check the lab instructions for detailed guidance
- Reach out during live Q&A sessions
- Submit issues to this repository

## Final note

This repository is for educational purposes as part of the O'Reilly Live Training course.
