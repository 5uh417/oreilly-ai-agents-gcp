# Building a Data Analyst Agent with MCP Toolbox and SQLite

In the previous lab, you learned how to connect your ADK agent to general-purpose tools using MCP. Now, we'll dive into a more specialized and powerful use case: data analysis.

You will build an agent that can answer natural language questions about data stored in a local SQLite database. This is a common requirement for building business intelligence bots, report generation assistants, and other data-driven AI applications.

We will use the **MCP Toolbox for Databases**, an open-source MCP server that securely exposes databases as a set of pre-built, production-ready tools. Instead of using Docker, we will build and run the toolbox server directly from its source code. This server handles the complex task of converting a user's natural language question into a SQL query, executing it, and returning the result to the agent.

### **What you'll learn**

- How to prepare a local SQLite database for your agent.
- How to **build and run the MCP Toolbox for Databases from source**.
- How to connect your ADK agent to a network-based MCP server using `SseConnectionParams`.
- How to build an agent that can perform Text-to-SQL queries.

### **What you'll need**

- All prerequisites from the previous lab.
- **The Go programming language toolchain (version 1.21 or later)** installed on your machine. You can follow the official instructions at [go.dev/doc/install](https://go.dev/doc/install).
- **Git** installed on your machine.

## Step 1: Prepare the Local Database

> This step is identical to the previous version. If you have already created the `products.db` file, you can skip to Step 2.

An agent is only as good as the data it can access. Let's create a simple product database in SQLite that our agent will analyze.

1.  In your project's root directory, create a new file named `setup_database.py`.

2.  Add the following Python code to the file. This script will create a SQLite database file named `products.db` and populate it with some sample data.

    ```python
    # setup_database.py
    import sqlite3
    import os

    DB_FILE = "products.db"

    # Delete the database file if it exists to ensure a clean start
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    # Connect to the SQLite database (this will create the file)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create the 'products' table
    cursor.execute("""
    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        stock_quantity INTEGER NOT NULL
    );
    """)

    # Sample product data
    products_data = [
        ('Virtual Reality Headset', 'Electronics', 349.99, 150),
        ('Smart Coffee Maker', 'Home Goods', 89.50, 200),
        ('Wireless Noise-Cancelling Headphones', 'Electronics', 249.99, 300),
        ('Robotic Vacuum Cleaner', 'Home Goods', 199.99, 120),
        ('4K Action Camera', 'Electronics', 175.00, 250),
        ('LED Desk Lamp', 'Home Goods', 45.99, 500),
        ('Portable Bluetooth Speaker', 'Electronics', 65.25, 400)
    ]

    # Insert the data into the table
    cursor.executemany("""
    INSERT INTO products (name, category, price, stock_quantity)
    VALUES (?, ?, ?, ?);
    """, products_data)

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print(f"Database '{DB_FILE}' created and populated successfully.")
    print(f"Absolute path: {os.path.abspath(DB_FILE)}")
    ```

3.  Run the script from your terminal in the `adk-mcp-lab` directory.

    ```console
    python3 setup_database.py
    ```

You should now have a `products.db` file in your project's root directory. This is the data source our agent will query.

## Step 2: Install and Run the MCP Toolbox Server

Instead of using Docker or building from source, we will download the pre-compiled MCP Toolbox binary and configure it for our SQLite database.

1.  Open a **new, separate terminal window**. This terminal will be dedicated to running the MCP Toolbox server.

2.  From your project directory, create a new folder for the MCP Toolbox and navigate into it:

    ```console
    mkdir mcp-toolbox
    cd mcp-toolbox
    ```

3.  Download the MCP Toolbox binary. Choose the appropriate version for your operating system:

    For **macOS (Apple Silicon)**:

    ```console
    export VERSION=0.16.0
    curl -O https://storage.googleapis.com/genai-toolbox/v$VERSION/darwin/arm64/toolbox
    ```

    For **macOS (Intel)**:

    ```console
    export VERSION=0.16.0
    curl -O https://storage.googleapis.com/genai-toolbox/v$VERSION/darwin/amd64/toolbox
    ```

    For **Linux**:

    ```console
    export VERSION=0.16.0
    curl -O https://storage.googleapis.com/genai-toolbox/v$VERSION/linux/amd64/toolbox
    ```

    For **Windows**, download the executable from: `https://storage.googleapis.com/genai-toolbox/v0.16.0/windows/amd64/toolbox.exe`

4.  Make the binary executable:

    ```console
    chmod +x toolbox
    ```

5.  Verify the installation:

    ```console
    ./toolbox -v
    ```

    This should output something like: `toolbox version 0.16.0+binary...`

6.  Create a `tools.yaml` configuration file in the same directory with the following content:

    ```yaml
    sources:
      my-sqlite-source:
        kind: sqlite
        database: ../products.db

    tools:
      search-products-by-category:
        kind: sqlite-sql
        source: my-sqlite-source
        description: Search for products by category
        parameters:
          - name: category
            type: string
            description: The category to search for (e.g., Electronics, Home Goods)
        statement: SELECT * FROM products WHERE category = $1

      get-products-sorted-by-price:
        kind: sqlite-sql
        source: my-sqlite-source
        description: Get products sorted by price (high to low)
        statement: SELECT * FROM products ORDER BY price DESC

      get-low-stock-products:
        kind: sqlite-sql
        source: my-sqlite-source
        description: Get products with low stock (less than 200 units)
        statement: SELECT * FROM products WHERE stock_quantity < 200

      get-average-price-by-category:
        kind: sqlite-sql
        source: my-sqlite-source
        description: Get the average price for a specific category
        parameters:
          - name: category
            type: string
            description: The category to calculate average price for
        statement: SELECT category, AVG(price) as average_price FROM products WHERE category = $1 GROUP BY category

    toolsets:
      my-toolset:
        - search-products-by-category
        - get-products-sorted-by-price
        - get-low-stock-products
        - get-average-price-by-category
    ```

7.  Run the MCP Toolbox server:

    ```console
    ./toolbox --tools-file "tools.yaml" --port 7000
    ```

    > aside positive
    > If port 7000 is already in use, you can use a different port (e.g., 8080). Just remember to update the port in the agent configuration in Step 3.

You will see log output indicating the server has started successfully:

```
INFO "Initialized 1 sources."
INFO "Initialized 0 authServices."
INFO "Initialized 1 tools."
INFO "Initialized 1 toolsets."
INFO "Server ready to serve!"
```

Keep this terminal window open - the server needs to remain running for the agent to connect to it.

## Step 3: Create the Data Analyst Agent

> The agent's code does not need to change at all. Because we are connecting to a network endpoint (`localhost:8080`), the agent is completely unaware of _how_ that server is running—whether in Docker or as a native binary. This is a key benefit of this architecture.

With our database ready and the MCP Toolbox server running, we can now build the agent that will connect to it.

1.  Open your `agents/agent.py` file. We will add a new agent definition to it.

2.  Install the required toolbox package if you haven't already:

    ```console
    pip install toolbox-core
    ```

3.  Append the following code to the end of the file:

    ```python
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
    ```

## Step 4: Run and Test the Agent

Let's see our data analyst in action!

1.  **Ensure the MCP Toolbox server is still running** in one terminal (you should see "Server ready to serve!" message). If it's not running, start it again:

    ```console
    cd mcp-toolbox
    ./toolbox --tools-file "tools.yaml" --port 7000
    ```

2.  In a **different terminal**, go to your project directory and run `adk web`:

    ```console
    adk web
    ```

    > Remember, you must have **two** terminals running simultaneously:
    >
    > - Terminal 1: The `./toolbox` server on port 7000
    > - Terminal 2: The `adk web` server for the agent UI

3.  Open your browser at `http://127.0.0.1:8000`.

4.  Select **`data_analyst_agent`** from the agent dropdown menu.

5.  Try asking it questions about the data:
    - `How many products do we have in stock?`
    - `What is the average price for products in the 'Electronics' category?`
    - `List the names and prices of all products, order them from most expensive to least expensive.`
    - `Which product has the lowest stock quantity?`

The agent will receive your question, use the LLM to generate a SQL query, send that query to the `execute_sql` tool provided by the MCP Toolbox, receive the result from the database, and then formulate a natural language answer for you.

## Congratulations!

You have successfully built a sophisticated data analyst agent without needing Docker. You've learned how to set up and configure the MCP Toolbox server using pre-compiled binaries and have seen firsthand the power of a protocol-based architecture where the client (your agent) is completely decoupled from the server's implementation.

In this lab, you learned to:

- **Install and configure the MCP Toolbox for Databases using pre-compiled binaries**.
- Create a proper `tools.yaml` configuration for SQLite databases.
- Connect an ADK agent to a networked MCP server.
- Provide schema context in your agent's instructions to guide the LLM in generating correct SQL queries.

This pattern is extremely scalable. The same agent code could query a production Postgres or BigQuery database simply by changing the configuration in the `tools.yaml` file—no agent changes required. This demonstrates the true power of decoupling agents from tools via the Model Context Protocol.
