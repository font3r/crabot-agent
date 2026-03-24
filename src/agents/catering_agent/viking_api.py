import datetime
import logging
import os
from typing import Any, Final

import aiohttp
from pydantic import BaseModel, Field, RootModel

logger = logging.getLogger('crabot.' + __name__)

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


async def get_active_orders() -> list[int]:
    logger.info("fetching active orders")
    async with aiohttp.ClientSession(VIKING_API) as session:
        resp = await session.get(
            "company/customer/order/active-ids", headers=_get_headers()
        )
        resp.raise_for_status()

        return ActiveOrders.model_validate_json(await resp.text()).root 


async def get_order_details(order_id: int) -> dict[str, Any]:
    logger.info(f"fetching order details {order_id}")
    async with aiohttp.ClientSession(VIKING_API) as session:
        resp = await session.get(
            f"company/customer/order/{order_id}", headers=_get_headers()
        )
        resp.raise_for_status()

        return {
            "status": "success",
            "order_details": OrderDetail.model_validate_json(await resp.text())
        }


async def get_delivery_menu(delivery_id: int) -> dict[str, Any]:
    logger.info(f"fetching delivery mernu {delivery_id}")
    async with aiohttp.ClientSession(VIKING_API) as session:
        resp = await session.get(
            f"company/general/menus/delivery/{delivery_id}/new", headers=_get_headers()
        )
        resp.raise_for_status()

        return {
            "status": "success",
            "delivery_menu": DeliveryMenu.model_validate_json(await resp.text())
        }


def _get_headers() -> dict[str, str]:
    session = os.getenv("VIKING_SESSION")
    if session is None:
        raise ValueError("Missing session env=VIKING_SESSION")

    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Cookie": f"SESSION={session}",
        "Company-Id": "kuchniavikinga",
    }
