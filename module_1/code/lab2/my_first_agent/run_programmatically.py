import asyncio

# Import the agent you defined in main.py
from agent import root_agent
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

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
        print("***starts here***\nmore context: ", event.content, "\n***ends here***\n")
        # 5. We look for the "final response" event to get the agent's output.
        if event.is_final_response() and event.content:
            final_response = event.content.parts[0].text.strip()
            print(final_response)
    print("--- End of Response ---\n")

# Run the asynchronous main function.
if __name__ == "__main__":
    asyncio.run(main())
