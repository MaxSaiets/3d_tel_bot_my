import pytest
from pydantic import ValidationError

from app.schemas.order import OrderCreateIn


def test_order_schema_accepts_valid_payload() -> None:
    payload = OrderCreateIn.model_validate(
        {
            "customer": {
                "name": "Alice",
                "phone": "+3801234567",
                "delivery_info": "Kyiv, Example street 1",
            },
            "items": [{"sku": "hoodie_black", "qty": 1, "price": 39.9}],
            "meta": {"source_code": "yt_video_01", "webapp_version": "v1"},
            "telegram_user_id": 12345,
            "telegram_username": "alice",
        }
    )
    assert payload.customer.name == "Alice"


def test_order_schema_rejects_empty_items() -> None:
    with pytest.raises(ValidationError):
        OrderCreateIn.model_validate(
            {
                "customer": {
                    "name": "Alice",
                    "phone": "+3801234567",
                    "delivery_info": "Kyiv, Example street 1",
                },
                "items": [],
                "meta": {"source_code": "yt_video_01", "webapp_version": "v1"},
                "telegram_user_id": 12345,
            }
        )

