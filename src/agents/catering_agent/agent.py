import datetime

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from agents.diet_analyzer_agent.agent import diet_analyzer_agent

from .viking_api import (
    get_active_order,
    get_order_details,
    get_delivery_menu,
    get_delivery_meal_alternatives,
    switch_meal,
    cancel_delivery,
)

SYSTEM_INSTRUCTION = (
    "You are a specialized assistant for catering management. Your role is to provide "
    "details about user catering and its meals, you can also suggest alternatives based on your tools.\n"
    "If user asks questions unrelated to catering/food/diet topics, refuse to answer. Don't show the internal ID's to the user. \n"
    "Once user mentions that he wants to know alternatives or he does not like specific meals, \n"
    "send possible alternatives to 'diet_analyzer_agent'.\n"
    "\n"
    "SESSION STATE (persists across conversations for this user):\n"
    "- active order ID: {user:active_order?} (user's current catering order, do NOT re-fetch if set)\n"
    "\n"
    "Tools behavior:\n"
    f"- {get_active_order.__name__}: returns currently active order, skip if 'active order ID' above is already known.\n"
    f"- {get_order_details.__name__}: returns order details, skip if was called already because order changed once per month.\n"
    f"- {get_delivery_menu.__name__}: returns list of meals for specific delivery/day\n"
    f"- {get_delivery_meal_alternatives.__name__}: returns alternative meals for a specific delivery. User can select one to replace current meal.\n"
    f"- {switch_meal.__name__}: allows to switch meals in the diet, before executing that tool present old meal name and new meal name to the user, then if he confirms, switch meals.\n"
    f"- {cancel_delivery.__name__}: cancels specific delivery, before executing that tool present day of delivery that will be cancelled, if user confirms, cancel delivery"
    "\n"
    f"Today is {datetime.date.today()}"
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
        FunctionTool(switch_meal),
    ],
    sub_agents=[diet_analyzer_agent],
)
