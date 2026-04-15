from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.services.crm_service import CrmService


@dataclass
class DummyItem:
    sku: str
    qty: int
    price: Decimal


@dataclass
class DummyOrder:
    id: int
    order_uuid: object
    source_code: str | None
    customer_name: str
    customer_phone: str
    delivery_info: str
    total_amount: Decimal
    created_at: datetime
    items: list[DummyItem]


def test_crm_payload_mapper() -> None:
    service = CrmService.__new__(CrmService)
    order = DummyOrder(
        id=1,
        order_uuid=uuid4(),
        source_code="yt_video_01",
        customer_name="Alice",
        customer_phone="+3801234567",
        delivery_info="Kyiv",
        total_amount=Decimal("39.90"),
        created_at=datetime.now(tz=timezone.utc),
        items=[DummyItem(sku="hoodie_black", qty=1, price=Decimal("39.90"))],
    )

    payload = service.build_payload(order)  # type: ignore[arg-type]
    assert payload["order"]["source_code"] == "yt_video_01"
    assert payload["order"]["items"][0]["sku"] == "hoodie_black"

