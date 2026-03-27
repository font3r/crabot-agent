import datetime

from google.adk import Runner
from google.adk.models.google_llm import _ResourceExhaustedError
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from gateway_contracts import MessageEvent
from rest_client import DiscordRestClient
from agents.orchestration_agent.agent import root_agent


async def handle_command(client: DiscordRestClient, msg: MessageEvent):
    if msg.author_id != "551147597545340961":  # bot author
        return

    prompt = msg.content[4 : len(msg.content)]
    await client.send_message(msg.channel_id, await run_agent(msg.author_id, prompt))


def mention(user_id: int) -> str:
    return f"<@!{user_id}>"


async def run_agent(user_id: str, prompt: str) -> str:
    session_service = InMemorySessionService()

    session = await session_service.create_session(
        app_name="personal_assistant",
        user_id=user_id,
        session_id=user_id, # move to conversation id that can be somehow stored and mapped to user
        state={"current_date": f"{datetime.date.today()}"},
    )

    runner = Runner(
        agent=root_agent, app_name=session.app_name, session_service=session_service
    )

    message = Content(role="user", parts=[Part(text=prompt)])

    try:
        async for event in runner.run_async(
            user_id=session.user_id,
            session_id=session.id,
            new_message=message,
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    return "".join(p.text or "" for p in event.content.parts)

        return ""
    except _ResourceExhaustedError:
        return "Resource exhaused"
    except Exception as e:
        print(e)
        return f"Something went wrong"
