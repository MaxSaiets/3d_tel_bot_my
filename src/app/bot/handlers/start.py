from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message

from app.bot.keyboards import main_menu_keyboard
from app.db.session import SessionLocal
from app.repositories.users import UserRepository
from app.services.attribution_service import AttributionService

router = Router(name="start")


@router.message(Command("id"))
async def get_chat_id(message: Message) -> None:
    """Показує поточний Chat ID — для налаштування ADMIN_GROUP_ID."""
    await message.answer(f"Chat ID: `{message.chat.id}`", parse_mode="Markdown")


@router.message(CommandStart(deep_link=True), F.chat.type == "private")
async def start_with_deeplink(message: Message, command: CommandObject) -> None:
    if message.from_user is None:
        return

    async with SessionLocal() as session:
        user_repo = UserRepository(session)
        service = AttributionService(session)

        user = await user_repo.upsert_user(
            telegram_user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )
        await service.save_start_source(user.id, command.args)
        await session.commit()

    first_name = message.from_user.first_name or "друже"
    await message.answer(
        f"👋 Вітаємо, <b>{first_name}</b>!\n\n"
        "🛒 Натисніть <b>«🛒 Відкрити магазин»</b> — оберіть товари та оформіть замовлення.\n\n"
        "💬 Виникли питання? Натисніть <b>«💬 Підтримка»</b> і ми відповімо.",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )


@router.message(CommandStart(), F.chat.type == "private")
async def start_plain(message: Message) -> None:
    if message.from_user is None:
        return

    async with SessionLocal() as session:
        user_repo = UserRepository(session)
        await user_repo.upsert_user(
            telegram_user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )
        await session.commit()

    first_name = message.from_user.first_name or "друже"
    await message.answer(
        f"👋 Вітаємо, <b>{first_name}</b>!\n\n"
        "🛒 Натисніть <b>«🛒 Відкрити магазин»</b> — оберіть товари та оформіть замовлення.\n\n"
        "💬 Виникли питання? Натисніть <b>«💬 Підтримка»</b> і ми відповімо.",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )


@router.message(F.text == "/menu")
async def menu_shortcut(message: Message) -> None:
    await message.answer("Головне меню:", reply_markup=main_menu_keyboard())

