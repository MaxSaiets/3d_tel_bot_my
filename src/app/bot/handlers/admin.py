import logging

from aiogram import Router
from aiogram.types import Message

from app.config import get_settings
from app.db.session import SessionLocal
from app.repositories.users import UserRepository
from app.services.support_service import SupportService

router = Router(name="admin")
logger = logging.getLogger(__name__)


@router.message()
async def route_admin_reply(message: Message) -> None:
    settings = get_settings()
    if message.chat.id != settings.admin_group_id:
        return
    if not message.reply_to_message:
        return

    async with SessionLocal() as session:
        support_service = SupportService(session)
        user_repo = UserRepository(session)
        user_id = await support_service.resolve_user_id_from_admin_reply(message)
        if not user_id:
            return

        user = await user_repo.get_by_id(user_id)
        if user is None:
            return

        await message.bot.copy_message(
            chat_id=user.telegram_user_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
        )
