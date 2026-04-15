import asyncio
import json
import logging

from aiogram import Router
from aiogram.types import Message
from pydantic import ValidationError

from app.db.session import SessionLocal
from app.schemas.order import OrderCreateIn
from app.services.crm_service import dispatch_event_in_background
from app.services.order_service import OrderService

router = Router(name="webapp")
logger = logging.getLogger(__name__)


@router.message(lambda m: m.web_app_data is not None)
async def handle_webapp_data(message: Message) -> None:
    if message.from_user is None or message.web_app_data is None:
        return

    try:
        raw = json.loads(message.web_app_data.data)
        payload = OrderCreateIn(
            customer=raw["customer"],
            items=raw["items"],
            meta=raw["meta"],
            telegram_user_id=message.from_user.id,
            telegram_username=message.from_user.username,
        )
    except (ValueError, KeyError, ValidationError):
        await message.answer("❌ Помилка даних замовлення. Спробуйте ще раз через магазин.")
        return

    async with SessionLocal() as session:
        service = OrderService(session)
        order_uuid, event_id = await service.create_order(payload)
        asyncio.create_task(dispatch_event_in_background(event_id))

    await message.answer(
        f"✅ Замовлення <b>#{order_uuid[:8]}</b> прийнято!\n\nОчікуйте підтвердження.",
        parse_mode="HTML",
    )
