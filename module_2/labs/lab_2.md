# Lab #2: Combining Built-in Tools and Custom Functions with ADK

Welcome to the second lab of Module 2! In the previous lab, you learned how to work with different models and providers. Now, you'll discover one of ADK's most powerful features: the ability to seamlessly combine built-in tools with your own custom functions to create sophisticated, multi-capability agents.

Built-in tools provide ready-to-use functionality for common tasks like web search and data analysis, while custom functions let you add domain-specific logic. Together, they enable you to build agents that can handle complex workflows combining external services with your business logic.

### **What You'll Learn**

- How to use ADK's built-in BigQuery tools for database operations.
- How to create custom function tools for specialized business logic.
- How to combine built-in tools (like Google Search) with custom functions in a single agent.
- How to implement agent-to-agent communication using `AgentTool`.
- Best practices for organizing and structuring multi-tool agents.

### **What You'll Need**

- A computer with Python 3.10 or higher installed.
- A code editor like Visual Studio Code.
- Access to Google Cloud Platform (for BigQuery example).
- A Google account with access to Google AI Studio.
- Basic understanding of SQL (for the BigQuery example).

Let's explore the power of combining different tool types.

## 1. Set Up Your Tools Laboratory

Let's create a dedicated environment for experimenting with different tool combinations.

1. Open your terminal and create a new directory for this lab:

    ```console
    mkdir adk-tools-lab
    cd adk-tools-lab
    ```

2. Create and activate a Python virtual environment:

    ```console
    python3 -m venv .venv
    source .venv/bin/activate
    # On Windows: .venv\Scripts\activate
    ```

3. Install the required dependencies:

    ```console
    pip install google-adk yfinance google-cloud-bigquery google-auth
    ```

4. Create the project structure:

    ```console
    mkdir data_agent
    mkdir news_agent
    touch data_agent/__init__.py
    touch news_agent/__init__.py
    touch .env
    ```

5. Add the required import to both `__init__.py` files:

    ```python
    # data_agent/__init__.py
    from . import agent
    ```

    ```python
    # news_agent/__init__.py
    from . import agent
    ```

6. Set up your environment variables in `.env`:

    ```
    GOOGLE_GENAI_USE_VERTEXAI=0
    GOOGLE_API_KEY=your-google-ai-studio-api-key-here
    ```

## 2. Demo 1: Using Built-in BigQuery Tools

Let's start by building an agent that can query BigQuery databases using ADK's built-in BigQuery toolset. This demonstrates how enterprise-grade tools can be easily integrated into your agents.

### **Configure Google Cloud Authentication**

Before we begin, ensure you have Google Cloud authentication set up:

```console
gcloud auth application-default login
```

### **Create the BigQuery Data Agent**

Create `data_agent/agent.py` with the following code:

```python
import asyncio
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.bigquery import BigQueryCredentialsConfig
from google.adk.tools.bigquery import BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig
from google.adk.tools.bigquery.config import WriteMode
from google.genai import types
import google.auth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define constants for this example agent
AGENT_NAME = "bigquery_agent"
GEMINI_MODEL = "gemini-2.0-flash"

# Define a tool configuration to block any write operations
tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)

# Define a credentials config - using application default credentials
# https://cloud.google.com/docs/authentication/provide-credentials-adc
application_default_credentials, _ = google.auth.default()
credentials_config = BigQueryCredentialsConfig(
    credentials=application_default_credentials
)

# Instantiate a BigQuery toolset
bigquery_toolset = BigQueryToolset(
    credentials_config=credentials_config,
    bigquery_tool_config=tool_config
)

# Agent Definition
root_agent = Agent(
    model=GEMINI_MODEL,
    name=AGENT_NAME,
    description=(
        "Agent to answer questions about BigQuery data and models and execute"
        " SQL queries."
    ),
    instruction="""\
        You are a data science agent with access to several BigQuery tools.
        Make use of those tools to answer the user's questions.

        When users ask about data analysis, use your BigQuery tools to:
        - Query datasets and tables
        - Analyze data patterns
        - Generate insights from the data

        Always explain what you're doing and provide context for your queries.
    """,
    tools=[bigquery_toolset],
)
```

### **Understanding the BigQuery Integration**

