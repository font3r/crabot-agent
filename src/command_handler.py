from gateway_contracts import MessageEvent
from rest_client import DiscordRestClient


def is_command(content: str) -> bool:
  return content.startswith("!")


async def handle_command(client: DiscordRestClient, msg: MessageEvent):
  if not is_command(msg.content):
    return
  
  msg.content = msg.content.strip("!")
  
  if msg.content == "zjeb":
    await client.send_message(msg.channel_id, "<@!269132306227265536>")
  elif msg.content == "aha":
    await client.send_message(msg.channel_id, "ok")
  else:
    await client.send_message(msg.channel_id, "invalid command")