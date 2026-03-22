from pydantic import BaseModel
from typing import Final

import aiohttp

DISCORD_API_GATEWAY: Final = "https://discord.com/api/v10/"

class MessageRequest(BaseModel):
    content: str

class DiscordRestClient:
    def __init__(self, token: str):
        self.token = token
        self.session = aiohttp.ClientSession(base_url=DISCORD_API_GATEWAY)

    async def send_message(self, channel: str, messsage: str):
        response = await self.session.post(
            f"channels/{channel}/messages",
            headers=self._get_http_headers(),
            json=MessageRequest(content=messsage).model_dump(),
        )
        response.raise_for_status()

    def _get_http_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bot {self.token}",
            "User-Agent": "DiscordBot (crabot, 0.0.1)",
        }