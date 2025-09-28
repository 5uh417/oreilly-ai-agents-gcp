# Lab: Evaluating ADK Agents with Vertex AI

In the previous lab, you learned how to evaluate agents locally using the ADK's built-in tools. While excellent for development and unit testing, production-grade AgentOps requires a more scalable and centralized solution.

This lab teaches you how to evaluate your ADK agents using the **Vertex AI Evaluation service**. This powerful, managed service allows you to benchmark agent performance, define custom, model-based metrics for quality, and track results over time in a persistent, shareable environment. We will build and evaluate a product research agent, assessing both its tool usage and the quality of its final response.

## What you'll learn

By the end of this lab, you will be able to:

- Build a simple, tool-using ADK agent.
- Create a Python script to run evaluations programmatically.
- Define an evaluation dataset with ground truth data.
- Evaluate an agent's tool usage with a `TrajectorySingleToolUse` metric.
- Evaluate response quality with a custom, model-based `PointwiseMetric`.
- Execute an evaluation task and analyze the summary results.
- Understand where to find detailed results in Google Cloud.

## Prerequisites

Before starting, ensure your environment is correctly configured.

1.  **Google Cloud Project:** You need a Google Cloud project with:

    - Billing enabled.
    - The **Vertex AI API** enabled.

2.  **`gcloud` CLI:** Make sure you have the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) installed and authenticated. Run the following commands in your terminal:

    ```console
    gcloud auth application-default login
    gcloud config set project YOUR_PROJECT_ID
    ```

    Replace `YOUR_PROJECT_ID` with your actual Google Cloud project ID.

3.  **Python Environment:** A Python version between 3.9 and 3.13 is required.

## Step 1: Project Setup and Installation

First, let's set up our project directory and install the necessary Python libraries.

1.  Create a new directory for your project and navigate into it.

    ```console
    mkdir adk-vertex-eval-lab
    cd adk-vertex-eval-lab
    ```

2.  Install the required libraries. We need the ADK itself and the Vertex AI SDK with the `[evaluation]` extra.

    ```console
    pip install --upgrade --quiet "google-adk" "google-cloud-aiplatform[evaluation]"
    ```

3.  Create a new file named `evaluate_agent.py`. We will build our entire evaluation script in this file.

    ```console
    touch evaluate_agent.py
    ```

## Step 2: Build the Evaluation Script

We will now populate the `evaluate_agent.py` script step-by-step. Open this file in your favorite code editor.

### **1. Imports and Configuration**

Add the necessary imports and configure your Google Cloud project details at the top of the script.

> **Important:** Remember to replace the placeholder values for `PROJECT_ID` and `BUCKET_NAME` with your own. The bucket will be created if it doesn't exist.

```python
# evaluate_agent.py

import os
import json
import asyncio
import pandas as pd

import vertexai
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.events import Event
from google.adk.sessions import InMemorySessionService
from google.genai import types
from vertexai.preview.evaluation import EvalTask
from vertexai.preview.evaluation.metrics import (
    PointwiseMetric,
    PointwiseMetricPromptTemplate,
    TrajectorySingleToolUse,
)

# --- Configuration ---
# TODO: Replace with your Google Cloud project ID
PROJECT_ID = "your-gcp-project-id"
# TODO: Replace with a unique GCS bucket name
BUCKET_NAME = "your-unique-gcs-bucket-name"
LOCATION = "us-central1"
BUCKET_URI = f"gs://{BUCKET_NAME}"

# Set environment variables for ADK
os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
os.environ["GOOGLE_CLOUD_LOCATION"] = LOCATION
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

# Configure Vertex AI Experiment name
EXPERIMENT_NAME = "adk-product-agent-evaluation"

print("Configuration loaded.")
```

### **2. Define the Agent and Tools**

Next, define the tools and the ADK agent that we want to evaluate. This agent will act as a product researcher.

