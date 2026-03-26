import logging
import os
from typing import Any, Final
from aiocache import cached
from aiocache.backends.memory import SimpleMemoryCache

import aiohttp
from pydantic import BaseModel, Field, RootModel

logger = logging.getLogger("crabot." + __name__)

VIKING_API: Final = "https://panel.kuchniavikinga.pl/api/"


class ActiveOrders(RootModel[list[int]]):
    pass


class OrderDetail(BaseModel):
    deliveries: list[Delivery]


class Delivery(BaseModel):
    delivery_id: int = Field(alias="deliveryId")
    date: str


class DeliveryMenu(BaseModel):
    menu: list[DeliveryMenuMeal] = Field(alias="deliveryMenuMeal")


class DeliveryMenuMeal(BaseModel):
    meal_time: str = Field(alias="mealName")
    meal_name: str = Field(alias="menuMealName")
    thermo: str = Field(alias="thermo")


@cached(ttl=180, cache=SimpleMemoryCache)
async def get_active_order() -> dict[str, Any]:
    """Fetches orders and returns first one (assuming only one active order exists)"""

    logger.info("fetching active orders")
    async with aiohttp.ClientSession(VIKING_API) as session:
        resp = await session.get(
            "company/customer/order/active-ids",
            headers=_get_utility_headers(),
            cookies=await _get_session(),
        )
        resp.raise_for_status()

        return {
            "status": "success",
            "active_order": ActiveOrders.model_validate_json(await resp.text()).root[0],
        }


@cached(ttl=180, cache=SimpleMemoryCache)
async def get_order_details(order_id: int) -> dict[str, Any]:
    logger.info(f"fetching order details {order_id}")
    async with aiohttp.ClientSession(VIKING_API) as session:
        resp = await session.get(
            f"company/customer/order/{order_id}",
            headers=_get_utility_headers(),
            cookies=await _get_session(),
        )
        resp.raise_for_status()

        return {
            "status": "success",
            "order_details": OrderDetail.model_validate_json(await resp.text()),
        }


async def get_delivery_menu(delivery_id: int) -> dict[str, Any]:
    logger.info(f"fetching delivery mernu {delivery_id}")
    async with aiohttp.ClientSession(VIKING_API) as session:
        resp = await session.get(
            f"company/general/menus/delivery/{delivery_id}/new",
            headers=_get_utility_headers(),
            cookies=await _get_session(),
        )
        resp.raise_for_status()

        return {
            "status": "success",
            "delivery_menu": DeliveryMenu.model_validate_json(await resp.text()),
        }


def _get_utility_headers() -> dict[str, str]:
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Company-Id": "kuchniavikinga",
    }


@cached(ttl=180, cache=SimpleMemoryCache)
async def _get_session() -> dict[str, str]:
    logger.info("generating API session")
    username = os.getenv("VIKING_USERNAME")
    if username is None:
        raise ValueError("Missing username API credentials")

    password = os.getenv("VIKING_PASSWORD")
    if password is None:
        raise ValueError("Missing password API credentials")

    async with aiohttp.ClientSession(VIKING_API) as session:
        resp = await session.post(
            "auth/login",
            headers=_get_utility_headers(),
            data={"username": username, "password": password},
        )
        resp.raise_for_status()

        return {"SESSION": resp.cookies["SESSION"].value}
