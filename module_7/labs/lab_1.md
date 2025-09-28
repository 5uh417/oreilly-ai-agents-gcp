# Lab: Evaluating Agents with the Agent Development Kit (ADK)

In this codelab, you will learn how to implement a robust evaluation workflow for your AI agents using the three primary methods provided by the ADK. Evaluating agents is a critical part of the AgentOps lifecycle, moving beyond simple prototypes to production-ready applications. Unlike traditional software, the probabilistic nature of LLMs means we need to assess not just the final answer, but the agent's entire decision-making process—its _trajectory_.

This lab provides a practical, hands-on guide to ensuring your agent behaves as expected, using a simple home automation agent as our example.

## What you'll learn

By the end of this lab, you will be able to:

- Create evaluation test cases from interactive sessions using the ADK Web UI.
- Run evaluations and analyze pass/fail results directly in the Web UI.
- Debug agent behavior using the powerful Trace view.
- Write and execute programmatic unit tests for your agent using `pytest`.
- Run larger, batch integration tests from the command line using `adk eval`.
- Understand and create the necessary evaluation files (`.test.json`, `.evalset.json`, `test_config.json`).

## Prerequisites

Before we begin, ensure you have the following set up.

### **Environment Setup**

1.  **Install ADK:** If you haven't already, install the Agent Development Kit.

    ```console
    pip install google-adk[eval]
    ```

### **Create the Lab Agent**

We'll use a simple "Home Automation Agent" that can control smart devices.

1.  Create the project directory structure.

    ```console
    mkdir -p home_automation_agent/tests/integration
    cd home_automation_agent
    ```

2.  Create the main agent file `agent.py`. This agent has a single tool to change a device's status.

    ```python
    # home_automation_agent/agent.py

    from google.adk.agents import LlmAgent

    def set_device_status(location: str, device_id: str, status: str) -> dict:
        """Sets the status of a smart home device.

        Args:
            location: The room where the device is located.
            device_id: The unique identifier for the device.
            status: The desired status, either 'ON' or 'OFF'.

        Returns:
            A dictionary confirming the action.
        """
        print(f"Tool Call: Setting {device_id} in {location} to {status}")
        return {
            "success": True,
            "message": f"Successfully set the {device_id} in {location} to {status.lower()}."
        }

    root_agent = LlmAgent(
        model="gemini-2.5-flash",
        name="home_automation_agent",
        description="An agent to control smart devices in a home.",
        instruction="You are a home automation assistant. Use the available tools to fulfill user requests to control devices.",
        tools=[set_device_status],
    )
    ```

3.  Create the package initializer `__init__.py`.

    ```python
    # home_automation_agent/__init__.py
    from . import agent
    ```

4.  Create the .env file with:
    ```
    GOOGLE_GENAI_USE_VERTEXAI=0
    GOOGLE_API_KEY=your-api-key
    ```

Your project is now set up and ready for evaluation.

## Method 1: Interactive Evaluation with the Web UI

The ADK Web UI is the perfect tool for rapid, iterative development and debugging. You can have a conversation with your agent, save it as a test case, and instantly re-run it to validate changes.

### **1. Start the Web UI**

From inside the `home_automation_agent` directory, run:

```console
cd ..
adk web . -v
```

The `-v` flag enables verbose logging, which is helpful for seeing what's happening under the hood. Your browser should open to the ADK development UI.

### **2. Create and Save a Test Case**

First, let's have a conversation with the agent to generate a baseline for our test.

1.  In the chat interface, type: `Turn on the desk lamp in the office.`
2.  The agent should respond with something like: `Successfully set the desk lamp in the office to on.`
3.  Navigate to the **Eval** tab on the right-hand panel.
4.  Click **Create a new eval set** and name it `ui_tests`.
5.  Click the **Add current session** button. You've just saved your conversation as a formal evaluation case.

### **3. Run the Evaluation**

Now, let's run the test case to see if the agent can replicate its previous success.

