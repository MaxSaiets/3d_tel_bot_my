from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.catalog import get_product, get_product_price


class OrderItemIn(BaseModel):
    sku: str = Field(min_length=1, max_length=128)
    qty: int = Field(ge=1, le=999)
    price: Decimal = Field(gt=0)


class CustomerIn(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    phone: str = Field(min_length=5, max_length=64)
    delivery_info: str = Field(min_length=5, max_length=1000)


class NovaPoshtaDeliveryIn(BaseModel):
    city_name: str = Field(min_length=2, max_length=120)
    warehouse_name: str = Field(min_length=2, max_length=200)
    city_ref: str | None = Field(default=None, max_length=64)
    warehouse_ref: str | None = Field(default=None, max_length=64)


class UkrPoshtaDeliveryIn(BaseModel):
    postcode: str = Field(min_length=5, max_length=5, pattern=r"^\d{5}$")
    city: str = Field(min_length=2, max_length=120)
    postoffice_id: str | None = Field(default=None, max_length=32)
    postoffice_name: str = Field(min_length=2, max_length=200)
    postoffice_address: str = Field(min_length=5, max_length=255)


class PickupDeliveryIn(BaseModel):
    city: str = Field(min_length=2, max_length=120)
    note: str | None = Field(default=None, max_length=255)


class MetaIn(BaseModel):
    source_code: str | None = Field(default=None, max_length=128)
    webapp_version: str = Field(min_length=1, max_length=32)
    delivery_method: Literal["nova_poshta", "ukrposhta", "pickup"] = "nova_poshta"


class OrderCreateIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    customer: CustomerIn
    items: list[OrderItemIn] = Field(min_length=1)
    meta: MetaIn
    nova_poshta: NovaPoshtaDeliveryIn | None = None
    ukr_poshta: UkrPoshtaDeliveryIn | None = None
    pickup: PickupDeliveryIn | None = None
    telegram_user_id: int = Field(ge=1)
    telegram_username: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validate_order(self) -> "OrderCreateIn":
        total_qty = 0
        for item in self.items:
            product = get_product(item.sku)
            if product is None:
                raise ValueError(f"Unknown SKU: {item.sku}")

            expected_price = get_product_price(item.sku)
            if expected_price is None or item.price != expected_price:
                raise ValueError(f"Unexpected price for SKU: {item.sku}")
            total_qty += item.qty

        if self.meta.delivery_method == "nova_poshta" and self.nova_poshta is None:
            raise ValueError("Nova Poshta data is required for selected delivery method")

        if self.meta.delivery_method == "ukrposhta" and self.ukr_poshta is None:
            raise ValueError("Ukrposhta data is required for selected delivery method")

        if self.meta.delivery_method == "pickup":
            if self.pickup is None:
                raise ValueError("Pickup data is required for selected delivery method")
            if self.pickup.city.casefold() != "хмельницький":
                raise ValueError("Pickup is available only in Khmelnytskyi")
            if total_qty < 5:
                raise ValueError("Pickup is available only from 5 items")

        return self


class OrderCreateOut(BaseModel):
    order_uuid: str
    status: str
