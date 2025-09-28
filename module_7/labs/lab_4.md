# Lab: Observability for ADK Agents on Agent Engine with Cloud Trace

Once an agent is deployed, how do you know what it's _really_ doing? When a user reports a slow or incorrect response, how do you debug the complex chain of LLM calls, tool executions, and internal logic?

The answer is **observability**. This codelab focuses on a cornerstone of observability: **distributed tracing**. You will learn how to enable tracing for your ADK agent on Vertex AI Agent Engine with a single line of code. We will then query our deployed agent and dive into **Google Cloud Trace** to visualize its entire execution path, from the initial user request to the final response.

## What you'll learn

- Why distributed tracing is essential for debugging AI agents.
- How to enable automatic tracing when deploying an agent to Agent Engine.
- How to generate trace data by sending requests to your deployed agent.
- How to navigate the Google Cloud Trace Explorer to find and analyze your agent's traces.
- How to interpret the trace "waterfall" diagram to understand your agent's performance and behavior.

## Prerequisites

Ensure your environment is correctly configured before you begin.

1.  **Google Cloud Project:** An active Google Cloud project with:

    - Billing enabled.
    - The **Vertex AI API** and **Cloud Trace API** enabled.

2.  **`gcloud` CLI:** The [Google Cloud CLI](httpss://cloud.google.com/sdk/docs/install) installed and authenticated. Run the following commands:

    ```console
    gcloud auth application-default login
    gcloud config set project YOUR_PROJECT_ID
    gcloud services enable aiplatform.googleapis.com cloudtrace.googleapis.com
    ```

    (Replace `YOUR_PROJECT_ID` with your actual project ID).

3.  **Google Cloud Storage (GCS) Bucket:** You need a GCS bucket for staging deployment files.

4.  **Python Environment:** Python 3.9 - 3.13.

## Step 1: Project Setup

Let's prepare our local workspace.

1.  Create a new directory for the lab and enter it.

    ```console
    mkdir -p adk-tracing-lab/agents
    cd adk-tracing-lab/agents
    ```

2.  Install the necessary libraries from PyPI.

    ```console
    pip install --upgrade --quiet "google-cloud-aiplatform[adk,agent_engines]"
    ```

3.  Create the files for our project. We'll have one file for the agent's logic and another for the deployment script.

    ```console
    touch agent.py __init__.py
    ```

## Step 2: Create the ADK Agent

We'll use the same simple weather agent from the previous lab. Its single-tool structure is perfect for demonstrating a clean, easy-to-understand trace.

Open `agent.py` and add the following code:

```python
# agent.py

from google.adk.agents import LlmAgent

def get_weather(city: str) -> dict:
    """Retrieves the current weather for a specified city."""
    print(f"Tool call: get_weather(city='{city}')")
    if city.lower() == "paris":
        return {
            "status": "success",
            "report": "The weather in Paris is cloudy with a temperature of 18°C.",
        }
    return {"status": "error", "message": f"Weather for '{city}' not found."}

root_agent = LlmAgent(
    name="weather_agent_traced",
    model="gemini-2.5-flash",
    description="An agent that can provide weather reports and is traced.",
    instruction="You must use the available tools to find an answer.",
    tools=[get_weather],
)
```

Next, open `__init__.py` and add this line to make the agent discoverable as a Python package:

```python
# __init__.py

from . import agent
```

## Step 3: Deploy the Agent with Tracing Enabled

Duration: 15:00

This is the key step of the lab. We will write a deployment script that is nearly identical to a standard deployment, but with one critical change.

Go under `adk-agent-engine-lab` and open `deploy_with_tracing.py` and add the following code:

```python
# deploy_with_tracing.py

import os
import vertexai
from vertexai import agent_engines
from agent import root_agent

# Configuration
PROJECT_ID = "your-project-id"
LOCATION = "us-central1"
BUCKET_NAME = "your-bucket-name"
BUCKET_URI = f"gs://{BUCKET_NAME}"

def deploy_agent():
    """Deploys the ADK agent with Cloud Trace enabled."""
    print(f"Initializing Vertex AI for project '{PROJECT_ID}'...")
    vertexai.init(
        project=PROJECT_ID,
        location=LOCATION,
        staging_bucket=BUCKET_URI,
    )

    print("Wrapping agent in AdkApp with tracing enabled...")

    # --- THIS IS THE KEY ---
    # The `enable_tracing=True` flag automatically configures the agent
    # to send OpenTelemetry traces to Google Cloud Trace.
    app = agent_engines.AdkApp(
        agent=root_agent,
        enable_tracing=True,
    )
    # -----------------------

    print("Starting deployment... This may take 5-10 minutes.")
    remote_app = agent_engines.create(
        agent_engine=app,
        requirements=["google-cloud-aiplatform[adk,agent_engines]"],
        display_name="Traced Weather Agent",
        extra_packages=["agents"]
    )

    print("\n--- Deployment finished! ---")
    print(f"Deployed Agent Resource Name: {remote_app.resource_name}")

if __name__ == "__main__":
    deploy_agent()
```

> **What does `enable_tracing=True` do?**
>
> This simple flag instructs the Agent Engine to automatically configure the industry-standard [OpenTelemetry](https://opentelemetry.io/) framework within your agent's managed environment. It sets up the necessary exporters and context propagation to capture detailed timing and metadata for each step of your agent's execution and securely sends this data to your project's Google Cloud Trace service.

Now, run the script from your terminal:

```console
python deploy_with_tracing.py
```

Wait for the deployment to complete. It can take several minutes. Once finished, **copy the output `Deployed Agent Resource Name`**. You will need it for the next step.

## Step 4: Generate Traces by Querying the Agent

An observability system is only useful if it has data. Let's send a request to our newly deployed agent to generate a trace.

1.  Open `query_agent.py`.

2.  Add the following code, pasting the **Resource Name** from the previous step.

    ```python
    # query_agent.py

    import asyncio
    from vertexai import agent_engines

    # TODO: Paste the Resource Name from the deployment script output here
    AGENT_RESOURCE_NAME = "projects/your-gcp-project-id/locations/us-central1/reasoningEngines/1234567890"

    async def main():
        """Connects to the deployed agent and sends a query to generate a trace."""
        print(f"Connecting to remote agent: {AGENT_RESOURCE_NAME}")
        remote_app = agent_engines.get(AGENT_RESOURCE_NAME)

        print("Creating new remote session...")
        session = await remote_app.async_create_session(user_id="trace-user-001")

        prompt = "How is the weather in Paris?"
        print(f"Sending prompt: '{prompt}'")

        final_response = ""
        async for event in remote_app.async_stream_query(
            user_id="trace-user-001",
            session_id=session["id"],
            message=prompt,
        ):
            print(event)
        print("\nTrace data has been sent to Google Cloud Trace.")


    if __name__ == "__main__":
        asyncio.run(main())
    ```

3.  Run the script to send a request.

    ```console
    python query_agent.py
    ```

You've now successfully executed your remote agent, and in the background, a detailed trace of that execution has been sent to Google Cloud.

## Step 5: Inspect Traces in Cloud Trace Explorer

Now for the payoff. Let's visualize what our agent did.

1.  Open the Google Cloud Trace Explorer in your browser

2.  It may take a minute or two for the trace data to be ingested and become visible. You should see a new entry in the trace list. Click on it to open the detailed view.

3.  You will now see a **waterfall diagram**. This is a timeline of your agent's execution, broken down into distinct operations called "spans."

### **Interpreting the Trace**

- **Parent Span (`/v1/...:query`)**: This is the top-level span representing the entire request to your deployed agent endpoint. Its duration is the total time the user waited for a response.
- **`agent_run`**: This span represents the execution of your ADK agent's logic.
- **`call_llm` (Child of `agent_run`)**: This shows the exact time spent on the network call to the Gemini model. Clicking this span reveals metadata like the model name.
- **`execute_tool` (Child of `agent_run`)**: This shows the execution of your `get_weather` function. It captures how long your custom tool code took to run.

This hierarchical view is invaluable. If your agent were slow, you could immediately see whether the bottleneck was in the LLM call, one of your tools, or the agent's own overhead.

## Step 6: Clean Up

To avoid ongoing costs, delete the deployed agent and the GCS bucket.

1.  Delete the Agent Engine instance from the Cloud Console or by running a cleanup script.

2.  Delete the GCS bucket:

    ```console
    gsutil rm -r $STAGING_BUCKET
    ```

## Congratulations!

You have successfully enabled and inspected production-grade observability for a deployed ADK agent.

You now have the power to look inside the "black box" of your agent's execution in the cloud. By simply adding `enable_tracing=True`, you unlocked a powerful debugging and performance analysis tool. This ability to trace the flow of requests through LLMs and tools is a fundamental practice in the AgentOps lifecycle and is critical for building reliable, efficient, and maintainable AI systems.
