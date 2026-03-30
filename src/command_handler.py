import logging

from google.adk import Runner
from google.adk.models.google_llm import _ResourceExhaustedError
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from google.genai.types import Content, Part

from gateway_contracts import MessageEvent
from rest_client import DiscordRestClient
from agents.orchestration_agent.agent import root_agent

logger = logging.getLogger("crabot." + __name__)


async def handle_command(client: DiscordRestClient, msg: MessageEvent):
    if msg.author_id != "551147597545340961":  # bot author
        return

    prompt = msg.content[4 : len(msg.content)]
    await client.send_message(
        msg.channel_id, await run_agent(msg.author_id, msg.channel_id, prompt)
    )


def mention(user_id: int) -> str:
    return f"<@!{user_id}>"


async def run_agent(user_id: str, channel_id: str, prompt: str) -> str:
    session_service = SqliteSessionService("./crabot_datastore.db")

    session = await session_service.get_session(
        app_name="personal_assistant", user_id=user_id, session_id=channel_id
    )

    if session is None:
        session = await session_service.create_session(
            app_name="personal_assistant",
            user_id=user_id,
            session_id=channel_id,
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
        logger.exception("error during communicating with model", e)
        return f"Something went wrong"
