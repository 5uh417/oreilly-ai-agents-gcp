# Lab: Deploying ADK Agents to Vertex AI Agent Engine

You've built and locally tested your AI agent with the ADK. Now it's time to take the next step: deploying it to a scalable, production-ready environment.

This codelab provides a hands-on guide to deploying your ADK agent to **Vertex AI Agent Engine**. Agent Engine is a fully managed Google Cloud service designed to run, manage, and scale AI agents. It handles the underlying infrastructure, containerization, and networking, allowing you to focus on building intelligent agent logic.

By the end of this lab, you will have taken a local Python agent and turned it into a secure, queryable endpoint on Google Cloud.

## What you'll learn

- How to structure an ADK project for deployment.
- How to write a Python script to programmatically deploy an agent using the Vertex AI SDK.
- The role of the `AdkApp` wrapper in making an agent compatible with Agent Engine.
- How to test your deployed agent by creating sessions and sending queries from a client script.
- How to clean up your deployed resources to manage costs.

## Prerequisites

To successfully complete this lab, you need the following:

1.  **Google Cloud Project:** An active Google Cloud project with:

    - Billing enabled.
    - The **Vertex AI API** enabled.

2.  **`gcloud` CLI:** The [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) installed and authenticated. Run these commands to log in and set your project:

    ```console
    gcloud auth application-default login
    gcloud config set project YOUR_PROJECT_ID
    ```

    (Replace `YOUR_PROJECT_ID` with your actual project ID).

3.  **Google Cloud Storage (GCS) Bucket:** Agent Engine requires a GCS bucket to stage your code for deployment. You can create one beforehand or let the deployment script create it for you.

4.  **Python Environment:** Python 3.9 - 3.13.

## Step 1: Project Setup

First, let's set up our local project directory and install the necessary libraries.

1.  Create a new directory for the lab and navigate into it.

    ```console
    mkdir -p adk-agent-engine-lab/agents
    cd adk-agent-engine-lab/agents
    ```

2.  Install the required Python packages. The `[adk,agent_engines]` extras are crucial for this lab.

    ```console
    pip install --upgrade --quiet "google-cloud-aiplatform[adk,agent_engines]"
    ```

3.  Create the files for our project. We'll have one file for the agent's logic and another for the deployment script.

    ```console
    touch agent.py __init__.py
    ```

## Step 2: Create the ADK Agent

Now, let's define a simple weather agent. This agent will have a single tool to fetch a weather report for a given city.

1.  Open `agent.py` and add the following code:

    ```python
    # agent.py

    from google.adk.agents import LlmAgent

    def get_weather(city: str) -> dict:
        """Retrieves the current weather for a specified city."""
        print(f"Tool call: get_weather(city='{city}')")
        if city.lower() == "new york":
            return {
                "status": "success",
                "report": "The weather in New York is sunny with a temperature of 25°C.",
            }
        return {"status": "error", "message": f"Weather for '{city}' not found."}


    # The 'root_agent' variable is what the ADK framework discovers.
    root_agent = LlmAgent(
        name="weather_agent",
        model="gemini-2.5-flash",
        description="An agent that can provide weather reports.",
        instruction="You must use the available tools to find an answer.",
        tools=[get_weather],
    )
    ```

2.  Open `__init__.py` and add the following line. This tells Python that the directory is a package and makes the agent discoverable.

    ```python
    # __init__.py

    from . import agent
    ```

## Step 3: Write the Deployment Script

This is the core of the lab. We will write a Python script that uses the Vertex AI SDK to package and deploy our agent to Agent Engine.

Go under `adk-agent-engine-lab` and open `deploy.py` and add the following code:

```python
# deploy.py

import os
import vertexai
from vertexai import agent_engines

# Import the agent we defined in the other file
from agent import root_agent

# Configuration
PROJECT_ID = "your-project-id"
LOCATION = "us-central1"
BUCKET_NAME = "your-bucket-name"
BUCKET_URI = f"gs://{BUCKET_NAME}"

def deploy_agent():
    """Packages and deploys the ADK agent to Vertex AI Agent Engine."""
    print(f"Initializing Vertex AI for project '{PROJECT_ID}' in '{LOCATION}'...")

    # Initialize the Vertex AI SDK
    vertexai.init(
        project=PROJECT_ID,
        location=LOCATION,
        staging_bucket=BUCKET_URI,
    )

    # Wrap the ADK agent in an AdkApp object
    # This makes it compatible with Agent Engine and handles session management.
    print("Wrapping agent in AdkApp...")
    app = agent_engines.AdkApp(
        agent=root_agent,
    )

    # Deploy the application
    # This packages the code, builds a container, and deploys it.
    # This process can take several minutes.
    print("Starting deployment to Agent Engine... This may take 5-10 minutes.")
    remote_app = agent_engines.create(
        agent_engine=app,
        # Tell Agent Engine which libraries to install in the managed environment.
        requirements=["google-cloud-aiplatform[adk,agent_engines]"],
        display_name="My Weather Agent",
        extra_packages=["agents"]
    )

    print("\n--- Deployment finished! ---")
    print(f"Deployed Agent Resource Name: {remote_app.resource_name}")

if __name__ == "__main__":
    deploy_agent()
```

