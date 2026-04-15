import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal

from aiogram import Bot
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import SessionLocal, get_db_session
from app.repositories.chat import ChatRepository
from app.repositories.users import UserRepository
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


# ── Chat ────────────────────────────────────────────────────────────────────


class ChatMessageIn(BaseModel):
    telegram_user_id: int = Field(ge=1)
    content: str = Field(min_length=1, max_length=2000)


class ChatMessageOut(BaseModel):
    id: int
    content: str
    direction: str  # 'user' | 'admin'
    created_at: str


@router.post("/api/chat", response_model=ChatMessageOut)
async def send_chat_message(
    request: Request,
    payload: ChatMessageIn,
    session: AsyncSession = Depends(get_db_session),
) -> ChatMessageOut:
    """User sends a support message from the WebApp."""
    settings = get_settings()
    user_repo = UserRepository(session)
    chat_repo = ChatRepository(session)

    user = await user_repo.get_by_telegram_user_id(payload.telegram_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Open bot first.")

    msg = await chat_repo.save_message(user.id, payload.content, "user")
    await session.commit()

    # Forward to admin group
    bot: Bot | None = getattr(request.app.state, "bot", None)
    if bot:
        try:
            username = f"@{user.username}" if user.username else "—"
            name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "—"
            await bot.send_message(
                chat_id=settings.admin_group_id,
                text=(
                    f"💬 <b>Чат-повідомлення з магазину</b>\n"
                    f"👤 {name} ({username})\n"
                    f"🆔 <code>{payload.telegram_user_id}</code>\n\n"
                    f"📝 {payload.content}\n\n"
                    f"<i>Відповідайте через бота /reply_{payload.telegram_user_id}</i>"
                ),
                parse_mode="HTML",
            )
        except Exception as exc:
            logger.warning("Failed to forward chat msg to admin", extra={"error": str(exc)})

    return ChatMessageOut(
        id=msg.id,
        content=msg.content,
        direction=msg.direction,
        created_at=msg.created_at.isoformat(),
    )


@router.get("/api/chat", response_model=list[ChatMessageOut])
async def get_chat_history(
    telegram_user_id: int = Query(ge=1),
    since: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> list[ChatMessageOut]:
    """Get chat history (or only new messages if 'since' timestamp provided)."""
    user_repo = UserRepository(session)
    chat_repo = ChatRepository(session)

    user = await user_repo.get_by_telegram_user_id(telegram_user_id)
    if not user:
        return []

    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            since_dt = datetime.fromtimestamp(0, tz=timezone.utc)
        messages = await chat_repo.get_since(user.id, since_dt)
    else:
        messages = await chat_repo.get_history(user.id)

    return [
        ChatMessageOut(id=m.id, content=m.content, direction=m.direction, created_at=m.created_at.isoformat())
        for m in messages
    ]


async def save_admin_chat_reply(telegram_user_id: int, content: str) -> None:
    """Called from admin handler when admin sends a Telegram reply — stores it for WebApp display."""
    try:
        async with SessionLocal() as session:
            user_repo = UserRepository(session)
            chat_repo = ChatRepository(session)
            user = await user_repo.get_by_telegram_user_id(telegram_user_id)
            if user:
                await chat_repo.save_message(user.id, content, "admin")
                await session.commit()
    except Exception as exc:
        logger.warning("Failed to store admin chat reply", extra={"error": str(exc)})
