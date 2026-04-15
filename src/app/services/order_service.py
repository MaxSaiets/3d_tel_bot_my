from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.orders import OrderRepository
from app.repositories.users import UserRepository
from app.schemas.order import OrderCreateIn
from app.services.crm_service import CrmService


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.order_repo = OrderRepository(session)
        self.crm_service = CrmService(session)

    async def create_order(self, payload: OrderCreateIn) -> tuple[str, int]:
        user = await self.user_repo.upsert_user(
            telegram_user_id=payload.telegram_user_id,
            username=payload.telegram_username,
            first_name=None,
            last_name=None,
        )
        source_code = payload.meta.source_code or await self.user_repo.get_latest_source_code(user.id)
        order = await self.order_repo.create_order(user_id=user.id, source_code=source_code, payload=payload)
        event_id = await self.crm_service.enqueue_order_event(order, request_payload=payload)
        await self.session.commit()
        return str(order.order_uuid), event_id
