# Lab #1: Build Your First Agent with the ADK Python Library

Welcome to the first hands-on lab of the AI Agents with Google’s Agent Development Kit (ADK) Bootcamp! In this session, you'll go from zero to a fully functional AI agent, this time by writing clean, explicit Python code.

While ADK supports a simple YAML configuration for quick starts, the Python library gives you ultimate control and flexibility. We will programmatically define an agent, its behavior, and see it come to life. This code-first approach is the foundation for building advanced agents with custom logic and tools.

### **What You'll Learn**

- How to install the Google Agent Development Kit (ADK).
- How to initialize a code-based agent project using the ADK CLI.
- How to define an agent programmatically using the `LlmAgent` class.
- How to configure your agent's identity, model, and instructions in Python.
- How to connect your agent to Google's Gemini models using an API key.
- How to run and interact with your Python agent using the ADK's built-in web interface.

### **What You'll Need**

- A computer with Python 3.10 or higher installed.
- A code editor like Visual Studio Code.
- Access to a command line/terminal.
- A Google account to generate a free Gemini API key.

Let's start coding.

## 1. Set Up Your Environment

First, let's prepare your local development environment. We'll create a dedicated project folder, set up a Python virtual environment to keep our dependencies isolated, and install the ADK.

1.  Open your terminal and create a new directory for your project. Navigate into it.

    ```console
    mkdir adk-bootcamp-python
    cd adk-bootcamp-python
    ```

2.  Create a Python virtual environment. This is a crucial best practice for managing project dependencies.

    ```console
    python3 -m venv .venv
    ```

3.  Activate the virtual environment. You'll need to do this every time you work on this project in a new terminal session.

    - **macOS / Linux:**
      ```console
      source .venv/bin/activate
      ```
    - **Windows:**
      ````console
      .venv\Scripts\activate
      ```    You'll know it's active when you see `(.venv)` at the beginning of your terminal prompt.
      ````

4.  With your virtual environment active, install the `google-adk` library using pip.

    ```console
    pip install google-adk
    ```

5.  Verify the installation by checking the ADK version.

    ```console
    adk --version
    ```

    You should see an output indicating the installed version number.

> **Tip:** If the `adk` command isn't found, double-check that your virtual environment is active. You should see `(.venv)` in your terminal prompt.

## 2. Get Your Gemini API Key

Your agent needs a brain! The ADK connects to Large Language Models (LLMs) to power your agent's reasoning and conversational abilities. For this lab, we'll use a Gemini model, which you can access for free via an API key from Google AI Studio.

1.  Navigate to [Google AI Studio](https://aistudio.google.com/app/apikey).

2.  Click **"Create API key in new project"**. A new key will be generated for you.

3.  Copy the generated API key and save it somewhere secure for the next step. You will not be able to see it again.

> The free Gemini API key provides a generous rate limit suitable for development and learning. For production applications, you would typically use a Google Cloud project.

## 3. Create Your Agent Project

Now for the magic. We'll use a single ADK command to scaffold a complete, code-based agent project.

1.  From your `adk-bootcamp-python` directory (with the virtual environment still active), run the following command:

    ```console
    adk create --type=code my_first_agent
    ```

2.  The ADK has created a new directory named `my_first_agent`. Let's examine the generated file structure:

    ```console
    my_first_agent/
    ├── .env
    └── main.py
    ```

    - `main.py`: This is the entry point for our agent. We'll write our Python code here to define and configure the agent.
    - `.env`: This is a special file for storing secrets, like our API key.

This clean structure provides the perfect starting point for building a Python-based agent.

## 4. Configure Your Agent

With the project created, let's write the code for our agent and provide it with the key to its brain.

### Define the Agent's Behavior in Python\*\*

1.  Now, open the `my_first_agent/main.py` file. This is where you'll programmatically define your agent's personality and purpose.

2.  Replace the contents of the file with the following Python code. This code instantiates a helpful and creative assistant.

    ```python
    from google.adk.agents import LlmAgent

    # The ADK runtime looks for an object named `root_agent`
    # in main.py to start the application.
    root_agent = LlmAgent(
        name="assistant_agent",
        model="gemini-2.5-flash",
        description="A helpful and creative assistant for a wide range of tasks.",
        instruction="""
    You are a friendly and knowledgeable assistant named Alex.
    Your goal is to help users with their questions clearly and concisely.
    When asked for creative tasks, like writing a poem or a joke, be imaginative!
    """
    )
    ```

Let's break down this code:

- `from google.adk.agents import LlmAgent`: We import the core class for building LLM-powered agents.
- `root_agent = LlmAgent(...)`: We create an instance of the `LlmAgent`. The ADK framework specifically looks for a variable named `root_agent` in `main.py` to serve as the entry point.
- The parameters `name`, `model`, `description`, and `instruction` directly correspond to the YAML fields from the previous lab, but here they are explicit arguments in our code. This gives us the power to dynamically generate these values if needed.

## 5. Run and Interact with Your Agent

The moment of truth! The process to run a code-based agent is identical to a config-based one, highlighting the unified tooling of ADK.

1.  In your terminal, navigate into your newly created agent's directory.

    ```console
    cd my_first_agent
    ```

2.  Run the ADK's built-in web interface.

    ```console
    adk web
    ```

3.  Your terminal will show output indicating that a local server is running, usually at `http://127.0.0.1:8080`.

    ```console
    INFO:     Started server process [12345]
    INFO:     Waiting for application startup.
    INFO:     Application startup complete.
    INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
    ```

4.  Open this URL in your web browser. You will see the same clean, simple chat interface as before.

5.  **Start chatting!** Try the same prompts to see your Python agent in action:
    - `Hello! What's your name?`
    - `What is the main purpose of the Google Agent Development Kit?`
    - `Write a short poem about building an AI agent.`
    - `Tell me a developer joke.`

You are now having a real-time conversation with the AI agent you just built and defined entirely with Python! When you're done, stop the server by pressing `CTRL+C` in your terminal.

## 6. Congratulations!

You've successfully built, configured, and run your first AI agent programmatically using the ADK Python library.

This code-first approach is the gateway to unlocking the full potential of ADK. You learned to:

✅ **Initialize** a code-based agent project with the `adk` CLI.

✅ **Define** an agent's behavior in Python using the `LlmAgent` class.

✅ **Connect** it to a powerful Gemini model with an API key.

✅ **Run and interact** with it through a unified web interface.

This is the foundational workflow for building with ADK in Python. In the upcoming labs, you will build on this foundation to equip your agents with custom tools, orchestrate them into complex workflows, and prepare them for production.

### **Frequently Asked Questions**

- **When should I use Python instead of the YAML Agent Config?**
  Use Python when you need custom logic, dynamic configuration, or want to integrate with other Python libraries. The YAML config is best for simple agents or for non-programmers to assemble agent behaviors.

- **How does the ADK know to run my code?**
  The `adk` command-line tool is designed to look for a `agent.py` file in the current directory and load the `root_agent` object from it.

- **How do I give my agent new skills, like searching the web?**
  You would define Python functions and pass them to the `tools` parameter of the `LlmAgent`. Equipping agents with tools is a key concept and the focus of our next lab.
