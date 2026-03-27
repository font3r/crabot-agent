import datetime

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from .viking_api import (
    get_active_order,
    get_order_details,
    get_delivery_menu,
    get_delivery_meal_alternatives,
)

SYSTEM_INSTRUCTION = (
    "You are a specialized assistant for catering management. Your role is to provide "
    "details about user catering and it's meals, you can also suggest alternatives based on your tools"
    "If user will asks questions unrelated to catering/food/diet topics, refuse to answer. "
    "Tools description: "
    f"- {get_active_order.__name__} returns currently active order"
    f"- {get_order_details.__name__} returns order details which contains list of deliveries, delivery is given per specific date in yyyy-MM-dd format"
    f"- {get_delivery_menu.__name__} returns list or meals for specific delivery/day"
    f"- {get_delivery_meal_alternatives.__name__} returns list of alternative meals for specific delivery/day. User can chose one of them to replace current one. "
    f"Today is {datetime.date.today()}"  # agent need to now todays date, probably good thing to store in state
)

catering_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="catering_agent",
    description="An agent that can help with catering management, food/diet informations",
    instruction=SYSTEM_INSTRUCTION,
    tools=[
        FunctionTool(get_active_order),
        FunctionTool(get_order_details),
        FunctionTool(get_delivery_menu),
        FunctionTool(get_delivery_meal_alternatives),
    ]
)