```python
# evaluate_agent.py (append to file)

def get_product_details(product_name: str) -> str:
    """Gathers basic details about a product."""
    details = {
        "smartphone": "A cutting-edge smartphone with advanced camera features.",
        "shoes": "High-performance running shoes designed for comfort and speed.",
    }
    return details.get(product_name.lower(), "Product details not found.")

def get_product_price(product_name: str) -> str:
    """Gathers the price of a product."""
    prices = {"smartphone": "500 USD", "shoes": "100 USD"}
    return prices.get(product_name.lower(), "Product price not found.")

def build_agent():
    """Builds and returns the ADK agent."""
    return Agent(
        name="ProductResearchAgent",
        model="gemini-2.5-flash",
        description="An agent that performs product research.",
        instruction="You must use the available tools to answer user questions about product price or details.",
        tools=[get_product_details, get_product_price],
    )

print("Agent definition ready.")
```

### **3. Create an Agent Runner Function**

The Vertex AI Evaluation service needs a standard way to call our agent. We'll create a wrapper function that takes a user prompt, runs the ADK agent, and returns the output in a structured dictionary.

```python
# evaluate_agent.py (append to file)

async def run_agent_async(prompt: str, agent: Agent) -> dict:
    """Runs the ADK agent for a given prompt and parses the output."""
    runner = Runner(
        agent=agent, app_name="eval_app", session_service=InMemorySessionService()
    )
    content = types.Content(role="user", parts=[types.Part(text=prompt)])

    await runner.session_service.create_session(
        app_name="eval_app", user_id="eval_user", session_id="eval_session"
    )

    events = [
        event
        async for event in runner.run_async(
            user_id="eval_user", session_id="eval_session", new_message=content
        )
    ]

    # Parse the event stream to find the final response and tool calls
    final_response = ""
    trajectory = []
    for event in events:
        if not getattr(event, "content", None) or not getattr(
            event.content, "parts", None
        ):
            continue
        for part in event.content.parts:
            if getattr(part, "function_call", None):
                info = {
                    "tool_name": part.function_call.name,
                    "tool_input": dict(part.function_call.args),
                }
                if info not in trajectory:
                    trajectory.append(info)
            if event.content.role == "model" and getattr(part, "text", None):
                final_response = part.text.strip()

    return {
        "response": final_response,
        "predicted_trajectory": json.dumps(trajectory),  # Must be a JSON string
    }

def agent_runner_sync(prompt: str):
    """Synchronous wrapper for the async agent runner."""
    # This is a bit of a trick to run our main async function from the sync context
    # of the evaluation library.
    agent = build_agent()
    result = asyncio.run(run_agent_async(prompt, agent))
    return result

print("Agent runner function defined.")
```

### **4. Define the Evaluation Dataset and Metrics**

Now, define the ground truth data and the metrics we'll use to judge the agent.

```python
# evaluate_agent.py (append to file)

def get_eval_dataset():
    """Creates a pandas DataFrame with evaluation data."""
    eval_data = {
        "prompt": [
            "How much does the smartphone cost?",
            "Tell me about your shoes.",
        ],
        "reference_trajectory": [
            [{"tool_name": "get_product_price", "tool_input": {"product_name": "smartphone"}}],
            [{"tool_name": "get_product_details", "tool_input": {"product_name": "shoes"}}],
        ],
    }
    df = pd.DataFrame(eval_data)
    # The evaluation service expects the trajectory to be a JSON string
    df["reference_trajectory"] = df["reference_trajectory"].apply(json.dumps)
    return df

def get_eval_metrics():
    """Defines the metrics for the evaluation task."""
    # Metric 1: Check if the correct single tool was used.
    tool_metric = TrajectorySingleToolUse(tool_name="get_product_price")

    # Metric 2: A custom, model-based metric to judge response quality.
    criteria = {
        "Follows trajectory": (
            "Evaluate whether the agent's response logically follows from the "
            "sequence of actions it took. Does the response reflect the information "
            "gathered by the tool?"
        )
    }
    rating_rubric = {"1": "Follows trajectory", "0": "Does not follow trajectory"}

    prompt_template = PointwiseMetricPromptTemplate(
        criteria=criteria,
        rating_rubric=rating_rubric,
        input_variables=["prompt", "predicted_trajectory"],
    )

    response_metric = PointwiseMetric(
        metric="response_follows_trajectory",
        metric_prompt_template=prompt_template,
    )

    return [tool_metric, response_metric]

print("Evaluation dataset and metrics defined.")
```

### **5. Define the Main Execution Block**

