from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import StartAttribution, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_user(
        self, telegram_user_id: int, username: str | None, first_name: str | None, last_name: str | None
    ) -> User:
        query = select(User).where(User.telegram_user_id == telegram_user_id)
        existing = await self.session.scalar(query)
        if existing:
            existing.username = username
            existing.first_name = first_name
            existing.last_name = last_name
            await self.session.flush()
            return existing

        user = User(
            telegram_user_id=telegram_user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def save_attribution(self, user_id: int, source_code: str) -> StartAttribution:
        attribution = StartAttribution(
            user_id=user_id,
            source_code=source_code,
            created_at=datetime.now(tz=timezone.utc),
        )
        self.session.add(attribution)
        await self.session.flush()
        return attribution

    async def get_latest_source_code(self, user_id: int) -> str | None:
        query = (
            select(StartAttribution.source_code)
            .where(StartAttribution.user_id == user_id)
            .order_by(StartAttribution.created_at.desc())
            .limit(1)
        )
        return await self.session.scalar(query)

    async def get_by_telegram_user_id(self, telegram_user_id: int) -> User | None:
        query = select(User).where(User.telegram_user_id == telegram_user_id)
        return await self.session.scalar(query)

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)
