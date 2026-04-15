from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.antispam import is_support_spam
from app.bot.keyboards import main_menu_keyboard, support_active_keyboard
from app.bot.states import SupportStates
from app.config import get_settings
from app.db.session import SessionLocal
from app.repositories.users import UserRepository
from app.services.support_service import SupportService

router = Router(name="support")


@router.message(F.text == "💬 Підтримка")
async def support_on(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return

    async with SessionLocal() as session:
        user_repo = UserRepository(session)
        support_service = SupportService(session)
        user = await user_repo.upsert_user(
            telegram_user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )
        await support_service.set_active(user.id)

    await state.set_state(SupportStates.active)
    await message.answer(
        "💬 <b>Режим підтримки увімкнено.</b>\n\n"
        "Напишіть ваше повідомлення — адміністратор відповість найближчим часом.\n\n"
        "Щоб завершити — натисніть <b>«❌ Стоп підтримка»</b>.",
        reply_markup=support_active_keyboard(),
        parse_mode="HTML",
    )


@router.message(F.text == "❌ Стоп підтримка")
async def support_off(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return

    async with SessionLocal() as session:
        user_repo = UserRepository(session)
        support_service = SupportService(session)
        user = await user_repo.get_by_telegram_user_id(message.from_user.id)
        if user:
            await support_service.set_closed(user.id)

    await state.clear()
    await message.answer(
        "✅ Режим підтримки вимкнено. Повертаємось до головного меню.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(SupportStates.active)
async def forward_user_to_admin(message: Message) -> None:
    if message.from_user is None:
        return

    if is_support_spam(message.from_user.id):
        await message.answer("⚠️ Надто багато повідомлень. Зачекайте кілька секунд.")
        return

    settings = get_settings()
    async with SessionLocal() as session:
        user_repo = UserRepository(session)
        support_service = SupportService(session)
        user = await user_repo.get_by_telegram_user_id(message.from_user.id)
        if not user:
            return

        # Send header with user info to admin group
        username = f"@{message.from_user.username}" if message.from_user.username else "—"
        name = message.from_user.full_name or "—"
        header = await message.bot.send_message(
            chat_id=settings.admin_group_id,
            text=(
                f"💬 <b>Звернення до підтримки</b>\n"
                f"👤 {name} ({username})\n"
                f"🆔 <code>{message.from_user.id}</code>"
            ),
            parse_mode="HTML",
        )

        # Copy the actual message content (text, photo, voice, etc.)
        forwarded = await message.bot.copy_message(
            chat_id=settings.admin_group_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            reply_to_message_id=header.message_id,
        )
        await support_service.save_link(
            user_id=user.id,
            user_message_id=message.message_id,
            admin_message_id=forwarded.message_id,
        )

    await message.answer("📨 Повідомлення надіслано. Очікуйте відповіді від адміністратора.")
