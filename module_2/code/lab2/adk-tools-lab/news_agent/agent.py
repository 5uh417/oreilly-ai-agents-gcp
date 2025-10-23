from typing import Dict, List

import yfinance as yf
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool

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
