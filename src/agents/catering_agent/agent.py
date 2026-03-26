from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from .viking_api import get_active_order, get_order_details, get_delivery_menu

SYSTEM_INSTRUCTION = (
    "You are a specialized assistant for catering management. "
    "If user will asks questions unrelated to catering/food/diet, refuse to answer"
)

catering_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="catering_agent",
    description="An agent that can help with catering management",
    instruction=SYSTEM_INSTRUCTION,
    tools=[
        FunctionTool(get_active_order),
        FunctionTool(get_order_details),
        FunctionTool(get_delivery_menu),
    ],
)
