from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SupportMessageLink, SupportSession, SupportSessionStatus


class SupportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def open_support_session(self, user_id: int) -> SupportSession:
        existing = await self.session.scalar(
            select(SupportSession).where(
                SupportSession.user_id == user_id,
                SupportSession.status == SupportSessionStatus.active,
            )
        )
        if existing:
            return existing

        session = SupportSession(
            user_id=user_id,
            status=SupportSessionStatus.active,
            started_at=datetime.now(tz=timezone.utc),
        )
        self.session.add(session)
        await self.session.flush()
        return session

    async def close_support_session(self, user_id: int) -> None:
        await self.session.execute(
            update(SupportSession)
            .where(SupportSession.user_id == user_id, SupportSession.status == SupportSessionStatus.active)
            .values(status=SupportSessionStatus.closed, ended_at=datetime.now(tz=timezone.utc))
        )

    async def save_message_link(self, user_id: int, user_message_id: int, admin_message_id: int) -> None:
        link = SupportMessageLink(
            user_id=user_id,
            user_message_id=user_message_id,
            admin_message_id=admin_message_id,
            created_at=datetime.now(tz=timezone.utc),
        )
        self.session.add(link)
        await self.session.flush()

    async def get_user_id_by_admin_message(self, admin_message_id: int) -> int | None:
        query = select(SupportMessageLink.user_id).where(SupportMessageLink.admin_message_id == admin_message_id)
        return await self.session.scalar(query)

