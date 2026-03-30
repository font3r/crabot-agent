import logging
import os
from typing import Any, Final
from aiocache import cached
from aiocache.backends.memory import SimpleMemoryCache
from google.adk.tools import ToolContext

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
    delivery_meal_id: int = Field(alias="deliveryMealId")
    meal_time: str = Field(
        alias="mealName", description="Time of the meal, like breakfast or dinner"
    )
    meal_name: str = Field(alias="menuMealName")
    thermo: str = Field(
        alias="thermo", description="Indicated whether meal has to be heated or no"
    )


class DeliveryMealChange(BaseModel):
    change_options: list[MealChangeOptions] = Field(alias="mealChangeOptions")


class MealChangeOptions(BaseModel):
    details: MealChangeDetails = Field(alias="menuMealDetails")


class MealChangeDetails(BaseModel):
    meal_time: str = Field(alias="mealName")
    meal_name: str = Field(alias="menuMealName")
    thermo: str = Field(alias="thermo")
    diet_calories_meal_id: int = Field(alias="dietCaloriesMealId")


class ApiError(BaseModel):
    title: str
    message: str


@cached(ttl=360, cache=SimpleMemoryCache)
async def get_active_order(tool_context: ToolContext) -> dict[str, Any]:
    """Fetches orders and returns first one (assuming only one active order exists)"""

    if "user:active_order" in tool_context.state:
        return {
            "status": "success",
            "active_order": tool_context.state["user:active_order"],
        }

    logger.info("fetching active orders")
    async with aiohttp.ClientSession(VIKING_API) as session:
        resp = await session.get(
            "company/customer/order/active-ids",
            headers=_get_utility_headers(),
            cookies=await _get_session(),
        )
        if not resp.ok:
            return _handle_error(await resp.text())

        active_order = ActiveOrders.model_validate_json(await resp.text()).root[0]
        tool_context.state["user:active_order"] = active_order

        return {"status": "success", "active_order": active_order}


@cached(ttl=360, cache=SimpleMemoryCache)
async def get_order_details(order_id: int) -> dict[str, Any]:
    """Fetches order details for gived order_id"""
    logger.info(f"fetching order details {order_id}")
    async with aiohttp.ClientSession(VIKING_API) as session:
        resp = await session.get(
            f"company/customer/order/{order_id}",
            headers=_get_utility_headers(),
            cookies=await _get_session(),
        )
        if not resp.ok:
            return _handle_error(await resp.text())

        order_details = OrderDetail.model_validate_json(await resp.text())

        return {"status": "success", "order_details": order_details}


async def get_delivery_menu(delivery_id: int) -> dict[str, Any]:
    logger.info(f"fetching delivery menu {delivery_id}")
    async with aiohttp.ClientSession(VIKING_API) as session:
        resp = await session.get(
            f"company/general/menus/delivery/{delivery_id}/new",
            headers=_get_utility_headers(),
            cookies=await _get_session(),
        )
        if not resp.ok:
            return _handle_error(await resp.text())

        return {
            "status": "success",
            "delivery_menu": DeliveryMenu.model_validate_json(await resp.text()),
        }


async def get_delivery_meal_alternatives(
    order_id: int, delivery_id: int, delivery_meal_id: int
) -> dict[str, Any]:
    logger.info(f"fetching delivery mernu alternatives {delivery_meal_id}")
    async with aiohttp.ClientSession(VIKING_API) as session:
        resp = await session.get(
            f"company/customer/order/{order_id}/deliveries/{delivery_id}/delivery-meals/{delivery_meal_id}/switch",
            headers=_get_utility_headers(),
            cookies=await _get_session(),
        )
        if not resp.ok:
            return _handle_error(await resp.text())

        return {
            "status": "success",
            "delivery_meal_alternatives": DeliveryMealChange.model_validate_json(
                await resp.text()
            ),
        }


async def switch_meal(
    order_id: int, delivery_id: int, delivery_meal_id: int, alternative_meal_id: int
) -> dict[str, Any]:
    """
    Switch meals for new alternative meal

    Args:
        order_id - order id
        delivery_id - delivery/day id
        delivery_meal_id - old meal id e.g. 180106450
        alternative_meal_id - new meal id (diet_calories_meal_id) e.g. 2449

    NOTE:
        alternative meal is specified by providing diet_calories_meal_id,
        it's a different type of identifier than delivery_meal_id
    """

    logger.info(f"switch delivery meal to alternative {alternative_meal_id}")
    async with aiohttp.ClientSession(VIKING_API) as session:
        resp = await session.put(
            f"company/customer/order/{order_id}/deliveries/{delivery_id}/delivery-meals/{delivery_meal_id}/switch",
            params={"amount": 1, "dietCaloriesMealId": alternative_meal_id},
            headers=_get_utility_headers(),
            cookies=await _get_session(),
        )
        if not resp.ok:
            return _handle_error(await resp.text())

        return {"status": "success"}


async def cancel_delivery(order_id: int, delivery_id: int) -> dict[str, Any]:
    logger.info(f"canceling delivery {delivery_id}")
    async with aiohttp.ClientSession(VIKING_API) as session:
        resp = await session.delete(
            f"company/customer/order/{order_id}/deliveries/{delivery_id}/cancel",
            headers=_get_utility_headers(),
            cookies=await _get_session(),
        )
        if not resp.ok:
            return _handle_error(await resp.text())

        return {"status": "success"}


def _get_utility_headers() -> dict[str, str]:
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Company-Id": "kuchniavikinga",
    }


@cached(ttl=360, cache=SimpleMemoryCache)
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


def _handle_error(raw_response: str):
    error = ApiError.model_validate_json(raw_response)
    logger.error(f"api returned error_message: {error.title} - {error.message}")
    return {"status": "error", "error_message": f"{error.title} - {error.message}"}
