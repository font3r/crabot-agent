import datetime

from google.adk.agents import LlmAgent

from currency_agent.agent import currency_agent
from catering_agent.agent import catering_agent


SYSTEM_INSTRUCTION = (
    "You are a helpful assistant for personal use. "
    "Your sole purpouse is to router user intent to other specialized agents. "
    f"Today is {datetime.date.today()}"
)

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="personal_assistant",
    description="An agent that can help with personal needs",
    instruction=SYSTEM_INSTRUCTION,
    sub_agents=[currency_agent, catering_agent],
)