## Step 4: Run the Deployment Script

With your agent and deployment script ready, execute the deployment from your terminal.

```console
python deploy.py
```

You will see output logs as the script initializes the SDK, wraps the agent, and then begins the deployment process. The deployment involves building a container image, pushing it to a registry, and provisioning the service on Agent Engine. Be patient, as this can take **5-10 minutes**.

Upon successful completion, the script will print the unique **Resource Name** for your deployed agent. **Copy this value**, as you will need it in the next step to test the agent.

```console
--- Deployment finished! ---
Deployed Agent Resource Name: projects/1234567890/locations/us-central1/reasoningEngines/9876543210
```

You can also see your deployed agent in the Google Cloud Console by navigating to the [Vertex AI > Agent Engine](https://console.cloud.google.com/vertex-ai/agents/agent-engines) page.

## Step 5: Test the Deployed Agent

Now that the agent is live, let's write a simple client script to interact with it.

1.  Create a new file named `test_deployed_agent.py`.

2.  Add the following code, replacing the placeholder with the **Resource Name** you copied from the previous step.

    ```python
    # test_deployed_agent.py

    import asyncio
    from vertexai import agent_engines

    # TODO: Paste the Resource Name from the deployment script output here
    AGENT_RESOURCE_NAME = "projects/1234567890/locations/us-central1/reasoningEngines/9876543210"

    async def main():
        """Connects to the deployed agent and sends a query."""
        print(f"Connecting to remote agent: {AGENT_RESOURCE_NAME}")

        # Get a client handle to the remote application
        remote_app = agent_engines.get(AGENT_RESOURCE_NAME)

        # Create a remote session to maintain conversation history
        print("Creating new remote session...")
        remote_session = await remote_app.async_create_session(user_id="test-user-123")
        print(f"Session created with ID: {remote_session['id']}")

        # Send a query to the agent
        prompt = "What's the weather like in New York?"
        print(f"\nSending prompt: '{prompt}'")

        print("\n--- Agent Response Stream ---")
        async for event in remote_app.async_stream_query(
            user_id="test-user-123",
            session_id=remote_session["id"],
            message=prompt,
        ):
            print(event)
        print("--- End of Stream ---")

    if __name__ == "__main__":
        asyncio.run(main())
    ```

3.  Run the test script from your terminal:

    ```console
    python test_deployed_agent.py
    ```

You will see the script connect to your agent, create a session, and then print the stream of events as the agent processes your request. This stream includes the initial tool call, the tool's response, and the final text response from the LLM.

```console
--- Agent Response Stream ---
{'role': 'model', 'parts': [{'function_call': {'name': 'get_weather', 'args': {'city': 'New York'}, 'id': '...'}}]}
{'role': 'user', 'parts': [{'function_response': {'name': 'get_weather', 'response': {'report': 'The weather in New York is sunny...', 'status': 'success'}, 'id': '...'}}]}
{'role': 'model', 'parts': [{'text': 'The weather in New York is sunny with a temperature of 25°C.'}]}
--- End of Stream ---
```

## Step 6: Clean Up

To avoid incurring charges, it's important to delete the deployed Agent Engine instance when you are finished.

1.  You can do this programmatically by creating a `cleanup.py` script:

    ```python
    # cleanup.py
    from vertexai import agent_engines

    AGENT_RESOURCE_NAME = "projects/1234567890/locations/us-central1/reasoningEngines/9876543210" # Paste your resource name here

    print(f"Deleting agent: {AGENT_RESOURCE_NAME}")
    remote_app = agent_engines.get(AGENT_RESOURCE_NAME)
    remote_app.delete(force=True) # force=True also deletes child resources like sessions
    print("Agent deleted.")
    ```

    Then run `python cleanup.py`.

Alternatively, you can delete the agent directly from the [Vertex AI > Agent Engine](https://console.cloud.google.com/vertex-ai/agents/agent-engines) page in the Google Cloud Console.

2.  Delete the GCS bucket:

    ```console
    gsutil rm -r $STAGING_BUCKET
    ```

## Congratulations!

You have successfully deployed, tested, and cleaned up a Google ADK agent on Vertex AI Agent Engine!

You've learned the end-to-end workflow of taking an agent from local code to a fully managed, scalable cloud service. You now have the foundational skills to deploy your own custom agents and integrate them into larger applications.

### **Next Steps**

- **CI/CD Automation:** Use a tool like [Agent Starter Pack](https://github.com/GoogleCloudPlatform/agent-starter-pack) to automate this deployment process in a CI/CD pipeline.
- **Observability:** With your agent deployed, explore how to monitor its performance using the built-in tracing, logging, and other observability tools in Google Cloud.
- **Build Complex Agents:** Now that you can deploy agents, try building more sophisticated ones with multiple tools and sequential or parallel logic.