Let's break down the key components:

- **`BigQueryToolConfig`**: Configures tool behavior. Here we block write operations for safety.
- **`BigQueryCredentialsConfig`**: Handles authentication using Application Default Credentials.
- **`BigQueryToolset`**: Provides multiple BigQuery-related tools automatically.
- **`WriteMode.BLOCKED`**: Prevents the agent from modifying data, ensuring read-only access.

### **Test Your BigQuery Agent**

1. Start the ADK web interface:

    ```console
    adk web
    ```

2. Open your browser to `http://127.0.0.1:8080` and test with prompts like:
    - `What datasets are available in my project?`
    - `Show me the schema of the public dataset bigquery-public-data.samples.shakespeare`
    - `Count the number of rows in bigquery-public-data.samples.natality`

The agent will use the BigQuery tools to execute these queries and provide detailed results.

## 3. Demo 2: Combining Custom Functions with Built-in Tools

Now let's build a more sophisticated agent that combines Google Search (built-in tool) with custom financial data functions and agent-to-agent communication.

### **Install Additional Dependencies**

```console
pip install yfinance
```

### **Create the AI News Agent**

Create `news_agent/agent.py` with the following code:

```python
from typing import Dict, List
from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
import yfinance as yf
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_financial_context(tickers: List[str]) -> Dict[str, str]:
    """
    Fetches the current stock price and daily change for a list of stock tickers
    using the yfinance library.

    Args:
        tickers: A list of stock market tickers (e.g., ["GOOG", "NVDA"]).

    Returns:
        A dictionary mapping each ticker to its formatted financial data string.
    """
    financial_data: Dict[str, str] = {}
    for ticker_symbol in tickers:
        try:
            # Create a Ticker object
            stock = yf.Ticker(ticker_symbol)

            # Fetch the info dictionary
            info = stock.info

            # Safely access the required data points
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            change_percent = info.get("regularMarketChangePercent")

            if price is not None and change_percent is not None:
                # Format the percentage and the final string
                change_str = f"{change_percent * 100:+.2f}%"
                financial_data[ticker_symbol] = f"${price:.2f} ({change_str})"
            else:
                # Handle cases where the ticker is valid but data is missing
                financial_data[ticker_symbol] = "Price data not available."

        except Exception:
            # This handles invalid tickers or other yfinance errors gracefully
            financial_data[ticker_symbol] = "Invalid Ticker or Data Error"

    return financial_data

# Create a specialized search agent
search_agent = Agent(
    model='gemini-2.0-flash',
    name='SearchAgent',
    description='Specialist agent for performing Google searches',
    instruction="""
    You are a specialist in Google Search. When asked to search for information,
    use your google_search tool to find the most relevant and recent results.
    Focus on providing accurate, up-to-date information.
    """,
    tools=[google_search],
)

# Main agent that orchestrates the workflow
root_agent = Agent(
    name="ai_news_chat_assistant",
    model="gemini-2.0-flash",
    description="AI News Analyst specializing in recent AI news about US-listed companies",
    instruction="""
    You are an AI News Analyst specializing in recent AI news about US-listed companies.
    Your primary goal is to be interactive and transparent about your information sources.

    **Your Workflow:**

    1.  **Clarify First:** If the user makes a general request for news (e.g., "give me AI news"),
        your very first response MUST be to ask for more details.
        *   **Your Response:** "Sure, I can do that. How many news items would you like me to find?"
        *   Wait for their answer before doing anything else.

    2.  **Search and Enrich:** Once the user specifies a number, perform the following steps:
        *   Use the SearchAgent (via AgentTool) to find the requested number of recent AI news articles.
        *   For each article, identify the US-listed company and its stock ticker.
        *   Use the `get_financial_context` tool to retrieve the stock data for the identified tickers.

    3.  **Present Headlines with Citations:** Display the findings as a concise, numbered list.
        You MUST cite your tools.
        *   **Start with:** "Using SearchAgent for news and `get_financial_context` (via yfinance) for market data, here are the top headlines:"
        *   **Format:**
            1.  [Headline 1] - [Company Stock Info]
            2.  [Headline 2] - [Company Stock Info]

    4.  **Engage and Wait:** After presenting the headlines, prompt the user for the next step.
        *   **Your Response:** "Which of these are you interested in? Or should I search for more?"

    5.  **Discuss One Topic:** If the user picks a headline, provide a more detailed summary for
        **only that single item**. Then, re-engage the user.

    **Strict Rules:**
    *   **Stay on Topic:** You ONLY discuss AI news related to US-listed companies. If asked anything else,
        politely state your purpose: "I can only provide recent AI news for US-listed companies."
    *   **Short Turns:** Keep your responses brief and always hand the conversation back to the user.
        Avoid long monologues.
    *   **Cite Your Tools:** Always mention which tools you're using when presenting information.
    """,
    tools=[AgentTool(agent=search_agent), get_financial_context],
)
```

