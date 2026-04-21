import uuid as uuid_lib
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Order, OrderItem, OrderStatus
from app.schemas.order import OrderCreateIn


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_order(
        self, user_id: int, source_code: str | None, payload: OrderCreateIn
    ) -> Order:
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

    async def get_by_uuid(self, order_uuid: str) -> Order | None:
        """Fetch order by its UUID string."""
        try:
            parsed = uuid_lib.UUID(order_uuid)
        except ValueError:
            return None
        return await self.session.scalar(
            select(Order).where(Order.order_uuid == parsed)
        )

    async def update_status(
        self,
        order_id: int,
        status: OrderStatus,
        ttn: str | None = None,
    ) -> None:
        """Update order status (and optionally TTN tracking number)."""
        order = await self.session.get(Order, order_id)
        if order is None:
            return
        order.status = status
        if ttn is not None:
            order.ttn = ttn
        await self.session.flush()

    async def get_recent_by_user_id(
        self, user_id: int, limit: int = 5
    ) -> list[Order]:
        """Return recent orders for internal user_id."""
        result = await self.session.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
