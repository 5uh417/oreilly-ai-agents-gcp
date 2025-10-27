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
