import asyncio
import logging
from decimal import Decimal

from aiogram import Bot
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import get_db_session
from app.schemas.order import OrderCreateIn, OrderCreateOut
from app.schemas.telegram import HealthResponse, ReadyResponse
from app.services.crm_service import dispatch_event_in_background
from app.services.integrations.nova_poshta import NovaPoshtaClient
from app.services.order_service import OrderService

router = APIRouter()
logger = logging.getLogger(__name__)

# Human-readable product names for admin notifications
_PRODUCT_NAMES: dict[str, str] = {
    "signal_fishing": "🎣 Сигналізатор клювання",
    "hoodie_black":   "🧥 Худі Black",
    "cap_white":      "🧢 Кепка White",
    "sticker_pack":   "🎨 Набір стікерів",
}


def _product_name(sku: str) -> str:
    return _PRODUCT_NAMES.get(sku, sku)


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@router.get("/ready", response_model=ReadyResponse)
async def ready(session: AsyncSession = Depends(get_db_session)) -> ReadyResponse:
    await session.execute(text("SELECT 1"))
    return ReadyResponse()


@router.post("/api/orders", response_model=OrderCreateOut)
async def create_order(
    request: Request, payload: OrderCreateIn, session: AsyncSession = Depends(get_db_session)
) -> OrderCreateOut:
    settings = get_settings()
    service = OrderService(session)
    order_uuid, event_id = await service.create_order(payload)
    asyncio.create_task(dispatch_event_in_background(event_id))

    short_uuid = order_uuid[:8]
    bot: Bot | None = getattr(request.app.state, "bot", None)

    if bot:
        total = sum(Decimal(str(i.price)) * i.qty for i in payload.items)

        # ── Notify customer ──
        try:
            await bot.send_message(
                chat_id=payload.telegram_user_id,
                text=(
                    f"✅ Замовлення <b>#{short_uuid}</b> прийнято!\n\n"
                    f"📦 {payload.customer.delivery_info}\n\n"
                    f"Ми зв'яжемось з вами для підтвердження."
                ),
                parse_mode="HTML",
            )
        except Exception as exc:
            logger.warning(
                "Failed to notify customer",
                extra={"order_id": order_uuid, "error": str(exc)},
            )

        # ── Notify admin group ──
        try:
            username_txt = f"@{payload.telegram_username}" if payload.telegram_username else "—"
            items_txt = "\n".join(
                f"  • {_product_name(i.sku)}  ×{i.qty}  = {int(i.qty * i.price)} ₴"
                for i in payload.items
            )
            dlv_method_map = {
                "nova_poshta": "🚚 Нова Пошта",
                "ukrposhta":   "📦 Укрпошта",
                "pickup":      "🏪 Самовивіз",
            }
            dlv_label = dlv_method_map.get(payload.meta.delivery_method, payload.meta.delivery_method)

            admin_text = (
                f"🛍 <b>НОВЕ ЗАМОВЛЕННЯ #{short_uuid}</b>\n\n"
                f"👤 <b>{payload.customer.name}</b>\n"
                f"📞 {payload.customer.phone}\n"
                f"🔗 {username_txt}  (<code>{payload.telegram_user_id}</code>)\n\n"
                f"📦 <b>Товари:</b>\n{items_txt}\n\n"
                f"💰 <b>Сума: {int(total)} ₴</b>\n\n"
                f"{dlv_label}\n"
                f"📍 {payload.customer.delivery_info}"
            )
            await bot.send_message(
                chat_id=settings.admin_group_id,
                text=admin_text,
                parse_mode="HTML",
            )
        except Exception as exc:
            logger.warning(
                "Failed to notify admin group",
                extra={"order_id": order_uuid, "error": str(exc)},
            )

    return OrderCreateOut(order_uuid=order_uuid, status="accepted")


@router.get("/api/np/cities")
async def search_nova_poshta_cities(query: str = Query(min_length=2, max_length=120)) -> dict:
    """Search Nova Poshta cities. Works whenever NOVA_POSHTA_API_KEY is configured."""
    settings = get_settings()
    client = NovaPoshtaClient(settings)
    try:
        cities = await client.search_cities(query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"items": cities}


@router.get("/api/np/warehouses")
async def search_nova_poshta_warehouses(
    city_ref: str = Query(min_length=10, max_length=64),
    query: str | None = Query(default=None, max_length=120),
) -> dict:
    """Search Nova Poshta warehouses for a given city. Works whenever NOVA_POSHTA_API_KEY is configured."""
    settings = get_settings()
    client = NovaPoshtaClient(settings)
    try:
        warehouses = await client.search_warehouses(city_ref=city_ref, query=query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"items": warehouses}
