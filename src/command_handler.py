from datetime import date
import datetime
from uuid import UUID

from google.adk import Runner
from google.adk.models.google_llm import _ResourceExhaustedError
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from agents.catering_agent.viking_api import get_active_orders, get_delivery_menu, get_order_details
from agents.currency_agent.currency_api import ApiError, get_exchange_rate
from agents.currency_agent.agent import root_agent as currency_agent
from agents.catering_agent.agent import root_agent as catering_agent

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
        await client.send_message(msg.channel_id, "ok\nok")
    elif msg.content == "currency":
        try:
            rates = await get_exchange_rate("EUR", "PLN")
            await client.send_message(
                msg.channel_id,
                f"[{rates.date}] 1 {rates.base} -> {rates.rates['PLN']} PLN",
            )
        except ApiError as e:
            await client.send_message(msg.channel_id, f"cannot fetch currency rate")
    elif msg.content.startswith("vai"):
        if msg.author_id != "551147597545340961":
            await client.send_message(msg.channel_id, "nie słucham cie")
        else:
            prompt = msg.content[3 : len(msg.content)]
            await client.send_message(msg.channel_id, await run_catering_agent(msg.author_id, prompt))
    elif msg.content.startswith("ai"):
        prompt = msg.content[3 : len(msg.content)]
        await client.send_message(msg.channel_id, await run_currency_agent(prompt))
    elif msg.content == "viking":
        active_orders = await get_active_orders()
        details = (await get_order_details(active_orders[0]))["order_details"]
        today_delivery = next(
            (delivery for delivery in details.deliveries if delivery.date == date.today()),
            None,
        )

        if today_delivery is None:
            await client.send_message(msg.channel_id, f"missing delivery for today")
        else:
            delivery_menu = (await get_delivery_menu(today_delivery.delivery_id))["delivery_menu"]
            meal_names = "\n".join(
                [f"{i}. {meal.meal_name}" for (i, meal) in enumerate(delivery_menu.menu)]
            )
            await client.send_message(msg.channel_id, meal_names)
    else:
        await client.send_message(msg.channel_id, "invalid command")


def mention(user_id: int) -> str:
    return f"<@!{user_id}>"


async def run_currency_agent(prompt: str) -> str:
    session_service = InMemorySessionService()

    session = await session_service.create_session(
        app_name="currency_app",
        user_id="123",
        session_id="123",
    )

    runner = Runner(
        agent=currency_agent,
        app_name=session.app_name,
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

async def run_catering_agent(user_id: str, prompt: str) -> str:
    session_service = InMemorySessionService()

    session = await session_service.create_session(
        app_name="catering_app",
        user_id=user_id,
        session_id=str(UUID.hex),
        state={"active_order": (await get_active_orders())[0]}
    )

    runner = Runner(
        agent=catering_agent,
        app_name=session.app_name,
        session_service=session_service,
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
        return "Gemini zapchane, kup premium biedaku"
    except Exception as e:
        print(e)
        return f"Coś się wyjebało aok"
