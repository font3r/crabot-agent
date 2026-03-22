from agents.currency_agent.currency_api import ApiError, get_exchange_rate
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
    else:
        await client.send_message(msg.channel_id, "invalid command")


def mention(user_id: int) -> str:
    return f"<@!{user_id}>"
