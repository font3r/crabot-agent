import aiohttp
from pydantic import BaseModel, ValidationError


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message


class ExchangeRateResponse(BaseModel):
    amount: float
    date: str
    base: str
    rates: dict[str, float]


async def get_exchange_rate(
    currency_from: str, currency_to: str
) -> ExchangeRateResponse:
    async with aiohttp.ClientSession("https://api.frankfurter.app/") as session:
        resp = await session.get(
            "latest", params={"from": currency_from, "to": currency_to}
        )
        if resp.status < 200 and resp.status > 299:
            raise ApiError(status=resp.status, message=await resp.text())

        try:
            return ExchangeRateResponse.model_validate_json(await resp.text())
        except ValidationError as e:
            raise ApiError(status=resp.status, message=e.title)
