from app.schemas.order import OrderCreateIn


def test_webapp_v1_contract_is_parsable() -> None:
    payload = {
        "customer": {"name": "Bob", "phone": "+11111111", "delivery_info": "Street, City"},
        "items": [{"sku": "cap_white", "qty": 2, "price": 19.9}],
        "meta": {"source_code": None, "webapp_version": "v1"},
        "nova_poshta": {
            "city_name": "Kyiv",
            "warehouse_name": "Branch 1",
            "city_ref": "city-ref",
            "warehouse_ref": "warehouse-ref",
        },
        "telegram_user_id": 42,
        "telegram_username": "bob",
    }
    parsed = OrderCreateIn.model_validate(payload)
    assert parsed.meta.webapp_version == "v1"
    assert parsed.items[0].qty == 2
