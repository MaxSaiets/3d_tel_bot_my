from aiogram import F, Router
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message

from app.bot.keyboards import main_menu_keyboard
from app.db.session import SessionLocal
from app.repositories.users import UserRepository
from app.services.attribution_service import AttributionService

router = Router(name="start")


@router.message(CommandStart(deep_link=True))
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
        source = await service.save_start_source(user.id, command.args)
        await session.commit()

    source_text = f"Source tracked: `{source}`." if source else "Source code was not valid."
    await message.answer(
        f"Welcome! {source_text}\nUse the menu to open store or contact support.",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
    )


@router.message(CommandStart())
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

    await message.answer("Welcome! Open the store from the button below.", reply_markup=main_menu_keyboard())


@router.message(F.text == "/menu")
async def menu_shortcut(message: Message) -> None:
    await message.answer("Main menu is ready.", reply_markup=main_menu_keyboard())

