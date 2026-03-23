from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from agents.currency_agent.currency_api import ApiError, get_exchange_rate
from agents.currency_agent.agent import root_agent

from gateway_contracts import MessageEvent
from rest_client import DiscordRestClient


def is_command(content: str) -> bool:
    return content.startswith("!")


async def handle_command(client: DiscordRestClient, msg: MessageEvent):
    if not is_command(msg.content):
        return

    msg.content = msg.content.strip("!")

    if msg.content == "zjeb":
        await client.send_message(msg.channel_id, mention(269132306227265536))
    elif msg.content == "aha":
        await client.send_message(msg.channel_id, "ok")
    elif msg.content == "currency":
        try:
            rates = await get_exchange_rate("EUR", "PLN")
            await client.send_message(
                msg.channel_id,
                f"[{rates.date}] 1 {rates.base} -> {rates.rates['PLN']} PLN",
            )
        except ApiError as e:
            await client.send_message(msg.channel_id, f"cannot fetch currency rate")
    elif msg.content.startswith("ai"):
        prompt = msg.content[3:len(msg.content)]
        await client.send_message(msg.channel_id, await run_agent(prompt))
    else:
        await client.send_message(msg.channel_id, "invalid command")


def mention(user_id: int) -> str:
    return f"<@!{user_id}>"

async def run_agent(prompt: str) -> str:
    session_service = InMemorySessionService()

    session = await session_service.create_session(
        app_name="currency_app",
        user_id="123",
        session_id="123",
    )

    runner = Runner(
        agent=root_agent,
        app_name="currency_app",
        session_service=session_service,
    )

    message = Content(role="user", parts=[Part(text=prompt)])

    async for event in runner.run_async(
        user_id=session.user_id,
        session_id=session.id,
        new_message=message,
    ):
        print(f"[AGENT] {event}")

        if event.is_final_response():
            if event.content and event.content.parts:
                return "".join(p.text or "" for p in event.content.parts)

    return ""