import asyncio
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import CrmEventStatus, Order
from app.db.session import SessionLocal
from app.logging import extra_fields
from app.repositories.crm import CrmRepository
from app.schemas.order import OrderCreateIn
from app.services.integrations.espocrm import EspoCrmClient
from app.services.integrations.nova_poshta import NovaPoshtaClient, NovaPoshtaCreateTtnInput

logger = logging.getLogger(__name__)


class CrmService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()
        self.repo = CrmRepository(session)
        self.espo_client = EspoCrmClient(self.settings)
        self.nova_poshta_client = NovaPoshtaClient(self.settings)

    def build_payload(self, order: Order, request_payload: OrderCreateIn | None = None) -> dict:
        extra_nova_poshta: dict[str, Any] = {}
        if request_payload and request_payload.nova_poshta:
            extra_nova_poshta = request_payload.nova_poshta.model_dump(exclude_none=True)

        return {
            "idempotency_key": str(order.order_uuid),
            "order": {
                "order_uuid": str(order.order_uuid),
                "source_code": order.source_code,
                "customer": {
                    "name": order.customer_name,
                    "phone": order.customer_phone,
                    "delivery_info": order.delivery_info,
                },
                "items": [{"sku": item.sku, "qty": item.qty, "price": float(item.price)} for item in order.items],
                "total_amount": float(order.total_amount),
                "created_at": order.created_at.isoformat(),
            },
            "nova_poshta": extra_nova_poshta,
        }

    async def enqueue_order_event(self, order: Order, request_payload: OrderCreateIn | None = None) -> int:
        payload = self.build_payload(order, request_payload=request_payload)
        event = await self.repo.create_pending_event(order.id, payload)
        return event.id

    async def _try_create_nova_poshta_ttn(self, payload: dict) -> None:
        if not self.settings.nova_poshta_enabled or not self.settings.nova_poshta_auto_create_ttn:
            return

        np_data = payload.get("nova_poshta") or {}
        city_ref = np_data.get("city_ref")
        warehouse_ref = np_data.get("warehouse_ref")
        if not city_ref or not warehouse_ref:
            return

        order = payload["order"]
        ttn_input = NovaPoshtaCreateTtnInput(
            city_ref=city_ref,
            warehouse_ref=warehouse_ref,
            recipient_name=order["customer"]["name"],
            recipient_phone=order["customer"]["phone"],
            cost=float(order["total_amount"]),
        )
        ttn = await self.nova_poshta_client.create_ttn(ttn_input)
        payload.setdefault("nova_poshta", {})
        payload["nova_poshta"]["tracking_number"] = ttn.get("IntDocNumber")
        payload["nova_poshta"]["tracking_ref"] = ttn.get("Ref")

    async def dispatch_event(self, event_id: int) -> None:
        event = await self.repo.get_event(event_id)
        if not event:
            return

        backoffs = [1, 2, 4]

        for attempt in range(1, self.settings.crm_max_retries + 1):
            event.attempts = attempt
            try:
                await self._try_create_nova_poshta_ttn(event.payload)
                if self.settings.crm_provider == "espocrm":
                    crm_response = await self.espo_client.create_order_entity(event.payload)
                else:
                    raise ValueError(f"Unsupported CRM_PROVIDER: {self.settings.crm_provider}")

                event.status = CrmEventStatus.sent
                event.last_error = None
                event.payload["crm_response"] = crm_response
                await self.session.commit()
                logger.info("CRM event sent", extra=extra_fields(order_id=event.order_id))
                return
            except Exception as exc:  # noqa: BLE001
                event.last_error = str(exc)
                logger.warning(
                    "CRM event attempt failed",
                    extra=extra_fields(order_id=event.order_id, request_id=f"crm-{event.id}-{attempt}"),
                )
                if attempt < self.settings.crm_max_retries:
                    await asyncio.sleep(backoffs[min(attempt - 1, len(backoffs) - 1)])

        event.status = CrmEventStatus.failed
        await self.session.commit()
        logger.error("CRM event failed", extra=extra_fields(order_id=event.order_id))


async def dispatch_event_in_background(event_id: int) -> None:
    async with SessionLocal() as session:
        service = CrmService(session)
        await service.dispatch_event(event_id)
