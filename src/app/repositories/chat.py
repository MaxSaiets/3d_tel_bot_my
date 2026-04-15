from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChatMessage


class ChatRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_message(self, user_id: int, content: str, direction: str) -> ChatMessage:
        msg = ChatMessage(user_id=user_id, content=content, direction=direction)
        self.session.add(msg)
        await self.session.flush()
        return msg

    async def get_history(self, user_id: int, limit: int = 50) -> list[ChatMessage]:
        result = await self.session.execute(
            select(ChatMessage)
            .where(ChatMessage.user_id == user_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_since(self, user_id: int, since: datetime) -> list[ChatMessage]:
        result = await self.session.execute(
            select(ChatMessage)
            .where(ChatMessage.user_id == user_id, ChatMessage.created_at > since)
            .order_by(ChatMessage.created_at.asc())
        )
        return list(result.scalars().all())
