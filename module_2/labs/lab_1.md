# Lab #1: Working with Different Models and Providers in ADK

Welcome to Module 2 of the AI Agents with Google's Agent Development Kit (ADK) Bootcamp! In this hands-on lab, you'll learn how to configure and work with different language models and providers in ADK. One of the powerful features of ADK is its flexibility to work with various LLM providers while maintaining the same agent code structure.

You'll explore how to seamlessly switch between different Gemini models, use Vertex AI, experiment with Gemini Live API, and integrate third-party models via LiteLLM—all while keeping your agent logic unchanged.

### **What You'll Learn**

- How to configure agents with different Gemini model variants (flash, pro, live).
- How to switch between Google AI Studio and Vertex AI as your model provider.
- How to use the Gemini Live API for real-time conversational experiences.
- How to integrate third-party models (like Claude) using LiteLLM.
- How the ADK abstraction allows for provider-agnostic agent development.
- Best practices for model selection based on your use case requirements.

### **What You'll Need**

- A computer with Python 3.10 or higher installed.
- A code editor like Visual Studio Code.
- Access to a command line/terminal.
- A Google account with access to Google AI Studio and/or Vertex AI.
- API keys for Google AI Studio and optionally Anthropic (for the LiteLLM example).

Let's explore the world of multi-model AI agents.

## 1. Set Up Your Model Testing Environment

First, let's create a dedicated project for testing different models and providers.

1. Open your terminal and create a new directory for this lab:

    ```console
    mkdir adk-models-lab
    cd adk-models-lab
    ```

2. Create and activate a Python virtual environment:

    ```console
    python3 -m venv .venv
    source .venv/bin/activate
    # On Windows: .venv\Scripts\activate
    ```

3. Install the ADK library:

    ```console
    pip install google-adk
    ```

4. Create the project structure:

    ```console
    mkdir model_agent
    touch model_agent/__init__.py
    touch .env
    ```

5. Add the required import to the `__init__.py` file:

    ```python
    # model_agent/__init__.py
    from . import agent
    ```

6. Add your initial configuration to the `.env` file:

    ```
    GOOGLE_GENAI_USE_VERTEXAI=0
    GOOGLE_API_KEY=your-google-ai-studio-api-key-here
    ```

## 2. Demo 1: Using Gemini Models from Google AI Studio

Let's start with the standard Gemini model from Google AI Studio. Create `model_agent/agent.py` with the following code:

```python
from google.adk.agents import LlmAgent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

root_agent = LlmAgent(
    name="weather_time_agent",
    model="gemini-2.0-flash",
    description=(
        "Agent to answer questions about the time and weather in a city."
    ),
    instruction=(
        "You are a helpful agent who can answer user questions about the time and weather in a city. "
        "Be friendly and informative in your responses. If you don't have access to real-time data, "
        "let the user know and suggest how they can get current information."
    ),
)
```

### **Test Your Google AI Studio Agent**

1. From your project root directory, start the ADK web interface:

    ```console
    adk web
    ```

2. Open your browser to `http://127.0.0.1:8080` and test with these prompts:
    - `What's the weather like in New York?`
    - `What time is it in Tokyo?`
    - `Tell me about the climate in London`

Notice how the agent responds. Since it doesn't have real-time tools, it will explain its limitations while being helpful.

## 3. Demo 2: Exploring Gemini Live API

The Gemini Live API enables real-time conversational experiences. Let's see how easy it is to switch to this model variant.

Update your `model_agent/agent.py` to use the Live API:

```python
from google.adk.agents import LlmAgent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

root_agent = LlmAgent(
    name="weather_time_agent",
    model="gemini-2.0-flash-live-001",  # Changed to Live API model
    description=(
        "Agent to answer questions about the time and weather in a city."
    ),
    instruction=(
        "You are a helpful agent who can answer user questions about the time and weather in a city. "
        "Be friendly and informative in your responses. If you don't have access to real-time data, "
        "let the user know and suggest how they can get current information."
    ),
)
```

### **Understanding Gemini Live**

The Gemini Live API is designed for:
- Real-time conversational experiences
- Lower latency interactions
- Streaming responses
- Enhanced conversational flow

> **Note:** The Live API may have different rate limits and pricing compared to the standard API. Check the current Google AI documentation for the latest details.

Restart your web interface (`Ctrl+C` then `adk web`) and test the same prompts. You may notice improved response times and conversational flow.

## 4. Demo 3: Switching to Vertex AI

Vertex AI is Google Cloud's enterprise AI platform. It offers enhanced security, compliance, and integration with Google Cloud services. The beauty of ADK is that switching providers requires only environment configuration changes.

### **Configure Vertex AI**

1. Update your `.env` file to use Vertex AI:

    ```
    GOOGLE_GENAI_USE_VERTEXAI=1
    GOOGLE_CLOUD_PROJECT=your-project-id
    GOOGLE_CLOUD_LOCATION=us-central1
    # Remove or comment out GOOGLE_API_KEY
    ```

