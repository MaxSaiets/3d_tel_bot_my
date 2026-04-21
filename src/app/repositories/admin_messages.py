from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AdminMessageLink


class AdminMessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(
        self,
        user_id: int,
        admin_message_id: int,
        link_type: str = "order",
    ) -> None:
        """Map an admin-group message_id to an internal user_id."""
        # Skip duplicates silently
        existing = await self.session.scalar(
            select(AdminMessageLink).where(
                AdminMessageLink.admin_message_id == admin_message_id
            )
        )
        if existing:
            return
        link = AdminMessageLink(
            user_id=user_id,
            admin_message_id=admin_message_id,
            link_type=link_type,
            created_at=datetime.now(tz=timezone.utc),
        )
        self.session.add(link)
        await self.session.flush()

    async def get_user_id(self, admin_message_id: int) -> int | None:
        """Return internal user_id for a given admin message_id, or None."""
        return await self.session.scalar(
            select(AdminMessageLink.user_id).where(
                AdminMessageLink.admin_message_id == admin_message_id
            )
        )