1.  In the Eval tab, make sure your new test case is checked.
2.  Click the **Run Evaluation** button.
3.  The **EVALUATION METRIC** dialog will appear. For now, leave the default values and click **Start**.
4.  The evaluation will run, and you should see a green **Pass** result in the Evaluation History. This confirms the agent's behavior matched the saved session.

### **4. Analyze a Failure**

Let's intentionally break the test to see what a failure looks like.

1.  In the list of eval cases, click the **Edit** (pencil) icon next to your test case.
2.  In the "Final Response" text box, change the expected text to something incorrect, like: `The office is now dark.`
3.  Save the changes and re-run the evaluation.
4.  This time, the result will be a red **Fail**. Hover your mouse over the "Fail" label. A tooltip will appear showing a side-by-side comparison of the **Actual vs. Expected Output**, highlighting exactly why the test failed (the final response didn't match). This immediate, detailed feedback is invaluable for debugging.

### **5. Debug with the Trace View**

The **Trace** tab provides a detailed, step-by-step log of your agent's execution flow.

1.  Go back to the **Chat** tab and send a new message: `Turn off the kitchen lights.`
2.  Now, click the **Trace** tab on the right.
3.  You will see a series of events. Click on the row for `call_llm` to see the exact request sent to the Gemini model, including the system prompt and tools. Click on the row for `execute_tool` to see the parameters passed to your `set_device_status` function and the result it returned.

This deep introspection is key to understanding and debugging the agent's reasoning process.

## Method 2: Programmatic Evaluation with `pytest` (Unit Tests)

For automated testing, such as in a CI/CD pipeline, you need a programmatic way to run evaluations. `pytest` is the perfect tool for this. We'll create a single, focused test file that acts as a "unit test" for a specific agent behavior.

### **1. Create the Test File**

Create a JSON file that defines our test case. Save this file as `tests/integration/simple.test.json`.

```json
{
  "eval_set_id": "home_automation_agent_unit_tests",
  "name": "Unit tests for basic device control.",
  "eval_cases": [
    {
      "eval_id": "turn_off_bedroom_device",
      "conversation": [
        {
          "user_content": {
            "parts": [{ "text": "Turn off device_2 in the Bedroom." }]
          },
          "final_response": {
            "parts": [
              { "text": "Successfully set the device_2 in the Bedroom to off." }
            ]
          },
          "intermediate_data": {
            "tool_uses": [
              {
                "args": {
                  "location": "Bedroom",
                  "device_id": "device_2",
                  "status": "OFF"
                },
                "name": "set_device_status"
              }
            ]
          }
        }
      ]
    }
  ]
}
```

> This JSON structure defines the user's query (`user_content`), the expected tool trajectory (`tool_uses`), and the expected final answer (`final_response`). The ADK evaluator will run the agent and compare its actual behavior against this "ground truth" data.

### **2. Create the `pytest` Script**

Now, create a Python script to run this test. Save this as `tests/test_evaluation.py`.

```python
# tests/test_evaluation.py

from google.adk.evaluation import AgentEvaluator
import pytest
import os

@pytest.mark.asyncio
async def test_agent_with_single_test_file():
    """Runs a single unit test file against the agent."""
    agent_module_path = os.path.join(os.path.dirname(__file__), "..", 'agent.py')
    test_file_path = os.path.join(
        os.path.dirname(__file__), "integration/simple.test.json"
    )

    await AgentEvaluator.evaluate(
        agent_module=agent_module_path,
        eval_dataset_file_path_or_dir=test_file_path,
    )
```

### **3. Run the Test**

Navigate to the root of your `home_automation_agent` directory and run `pytest`.

```console
pytest
```

You should see a clean, passing result, which gives you a reliable, automated signal that your agent's core functionality is working correctly.

```console
============================= test session starts ==============================
...
collected 1 item

tests/test_evaluation.py .                                               [100%]

============================== 1 passed in 3.21s ===============================
```

## Method 3: CLI Evaluation with `adk eval` (Integration Tests)

The `adk eval` command is designed for running larger batches of evaluations from the command line. This is ideal for integration tests or regression suites that cover multiple conversational flows.

### **1. Create an Evalset File**

This file will contain multiple test cases (sessions). Create `integration.evalset.json` in your root directory.

```json
{
  "eval_set_id": "home_automation_integration_suite",
  "eval_cases": [
    {
      "eval_id": "living_room_light_on",
      "conversation": [
        {
          "user_content": {
            "parts": [
              { "text": "Please turn on the floor lamp in the living room" }
            ]
          },
          "final_response": {
            "parts": [
              {
                "text": "Successfully set the floor lamp in the living room to on."
              }
            ]
          },
          "intermediate_data": {
            "tool_uses": [
              {
                "name": "set_device_status",
                "args": {
                  "location": "living room",
                  "device_id": "floor lamp",
                  "status": "ON"
                }
              }
            ]
          }
        }
      ]
    },
    {
      "eval_id": "kitchen_on_off_sequence",
      "conversation": [
        {
          "user_content": {
            "parts": [{ "text": "Switch on the main light in the kitchen." }]
          },
          "final_response": {
            "parts": [
              {
                "text": "Successfully set the main light in the kitchen to on."
              }
            ]
          },
          "intermediate_data": {
            "tool_uses": [
              {
                "name": "set_device_status",
                "args": {
                  "location": "kitchen",
                  "device_id": "main light",
                  "status": "ON"
                }
              }
            ]
          }
        },
        {
          "user_content": {
            "parts": [{ "text": "Actually, turn it off now." }]
          },
          "final_response": {
            "parts": [
              {
                "text": "Successfully set the main light in the kitchen to off."
              }
            ]
          },
          "intermediate_data": {
            "tool_uses": [
              {
                "name": "set_device_status",
                "args": {
                  "location": "kitchen",
                  "device_id": "main light",
                  "status": "OFF"
                }
              }
            ]
          }
        }
      ]
    }
  ]
}
```

### **2. Create a Configuration File**

This optional file lets us define the pass/fail thresholds. Create `test_config.json` in the root directory.

```json
{
  "criteria": {
    "tool_trajectory_avg_score": 1.0,
    "response_match_score": 0.85
  }
}
```

> `tool_trajectory_avg_score: 1.0` requires a perfect 100% match of the tools used. `response_match_score: 0.85` allows for some variation in the natural language response, using the ROUGE metric for comparison.

### **3. Run the Evaluation from the CLI**

Execute the `adk eval` command, pointing it to your agent directory, the evalset, and the config file.

```console
adk eval . integration.evalset.json --config_file_path=test_config.json --print_detailed_results
```

### **4. Analyze the CLI Output**

The command will run all test cases and print a summary. The `--print_detailed_results` flag provides a turn-by-turn breakdown of each test, showing scores and a diff for any failures.

```console
...
[Eval Summary]
2/2 evals passed.

[Eval Details]
Eval ID: living_room_light_on, Result: Pass
Eval ID: kitchen_on_off_sequence, Result: Pass
```

## Congratulations!

You have successfully implemented a comprehensive evaluation strategy for your ADK agent. You've learned how to:

✅ **Develop interactively** with the Web UI, creating test cases on the fly.
✅ **Automate unit tests** with `pytest` for robust CI/CD integration.
✅ **Run batch integration tests** with `adk eval` to ensure end-to-end quality.

This multi-faceted approach to evaluation is fundamental to building reliable, production-grade AI agents.

### **Next Steps**

- **AgentOps and Observability:** Evaluation tells you if your agent _can_ work correctly. Observability tells you how it _is_ working in production. Explore integrating with tools like **AgentOps**, **Arize AX**, or **Cloud Trace** to monitor real-world performance, track costs, and catch issues.
- **CI/CD Integration:** Integrate your `pytest` script into a GitHub Actions or Cloud Build pipeline to automatically test every code change. The [Agent Starter Pack](https://github.com/GoogleCloudPlatform/agent-starter-pack) provides excellent examples of how to set this up.
- **Advanced Evaluation:** Explore more complex evaluation scenarios, including multi-turn conversations, error handling, and testing for resistance to prompt injection.