2. Ensure you have Google Cloud credentials configured. You can either:
   - Run `gcloud auth application-default login`
   - Or set up a service account with appropriate permissions

3. Your agent code stays exactly the same! Update back to the standard model:

```python
from google.adk.agents import LlmAgent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

root_agent = LlmAgent(
    name="weather_time_agent",
    model="gemini-2.0-flash",  # Same model, now via Vertex AI
    description=(
        "Agent to answer questions about the time and weather in a city."
    ),
    instruction=(
        "You are a helpful agent who can answer user questions about the time and weather in a city. "
        "Be friendly and informative in your responses. If you don't have access to real-time data, "
        "let the user know and suggest how they can get current information."
    ),
)
```

### **Vertex AI Benefits**

- **Enterprise Security**: Enhanced data governance and security controls
- **Integration**: Seamless integration with Google Cloud services
- **Monitoring**: Built-in logging and monitoring capabilities
- **Compliance**: Supports various compliance requirements

Restart your agent and test—the functionality remains identical, but now you're using Vertex AI's enterprise infrastructure.

## 5. Demo 4: Using Third-Party Models with LiteLLM

ADK supports third-party models through LiteLLM, which provides a unified interface to various model providers. Let's integrate Anthropic's Claude model.

### **Install LiteLLM**

First, install the LiteLLM dependency:

```console
pip install litellm
```

### **Configure Third-Party API Keys**

Add your Anthropic API key to your `.env` file:

```
GOOGLE_GENAI_USE_VERTEXAI=0
GOOGLE_API_KEY=your-google-ai-studio-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

### **Update Your Agent**

```python
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

root_agent = LlmAgent(
    name="weather_time_agent",
    model=LiteLlm(model="anthropic/claude-3-haiku-20240307"),
    description=(
        "Agent to answer questions about the time and weather in a city."
    ),
    instruction=(
        "You are a helpful agent who can answer user questions about the time and weather in a city. "
        "Be friendly and informative in your responses. If you don't have access to real-time data, "
        "let the user know and suggest how they can get current information."
    ),
)
```

### **Understanding LiteLLM Integration**

The `LiteLlm` wrapper provides:
- **Unified Interface**: Same ADK agent code works with different providers
- **Provider Flexibility**: Easy switching between OpenAI, Anthropic, Cohere, and others
- **Consistent Behavior**: Tool calling and other ADK features work across providers

Test your Claude-powered agent and notice any differences in response style or capabilities.

## 6. Model Selection Guide

Different models excel in different scenarios. Here's a guide to help you choose:

### **Gemini 2.0 Flash**
- **Best for**: General-purpose applications, fast responses
- **Strengths**: Speed, cost-effectiveness, good reasoning
- **Use cases**: Chatbots, content generation, simple analysis

### **Gemini 2.0 Flash Live**
- **Best for**: Real-time conversational experiences
- **Strengths**: Low latency, streaming responses
- **Use cases**: Live chat, interactive assistants, real-time applications

### **Vertex AI vs Google AI Studio**
- **Google AI Studio**: Quick prototyping, development, simpler setup
- **Vertex AI**: Production deployments, enterprise features, compliance needs

### **Third-Party Models (via LiteLLM)**
- **Claude**: Excellent for reasoning, analysis, longer contexts
- **GPT-4**: General capabilities, large ecosystem
- **Use when**: You need specific model capabilities or have existing provider relationships

## 7. Congratulations!

You've successfully explored ADK's multi-model capabilities!

In this lab, you learned to:

✅ **Configure agents** with different Gemini model variants

✅ **Switch providers** seamlessly between Google AI Studio and Vertex AI

✅ **Integrate real-time capabilities** using Gemini Live API

✅ **Use third-party models** via LiteLLM integration

✅ **Understand model selection** criteria for different use cases

### **Key Takeaways**

- **Provider Abstraction**: ADK abstracts away provider differences, letting you focus on agent logic
- **Easy Switching**: Environment variables control provider configuration without code changes
- **Model Diversity**: Different models offer different strengths—choose based on your requirements
- **Enterprise Ready**: Vertex AI provides enterprise features when you need them

### **What's Next?**

Now that you understand model flexibility, you're ready to explore:
- **Function Tools**: Adding custom capabilities to your agents
- **Built-in Tools**: Leveraging pre-built tools for common tasks
- **Agent Orchestration**: Building multi-agent systems
- **Production Deployment**: Scaling your agents for real-world use

### **Frequently Asked Questions**

- **Which model should I use for production?**
  Consider your requirements: speed (Flash), real-time (Live), enterprise features (Vertex AI), or specific capabilities (third-party models).

- **Can I mix different models in the same application?**
  Yes! Different agents can use different models based on their specific roles and requirements.

- **How do I handle API rate limits?**
  Each provider has different rate limits. ADK provides built-in retry mechanisms, and you can implement custom retry logic if needed.

- **Are there cost differences between providers?**
  Yes, pricing varies by provider and model. Check current pricing documentation for your specific use case.