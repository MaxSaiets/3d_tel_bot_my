import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
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


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@router.get("/ready", response_model=ReadyResponse)
async def ready(session: AsyncSession = Depends(get_db_session)) -> ReadyResponse:
    await session.execute(text("SELECT 1"))
    return ReadyResponse()


@router.post("/api/orders", response_model=OrderCreateOut)
async def create_order(
    payload: OrderCreateIn, session: AsyncSession = Depends(get_db_session)
) -> OrderCreateOut:
    service = OrderService(session)
    order_uuid, event_id = await service.create_order(payload)
    asyncio.create_task(dispatch_event_in_background(event_id))
    return OrderCreateOut(order_uuid=order_uuid, status="accepted")


@router.get("/api/np/cities")
async def search_nova_poshta_cities(query: str = Query(min_length=2, max_length=120)) -> dict:
    settings = get_settings()
    if not settings.nova_poshta_enabled:
        raise HTTPException(status_code=400, detail="Nova Poshta integration is disabled")
    client = NovaPoshtaClient(settings)
    cities = await client.search_cities(query)
    return {"items": cities}


@router.get("/api/np/warehouses")
async def search_nova_poshta_warehouses(
    city_ref: str = Query(min_length=10, max_length=64),
    query: str | None = Query(default=None, max_length=120),
) -> dict:
    settings = get_settings()
    if not settings.nova_poshta_enabled:
        raise HTTPException(status_code=400, detail="Nova Poshta integration is disabled")
    client = NovaPoshtaClient(settings)
    warehouses = await client.search_warehouses(city_ref=city_ref, query=query)
    return {"items": warehouses}
