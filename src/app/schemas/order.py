from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


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


class MetaIn(BaseModel):
    source_code: str | None = Field(default=None, max_length=128)
    webapp_version: str = Field(min_length=1, max_length=32)
    delivery_method: str = Field(default="nova_poshta", max_length=32)


class OrderCreateIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    customer: CustomerIn
    items: list[OrderItemIn] = Field(min_length=1)
    meta: MetaIn
    nova_poshta: NovaPoshtaDeliveryIn | None = None
    telegram_user_id: int = Field(ge=1)
    telegram_username: str | None = Field(default=None, max_length=255)


class OrderCreateOut(BaseModel):
    order_uuid: str
    status: str
