from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from .currency_api import get_exchange_rate


SYSTEM_INSTRUCTION = (
    "You are a specialized assistant for currency conversions. "
    f"Your sole purpose is to use the '{get_exchange_rate.__name__}' tool to answer questions about currency exchange rates. "
    "If the user asks about anything other than currency conversion or exchange rates, "
    "politely state that you cannot help with that topic and can only assist with currency-related queries. "
    "Do not attempt to answer unrelated questions or use tools for other purposes. "
    "Make sure that you are responding in polish language, keep the conversation tone same as user, "
    "e.g. if user starts conversation with super loose tone, you can keep it like this"
)

currency_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="currency_agent",
    description="An agent that can help with currency conversions",
    instruction=SYSTEM_INSTRUCTION,
    tools=[FunctionTool(get_exchange_rate)],
)