Finally, create the main block that initializes Vertex AI, creates the GCS bucket, sets up the `EvalTask`, runs it, and prints the results.

```python
# evaluate_agent.py (append to file)

def main():
    """Main function to run the evaluation pipeline."""
    # Initialize Vertex AI
    vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=BUCKET_URI, experiment=EXPERIMENT_NAME)

    # Create GCS bucket if it doesn't exist
    print(f"Checking for GCS bucket: {BUCKET_URI}")
    os.system(f"gsutil ls -b {BUCKET_URI} || gsutil mb -l {LOCATION} {BUCKET_URI}")

    # Get dataset and metrics
    eval_dataset = get_eval_dataset()
    eval_metrics = get_eval_metrics()

    print("\n--- Starting Evaluation Task ---")
    print(f"Dataset has {len(eval_dataset)} rows.")

    # Create the evaluation task
    eval_task = EvalTask(
        dataset=eval_dataset,
        metrics=eval_metrics,
        experiment=EXPERIMENT_NAME
    )

    # Run the evaluation
    eval_result = eval_task.evaluate(
        runnable=agent_runner_sync,
        experiment_run_name="product-agent-run-1"
    )

    print("\n--- Evaluation Complete ---")
    print("Summary Metrics:")
    print(pd.DataFrame(eval_result.summary_metrics.items(), columns=["Metric", "Value"]))


if __name__ == "__main__":
    main()
```

## Step 3: Run the Evaluation Script

Your `evaluate_agent.py` script is now complete. Run it from your terminal.

```console
python evaluate_agent.py
```

The script will:

1.  Initialize Vertex AI and create the GCS bucket.
2.  Start the evaluation task. This may take a few minutes as the service needs to spin up resources and call the LLM for both the agent's logic and the model-based metric evaluation.
3.  Print the summary metrics to your console when finished.

You should see output similar to this:

```console
Configuration loaded.
Agent definition ready.
Agent runner function defined.
Evaluation dataset and metrics defined.
Checking for GCS bucket: gs://your-unique-gcs-bucket-name
Creating gs://your-unique-gcs-bucket-name/...

--- Starting Evaluation Task ---
Dataset has 2 rows.
...
--- Evaluation Complete ---
Summary Metrics:
                                           Metric  Value
0             trajectory_single_tool_use/mean_score    0.5
1                response_follows_trajectory/mean    1.0
...
```

### **Analyzing the Results**

- `trajectory_single_tool_use/mean_score: 0.5`: This makes sense. The metric was configured to _only_ check for `get_product_price`. It was used in one of our two test cases, so the score is 50%.
- `response_follows_trajectory/mean: 1.0`: This indicates that in both cases, the LLM-as-a-judge determined that the agent's final answer was a logical conclusion from the tool it used.

You can find the full, row-by-row results in the GCS bucket you created and see a visual dashboard in the Vertex AI Experiments section of the Google Cloud Console.

## Step 4: Cleanup

To avoid incurring ongoing charges, clean up the resources you created.

1.  **Delete the Vertex AI Experiment:**

    - Navigate to the Vertex AI Experiments in the Cloud Console.
    - Select the experiment named `adk-product-agent-evaluation` and delete it.

2.  **Delete the GCS Bucket:** Run the following command in your terminal:

    ```console
    gsutil rm -r gs://your-unique-gcs-bucket-name
    ```

## Congratulations!

You have successfully evaluated a Google ADK agent using the managed Vertex AI Evaluation service.

You've learned how to go beyond local testing to implement a scalable, programmatic evaluation workflow. You defined ground truth data, assessed specific agent behaviors like tool selection, and even created a custom, model-based metric to judge the qualitative aspect of your agent's responses. This is a critical skill for building robust, reliable, and production-ready AI agents.

### **Next Steps**

- **Automate in CI/CD:** Integrate this evaluation script into a CI/CD pipeline (e.g., Cloud Build, GitHub Actions) to automatically test your agent on every code change.
- **Explore More Metrics:** Dive deeper into the [Vertex AI Evaluation documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/models/determine-eval) to explore other pre-built metrics for safety, faithfulness, summarization, and more.
- **Expand Your Dataset:** A larger and more diverse evaluation dataset will give you higher confidence in your agent's performance across a wider range of user inputs.
