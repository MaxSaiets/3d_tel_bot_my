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


def test_order_schema_accepts_ukrposhta_payload() -> None:
    payload = OrderCreateIn.model_validate(
        {
            "customer": {
                "name": "Alice",
                "phone": "+3801234567",
                "delivery_info": "Укрпошта: 29000, Хмельницький, Відділення №1",
            },
            "items": [{"sku": "cap_white", "qty": 1, "price": 320}],
            "meta": {"source_code": "yt_video_01", "webapp_version": "v5", "delivery_method": "ukrposhta"},
            "ukr_poshta": {
                "postcode": "29000",
                "city": "Хмельницький",
                "postoffice_id": "123",
                "postoffice_name": "29000 Хмельницький",
                "postoffice_address": "вул. Проскурівська, 1",
            },
            "telegram_user_id": 12345,
        }
    )
    assert payload.ukr_poshta is not None
    assert payload.ukr_poshta.postcode == "29000"


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


def test_order_schema_rejects_wrong_price() -> None:
    with pytest.raises(ValidationError):
        OrderCreateIn.model_validate(
            {
                "customer": {
                    "name": "Alice",
                    "phone": "+3801234567",
                    "delivery_info": "Kyiv, Example street 1",
                },
                "items": [{"sku": "hoodie_black", "qty": 1, "price": 39.9}],
                "meta": {"source_code": "yt_video_01", "webapp_version": "v5"},
                "telegram_user_id": 12345,
            }
        )


def test_order_schema_rejects_pickup_below_min_qty() -> None:
    with pytest.raises(ValidationError):
        OrderCreateIn.model_validate(
            {
                "customer": {
                    "name": "Alice",
                    "phone": "+3801234567",
                    "delivery_info": "Самовивіз, Хмельницький",
                },
                "items": [{"sku": "sticker_pack", "qty": 4, "price": 90}],
                "meta": {"source_code": "yt_video_01", "webapp_version": "v5", "delivery_method": "pickup"},
                "pickup": {"city": "Хмельницький"},
                "telegram_user_id": 12345,
            }
        )
