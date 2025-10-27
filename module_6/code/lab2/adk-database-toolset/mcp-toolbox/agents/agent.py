# ... (Keep the code from Lab 1 at the top of the file) ...

# Add these imports at the top of the file with the other imports
from google.adk.agents import Agent
from toolbox_core import ToolboxSyncClient

# Connect to the MCP Toolbox server (use port 7000 or whatever port you used)
toolbox = ToolboxSyncClient("http://127.0.0.1:7000")

# Load the tools from the toolset we defined in tools.yaml
tools = toolbox.load_toolset('my-toolset')

# --- Lab 2: Data Analyst Agent ---
root_agent = Agent(
    model='gemini-2.5-pro',  # Using a more powerful model for better SQL generation
    name='data_analyst_agent',
    description='Agent to answer questions about products in the database',
    instruction="""
    You are a data analyst. Your goal is to help users understand data from a
    product database. You have access to several predefined tools to query the database:

    - search-products-by-category: Search products by category (needs 'category' parameter)
    - get-products-sorted-by-price: Get products sorted by price (high to low)
    - get-low-stock-products: Get products with stock less than 200 units
    - get-average-price-by-category: Get average price for a category (needs 'category' parameter)

    The database contains products with categories: 'Electronics' and 'Home Goods'

    Use the appropriate tool based on the user's question.
    """,
    tools=tools,
)
