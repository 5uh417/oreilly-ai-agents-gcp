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
