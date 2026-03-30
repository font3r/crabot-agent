from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field, RootModel

SYSTEM_INSTRUCTION = (
    "You are a specialized assistant for diet analyzing. Your role is to improve user diet based on his meal preferences. "
    "Your job is to choose best meal from the list that you're going to receive. "
    "Return meal that is going to be the most suitable for user.\n"
    "In your response, clearly state the meal ID and meal name you recommend.\n"
    "\n"
    "User meal preferences:\n"
    "- user does not like shrimps\n"
    "- user prefers shakes/juices for the second breakfast"
)


class MealChangeListSchema(RootModel[list[int]]):
    pass


class MealChangeSchema(BaseModel):
    diet_calories_meal_id: int = Field(description="id of meal alternative")
    meal_name: str = Field(description="name of the meal")


diet_analyzer_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="diet_analyzer_agent",
    description="An agent that can analyze diet and suggest improvements based on user preferations",
    instruction=SYSTEM_INSTRUCTION,
    input_schema=MealChangeListSchema,
)
