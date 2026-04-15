from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CrmEvent, CrmEventStatus


class CrmRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_pending_event(self, order_id: int, payload: dict) -> CrmEvent:
        event = CrmEvent(order_id=order_id, payload=payload, status=CrmEventStatus.pending, attempts=0)
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_event(self, event_id: int) -> CrmEvent | None:
        return await self.session.get(CrmEvent, event_id)

    async def list_pending(self, limit: int = 50) -> list[CrmEvent]:
        query = select(CrmEvent).where(CrmEvent.status == CrmEventStatus.pending).limit(limit)
        result = await self.session.scalars(query)
        return list(result)

