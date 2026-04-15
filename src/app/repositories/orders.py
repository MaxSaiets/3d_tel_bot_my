from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Order, OrderItem
from app.schemas.order import OrderCreateIn


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_order(self, user_id: int, source_code: str | None, payload: OrderCreateIn) -> Order:
        total = sum(item.price * item.qty for item in payload.items)
        order = Order(
            user_id=user_id,
            source_code=source_code,
            customer_name=payload.customer.name,
            customer_phone=payload.customer.phone,
            delivery_info=payload.customer.delivery_info,
            total_amount=Decimal(total),
        )
        self.session.add(order)
        await self.session.flush()

        for item in payload.items:
            self.session.add(
                OrderItem(
                    order_id=order.id,
                    sku=item.sku,
                    qty=item.qty,
                    price=item.price,
                )
            )

        await self.session.flush()
        return order

