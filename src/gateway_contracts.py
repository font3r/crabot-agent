from dataclasses import dataclass
from enum import IntEnum
from typing import Any
import json


class GatewayOpcode(IntEnum):
    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    INVALID_SESSION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11

# TODO: migrate to pydantic
@dataclass
class GatewayPayload:
    op: GatewayOpcode
    data: Any = None
    sequence_number: int | None = None
    event_name: str | None = None

    def to_json(self) -> str:
        return json.dumps(
            {
                "op": self.op,
                "d": self.data,
                "s": self.sequence_number,
                "t": self.event_name,
            }
        )

    @staticmethod
    def from_json(data: str) -> GatewayPayload:
        raw = json.loads(data)
        return GatewayPayload(
            op=raw["op"],
            data=raw.get("d"),
            sequence_number=raw.get("s"),
            event_name=raw.get("t"),
        )


@dataclass
class MessageEvent:
    channel_id: str
    content: str
    author_username: str
    author_id: str

    @staticmethod
    def from_payload(d: dict) -> MessageEvent:
        return MessageEvent(
            channel_id=d["channel_id"],
            content=d["content"],
            author_username=d["author"]["username"],
            author_id=d["author"]["id"]
        )


@dataclass
class ReadyEvent:
    session_id: str
    username: str
    discriminator: str

    @staticmethod
    def from_payload(d: dict) -> ReadyEvent:
        return ReadyEvent(
            session_id=d["session_id"],
            username=d["user"]["username"],
            discriminator=d["user"]["discriminator"],
        )


@dataclass
class IdentifyData:
    token: str
    intents: int

    def to_dict(self) -> dict:
        return {
            "token": self.token,
            "intents": self.intents,
            "properties": {
                "os": "linux",
                "browser": "crabot/0.0.1",
                "device": "crabot/0.0.1",
            },
        }