### **Understanding the Multi-Tool Architecture**

This example demonstrates several advanced concepts:

- **Custom Function Tools**: `get_financial_context` provides domain-specific functionality
- **Built-in Tools**: `google_search` provides web search capabilities
- **Agent-as-Tool**: `AgentTool(agent=search_agent)` allows one agent to use another as a tool
- **Workflow Orchestration**: The main agent coordinates between different tool types

### **Test Your Multi-Tool Agent**

1. Restart the web interface to pick up the new agent:

    ```console
    # Stop the current server (Ctrl+C), then restart
    adk web
    ```

2. Select the `ai_news_chat_assistant` from the agent dropdown and test:
    - `Give me AI news`
    - Follow the conversation flow as the agent asks for specifics
    - Provide a number like `3` when asked
    - Watch how it combines search results with financial data

## 4. Tool Integration Patterns

Based on what you've built, here are key patterns for combining tools effectively:

### **Tool Type Categories**

1. **Built-in Tools** (`google_search`, `BigQueryToolset`)
   - Pre-built, production-ready functionality
   - Handle complex external service integration
   - Often include authentication and error handling

2. **Custom Function Tools** (`get_financial_context`)
   - Domain-specific business logic
   - Integration with third-party libraries
   - Custom data processing and formatting

3. **Agent Tools** (`AgentTool`)
   - Specialized sub-agents for specific tasks
   - Modular, reusable components
   - Complex reasoning capabilities

### **Best Practices for Tool Combination**

- **Separation of Concerns**: Each tool should have a focused responsibility
- **Clear Instructions**: Guide the agent on when and how to use each tool
- **Error Handling**: Implement robust error handling in custom functions
- **Authentication**: Use appropriate credential management for each tool type

## 5. Congratulations!

You've successfully built sophisticated agents that combine multiple tool types!

In this lab, you learned to:

✅ **Integrate built-in BigQuery tools** for enterprise data access

✅ **Create custom function tools** for specialized business logic

✅ **Combine built-in and custom tools** in a single agent

✅ **Implement agent-to-agent communication** using AgentTool

✅ **Design effective tool orchestration** workflows

### **Key Takeaways**

- **Tool Diversity**: ADK supports seamless integration of built-in, custom, and agent tools
- **Modular Design**: Break complex functionality into focused, reusable tools
- **Security First**: Use appropriate access controls and authentication for each tool type
- **Clear Instructions**: Guide your agent's tool selection with specific, detailed instructions

### **What's Next?**

Now that you understand tool integration, you're ready to explore:
- **Memory and State Management**: Building agents that remember across conversations
- **Advanced Workflows**: Creating complex multi-step agent processes
- **Production Deployment**: Scaling your tool-enabled agents for real-world use
- **Custom Toolsets**: Building reusable collections of related tools

### **Frequently Asked Questions**

- **Can I mix different authentication methods for different tools?**
  Yes! Each tool can have its own authentication configuration. Built-in tools handle this automatically, while custom tools can implement their own auth logic.

- **How many tools can an agent have?**
  There's no hard limit, but for optimal performance, focus on 5-10 well-designed tools. Too many tools can confuse the agent's decision-making.

- **Can custom tools call other tools?**
  Not directly, but you can use AgentTool to create specialized sub-agents that have access to specific tool sets, enabling hierarchical tool organization.

- **How do I handle tool failures gracefully?**
  Implement proper error handling in custom functions and provide clear error messages. The agent can then decide how to respond to failures (retry, use alternative tools, or inform the user).