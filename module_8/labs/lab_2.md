# Lab #2: Building a Data Science Agent with Built-in Code Execution

Welcome to Module 8! In this lab, you'll build a data science agent that can execute Python code, analyze datasets, and generate insights using ADK's built-in code execution capabilities.

**Why this matters**: This demonstrates how to create AI agents that can perform complex analytical tasks while maintaining security and reliability through Gemini 2.0's built-in code execution.


## What You'll Need

- Python 3.10+ and terminal access
- Google AI Studio API key (free tier available)
- Completion of previous modules (understanding of ADK agents)

## 1. Set Up Your Data Science Laboratory

Let's create a comprehensive environment for building a data science agent with code execution.

1. Open your terminal and create a new directory for this lab:

    ```console
    mkdir adk-data-science-lab
    cd adk-data-science-lab
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
    touch __init__.py
    touch agent.py
    touch .env
    touch requirements.txt
    ```

5. Set up your environment variables in `.env`:

    ```
    GOOGLE_API_KEY=your-google-ai-studio-api-key-here
    ```

6. Create the requirements file:

    ```
    # requirements.txt
    google-adk
    ```

## 2. Understanding Built-in Code Execution

Before building the agent, let's understand the key concepts:

### **How Built-in Code Execution Works**

The `BuiltInCodeExecutor` leverages **Gemini 2.0's native code execution** rather than local Python environments:

- **Zero Setup**: No local Python environment configuration needed
- **Secure Execution**: Code runs in Google's sandboxed environment
- **Stateful Sessions**: Variables persist across code executions
- **Pre-loaded Libraries**: Common data science libraries are ready to use

### **Key Benefits**

```python
from google.adk.code_executors import BuiltInCodeExecutor

# Simple setup - just pass the executor
agent = Agent(
    model="gemini-2.0-flash-001",  # Must be Gemini 2.0+
    code_executor=BuiltInCodeExecutor(),  # Zero configuration needed
    instruction="You can write and execute Python code for data analysis."
)
```

## 3. Create the Data Science Agent Foundation

### **Create the Base System Instructions**

Create `agent.py` and add the foundational instruction system:

