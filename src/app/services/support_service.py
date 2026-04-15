from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.support import SupportRepository


class SupportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = SupportRepository(session)

    async def set_active(self, user_id: int) -> None:
        await self.repo.open_support_session(user_id)
        await self.session.commit()

    async def set_closed(self, user_id: int) -> None:
        await self.repo.close_support_session(user_id)
        await self.session.commit()

    async def save_link(self, user_id: int, user_message_id: int, admin_message_id: int) -> None:
        await self.repo.save_message_link(user_id=user_id, user_message_id=user_message_id, admin_message_id=admin_message_id)
        await self.session.commit()

    async def resolve_user_id_from_admin_reply(self, message: Message) -> int | None:
        if not message.reply_to_message:
            return None
        return await self.repo.get_user_id_by_admin_message(message.reply_to_message.message_id)

