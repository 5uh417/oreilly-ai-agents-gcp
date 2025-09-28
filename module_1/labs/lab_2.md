# Lab #2: Running Your Agent via CLI and Python Code

Welcome back! In Lab #1, you successfully built your first AI agent using the ADK Python library and interacted with it through the `adk web` interface. Now, it's time to explore more powerful and flexible ways to run your agent.

A web UI is great for demos, but as a developer, you'll often need to test your agent from the command line or integrate it directly into another application. This lab covers two essential execution methods:

1.  **Interactive CLI:** Using the `adk run` command for quick, terminal-based conversations.
2.  **Programmatic Execution:** Using the ADK's `Runner` class in a Python script to control the agent, send messages, and process responses. This is the key to embedding your agent in any application.

### **What You'll Learn**

- How to start an interactive chat session with your agent directly in the terminal.
- The core role of the `Runner` class for programmatic agent control.
- How to set up a `SessionService` to manage conversational state.
- How to write a Python script to send a message to your agent and print its response.
- The concept of `Events` as the data stream returned by the `Runner`.

### **What You'll Need**

- Your completed agent project from Lab #1 (`my_first_agent`).
- A terminal with your Python virtual environment activated.

Let's start running your agent.

## 1. Get Ready: Your Lab #1 Agent

We will continue working with the `my_first_agent` project you created in the previous lab.

1.  First, open your terminal and navigate to the project's root directory.

    ```console
    # Make sure you are in the parent directory, e.g., adk-bootcamp-python
    cd my_first_agent
    ```

2.  Activate the Python virtual environment you created in Lab #1. This is essential to ensure you have `google-adk` installed and available.

        - **macOS / Linux:**
          ```console
          source ../.venv/bin/activate
          ```
        - **Windows:**
          `console

    ..\.venv\Scripts\activate
    `      Your prompt should now be prefixed with`(.venv)`. Your agent code in `main.py`and your API key in`.env` are all set and ready to go.

## 2. Method 1: Interactive Terminal with `adk run`

The `adk run` command is your go-to tool for quick tests and direct conversations with your agent without needing to open a browser. It's a lightweight and efficient way to verify your agent's instructions and behavior.

1.  From the `my_first_agent` directory, simply execute the command:

    ```console
    adk run my_first_agent
    ```

2.  The ADK will load your `root_agent` from `main.py` and present you with an interactive prompt.

    ```console
    >
    ```

3.  Type a message and press `Enter`. The agent will process your input and print its response directly to the terminal, then present a new prompt for your next message.

    **Example Session:**

    ```console
    > Hello! What is your name?
    My name is Alex. It's a pleasure to meet you!
    > Tell me a joke about Python.
    Why did the Python developer get glasses? Because he couldn't C#!
    >
    ```

4.  This creates a continuous conversation where the agent remembers the context of the current session, just like in the web UI.

5.  To exit the interactive session, you can type `exit`, `quit`, or press `CTRL+D`.

The `adk run` command is an indispensable part of the development workflow for rapid iteration and testing.

## 3. Method 2: Programmatic Execution with `Runner`

This is the most powerful way to run your agent. By using the `Runner` class in your own Python script, you can integrate your agent's capabilities into any backend service, automated script, or larger application. You gain full control over the interaction.

### **Create the Runner Script**

1.  Inside your `my_first_agent` directory, create a new file named `run_programmatically.py`.

2.  Open this new file in your code editor and add the following code:

    ```python
    import asyncio

    # Import the agent you defined in main.py
    from agent import root_agent

    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai.types import Content, Part

    from dotenv import load_dotenv

    # Load environment variables from .env file
    load_dotenv()

    # A unique name for your application.
    APP_NAME = "my_first_app"

    # Unique IDs for the user and the conversation session.
    USER_ID = "user_12345"
    SESSION_ID = "session_67890"

    async def main():
        """The main function to run the agent programmatically."""

        # 1. The Runner is the main entry point for running an agent.
        #    It requires the agent to run and a session service to store history.
        runner = Runner(
            agent=root_agent,
            session_service=InMemorySessionService(),
            app_name=APP_NAME
        )

        # 2. A session must be created to hold the conversation's history.
        print(f"Creating session: {SESSION_ID}")
        await runner.session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
        )

        # 3. Prepare the user's message in the required ADK format.
        user_message = Content(parts=[Part(text="Write a haiku about APIs.")])
        print(f"User Message: '{user_message.parts[0].text}'")

        # 4. The `run` method executes the agent and returns a stream of events.
        print("\n--- Agent Response ---")
        final_response = ""
        async for event in runner.run_async(
            user_id=USER_ID, session_id=SESSION_ID, new_message=user_message
        ):
            # 5. We look for the "final response" event to get the agent's output.
            if event.is_final_response() and event.content:
                final_response = event.content.parts[0].text.strip()
                print(final_response)
        print("--- End of Response ---\n")

    # Run the asynchronous main function.
    if __name__ == "__main__":
        asyncio.run(main())
    ```

### **Understand the Code**

Let's break down the key concepts from the script:

1.  **`Runner`**: This is the core class for executing an agent. It orchestrates the entire process: it takes the user's message, passes it to the agent, handles the LLM calls, and manages the session history.
2.  **`SessionService`**: Conversations need to be stored somewhere. `InMemorySessionService` is a simple implementation that stores the conversation history in memory. For production, you would use a persistent service like `VertexAiSessionService`.
3.  **`create_session`**: Before you can have a conversation, you need a place to store it. This method creates a new conversation thread, identified by a unique `session_id`.
4.  **`Content` and `Part`**: This is the standardized structure ADK uses for all messages, ensuring compatibility with different models and tools.
5.  **`runner.run_async` and `Events`**: The `run_async` method doesn't just return a single string. It returns an asynchronous stream of `Event` objects. These events represent every step in the agent's thought process: tool calls, partial text responses (streaming), and the final answer. By iterating through the events and checking `event.is_final_response()`, we reliably capture the complete, final output meant for the user.

### **Execute the Script**

1.  Back in your terminal (in the `my_first_agent` directory), run your new Python script.

    ```console
    python run_programmatically.py
    ```

2.  You will see the output printed directly to your console.

    ```console
    Creating session: session_67890
    User Message: 'Write a haiku about APIs.'

    --- Agent Response ---
    Data flows so fast,
    Connecting worlds, a silent,
    Digital handshake.
    --- End of Response ---
    ```

You have just successfully controlled your AI agent entirely from your own code!

## 4. Congratulations!

You've now mastered the three primary ways to run and interact with an agent in the ADK. This knowledge is fundamental to the entire development lifecycle, from initial creation to final integration.

You learned how to:

✅ **Chat interactively** in your terminal using `adk run` for quick tests.

✅ **Integrate and control** your agent in a Python script using the powerful `Runner` class.

✅ **Understand the roles** of `SessionService`, `Content`, and `Events` in programmatic execution.

You now have a complete toolkit for running your agent in any context. In the next lab, we will move from just talking _to_ our agent to giving it _superpowers_ by equipping it with tools to interact with the outside world.