```python
from google.adk.agents.llm_agent import Agent
from google.adk.code_executors.built_in_code_executor import BuiltInCodeExecutor


def base_system_instruction():
    """Returns: data science agent system instruction."""

    return """
    # Guidelines

    **Objective:** Assist the user in achieving their data analysis goals within the context of a Python environment, **with emphasis on avoiding assumptions and ensuring accuracy.** Reaching that goal can involve multiple steps. When you need to generate code, you **don't** need to solve the goal in one go. Only generate the next step at a time.

    **Code Execution:** All code snippets provided will be executed within the environment.

    **Statefulness:** All code snippets are executed and the variables stays in the environment. You NEVER need to re-initialize variables. You NEVER need to reload files. You NEVER need to re-import libraries.

    **Imported Libraries:** The following libraries are ALREADY imported and should NEVER be imported again:

    ```tool_code
    import io
    import math
    import re
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import scipy
    ```

    **Output Visibility:** Always print the output of code execution to visualize results, especially for data exploration and analysis. For example:
      - To look at the shape of a pandas.DataFrame do:
        ```tool_code
        print(df.shape)
        ```
        The output will be presented to you as:
        ```tool_output
        (49, 7)

        ```
      - To display the result of a numerical computation:
        ```tool_code
        x = 10 ** 9 - 12 ** 5
        print(f'{x=}')
        ```
        The output will be presented to you as:
        ```tool_output
        x=999751168

        ```
      - You **never** generate ```tool_output yourself.
      - You can then use this output to decide on next steps.
      - Print just variables (e.g., `print(f'{variable=}')`).

    **No Assumptions:** **Crucially, avoid making assumptions about the nature of the data or column names.** Base findings solely on the data itself. Always use the information obtained from `explore_df` to guide your analysis.

    **Available files:** Only use the files that are available as specified in the list of available files.

    **Data in prompt:** Some queries contain the input data directly in the prompt. You have to parse that data into a pandas DataFrame. ALWAYS parse all the data. NEVER edit the data that are given to you.

    **Answerability:** Some queries may not be answerable with the available data. In those cases, inform the user why you cannot process their query and suggest what type of data would be needed to fulfill their request.
    """
```

## 4. Build the Complete Data Science Agent

### **Add Specialized Analysis Instructions**

Continue building the agent with specific data science capabilities:

```python
root_agent = Agent(
    model="gemini-2.0-flash-001",
    name="data_science_agent",
    instruction=base_system_instruction() + """

    You need to assist the user with their queries by looking at the data and the context in the conversation.
    Your final answer should display the code written, summarize the code and code execution relevant to the user query.

    You should include all pieces of data to answer the user query, such as the table from code execution results.
    If you cannot answer the question directly, you should follow the guidelines above to generate the next step.
    If the question can be answered directly without writing any code, you should do that.
    If you don't have enough data to answer the question, you should ask for clarification from the user.

    You should NEVER install any package on your own like `pip install ...`.
    When plotting trends, you should make sure to sort and order the data by the x-axis.
    """,
    code_executor=BuiltInCodeExecutor(),
)
```

### **Set up Module Exports**

Update `__init__.py`:

```python
from . import agent
```

## 5. Understanding Key Features

### **Automatic Data Parsing**

Your agent intelligently handles different data formats:

- **CSV data in prompts**: Automatically converts to pandas DataFrame
- **File uploads**: Processes using pandas methods
- **Multiple formats**: Handles JSON, CSV, TSV automatically

### **Stateful Execution**

Variables persist across interactions:

```python
# First interaction: Load data
df = pd.read_csv('data.csv')

# Later interaction: Use existing df
df.describe()  # df still available from previous execution!
```

### **Pre-loaded Libraries**

Common data science tools are immediately available:
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **matplotlib**: Plotting and visualization
- **scipy**: Scientific computing
- **math, re, io**: Standard utilities

### **Smart Output Formatting**

The agent ensures all results are visible by automatically printing outputs.

## 6. Testing Your Data Science Agent

### **Start the Agent**

1. From your project directory, start the ADK web interface:

    ```console
    adk web
    ```

2. Open your browser to `http://127.0.0.1:8080` and select your agent from the dropdown.

### **Test 1: Basic Data Analysis**

Try this prompt with inline CSV data:
```
Analyze this sales data:
Date,Product,Sales,Revenue
2024-01-01,Widget A,100,1000
2024-01-02,Widget B,150,1500
2024-01-03,Widget A,120,1200

Calculate total sales and average revenue.
```

**Expected behavior:**
- Agent parses CSV data into a pandas DataFrame
- Calculates total sales and average revenue
- Displays both the code and results
- Shows the data table for verification

### **Test 2: Statistical Analysis**

Try this prompt:
```
Generate 100 random numbers from a normal distribution with mean=50, std=10.
Calculate the mean, median, and standard deviation.
Create a histogram to visualize the distribution.
```

**Expected behavior:**
- Generates random data using numpy
- Calculates statistical measures
- Creates a visualization with matplotlib
- Explains the distribution characteristics

### **Test 3: Multi-step Analysis**

Try this sequence of prompts:
1. "Create a dataset of 50 random temperatures between 20-35°C"
2. "Add a 'comfort_level' column: 'cold' if temp < 22, 'comfortable' if 22-28, 'hot' if > 28"
3. "Show the distribution of comfort levels with a bar chart"

**Expected behavior:**
- Each step builds on the previous one
- Variables remain available across interactions
- Progressive analysis with clear explanations

### **Test 4: Real-world Dataset**

Try this crocodile research data:
```
Here's crocodile research data:
1,Morelet's Crocodile,Crocodylus moreletii,Crocodylidae,Crocodylus,1.9,62,Adult,Male,31-03-2018
2,American Crocodile,Crocodylus acutus,Crocodylidae,Crocodylus,4.09,334.5,Adult,Male,28-01-2015
3,Orinoco Crocodile,Crocodylus intermedius,Crocodylidae,Crocodylus,1.08,118.2,Juvenile,Unknown,07-12-2010

Calculate summary statistics for length and weight, and determine if there's a correlation.
```

## 7. Congratulations!

🎉 You've successfully built a data science agent using ADK's built-in code execution capabilities!
