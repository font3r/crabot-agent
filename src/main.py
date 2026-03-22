import asyncio
import os
import aiohttp
from typing import Final

from command_handler import handle_command
from gateway_contracts import (
    GatewayOpcode,
    GatewayPayload,
    IdentifyData,
    MessageEvent,
    ReadyEvent,
)
from rest_client import DiscordRestClient

DISCORD_GATEWAY: Final = "wss://gateway.discord.gg/?v=10&encoding=json"


class DiscordGatewayClient:
    def __init__(self, token: str, api_client: DiscordRestClient):
        self.token = token
        self.heartbeat_interval: int = 41250
        self.session_id: str | None = None
        self.sequence: int | None = None
        self.session: aiohttp.ClientSession
        self.ws: aiohttp.ClientWebSocketResponse | None = None
        self.rest_client: DiscordRestClient = api_client

    async def connect(self):
        async with aiohttp.ClientSession() as session:
            self.session = session
            async with session.ws_connect(DISCORD_GATEWAY) as ws:
                self.ws = ws
                print(f"[CONNECTED] {DISCORD_GATEWAY}")
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        payload = GatewayPayload.from_json(msg.data)
                        await self.handle_message(payload)
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print(f"[ERROR] {ws.exception()}")
                        break
                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        print("[CLOSED] Connection closed")
                        break

    async def handle_message(self, payload: GatewayPayload):
        self.sequence = payload.sequence_number or self.sequence

        if payload.op == GatewayOpcode.HELLO and payload.data:
            self.heartbeat_interval = payload.data["heartbeat_interval"]
            print(f"[S->C=HELLO] heartbeat_interval={self.heartbeat_interval}ms")
            asyncio.create_task(self.heartbeat_loop())
            await self.identify()


        elif payload.op == GatewayOpcode.DISPATCH and payload.data:
            print(f"[S->C=EVENT] {payload.event_name}")
            if payload.event_name == "READY":
                ready = ReadyEvent.from_payload(payload.data)
                self.session_id = ready.session_id
            elif payload.event_name == "MESSAGE_CREATE":
                msg = MessageEvent.from_payload(payload.data)
                print(f"[S->C=MSG] #{msg.channel_id} {msg.author_username}: {msg.content}")
                await handle_command(self.rest_client, msg)

        elif payload.op == GatewayOpcode.INVALID_SESSION:
            print("[ERROR] Invalid session — re-identifying...")
            await asyncio.sleep(2)
            await self.identify()

    async def heartbeat_loop(self):
        while True:
            await asyncio.sleep(self.heartbeat_interval / 1000)
            await self.send(GatewayPayload(op=GatewayOpcode.HEARTBEAT, data=self.sequence))

    async def identify(self):
        identify_data = IdentifyData(token=self.token, intents=33281)
        await self.send(GatewayPayload(op=GatewayOpcode.IDENTIFY, data=identify_data.to_dict()))

    async def send(self, payload: GatewayPayload):
        if self.ws is None:
            raise RuntimeError("WebSocket is not connected")
        await self.ws.send_str(payload.to_json())
        print(f"[C->S={payload.op.name}]")


async def main():
    token = os.getenv("DISCORD_BOT_TOKEN")
    if token is None:
        raise ValueError("Missing bot token from env=DISCORD_BOT_TOKEN")

    await DiscordGatewayClient(token, DiscordRestClient(token)).connect()


if __name__ == "__main__":
    asyncio.run(main())
