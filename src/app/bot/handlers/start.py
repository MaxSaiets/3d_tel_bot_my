from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message

from app.bot.keyboards import main_menu_keyboard
from app.db.session import SessionLocal
from app.db.models import OrderStatus
from app.repositories.orders import OrderRepository
from app.repositories.users import UserRepository
from app.services.attribution_service import AttributionService

router = Router(name="start")

_STATUS_EMOJI = {
    OrderStatus.submitted: "🕐 Очікує",
    OrderStatus.confirmed: "✅ Підтверджено",
    OrderStatus.shipped:   "🚚 Відправлено",
    OrderStatus.delivered: "📦 Доставлено",
    OrderStatus.cancelled: "❌ Скасовано",
    OrderStatus.failed:    "⚠️ Помилка",
    OrderStatus.pending:   "🔄 Обробляється",
}


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
        service   = AttributionService(session)
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
        _welcome_text(first_name),
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
        _welcome_text(first_name),
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )


@router.message(F.text == "/menu")
async def menu_shortcut(message: Message) -> None:
    await message.answer("Головне меню:", reply_markup=main_menu_keyboard())


@router.message(F.text == "📋 Мої замовлення", F.chat.type == "private")
async def my_orders(message: Message) -> None:
    if message.from_user is None:
        return

    async with SessionLocal() as session:
        user_repo  = UserRepository(session)
        order_repo = OrderRepository(session)

        user = await user_repo.get_by_telegram_user_id(message.from_user.id)
        if not user:
            await message.answer("Ви ще не робили замовлень. 🛒")
            return

        orders = await order_repo.get_recent_by_user_id(user.id, limit=5)

    if not orders:
        await message.answer(
            "📋 У вас ще немає замовлень.\n\n"
            "Натисніть <b>«🛒 Відкрити магазин»</b>, щоб зробити перше!",
            parse_mode="HTML",
        )
        return

    lines = ["📋 <b>Ваші останні замовлення:</b>\n"]
    for o in orders:
        emoji_status = _STATUS_EMOJI.get(o.status, "•")
        date_str = o.created_at.strftime("%d.%m.%Y") if o.created_at else "—"
        line = f"{emoji_status}  <b>#{str(o.order_uuid)[:8]}</b>  ·  {int(o.total_amount)} ₴  ·  {date_str}"
        if o.ttn:
            line += f"\n   📦 ТТН: <code>{o.ttn}</code>"
        lines.append(line)

    await message.answer("\n\n".join(lines), parse_mode="HTML")


# ─────────────────────────────────────────────────────────────────────────────

def _welcome_text(first_name: str) -> str:
    return (
        f"👋 Вітаємо, <b>{first_name}</b>!\n\n"
        "🎣 У нас є класний товар для рибалок — натисніть <b>«🛒 Відкрити магазин»</b> "
        "щоб переглянути та оформити замовлення.\n\n"
        "📋 Переглянути свої замовлення — <b>«📋 Мої замовлення»</b>\n\n"
        "💬 Виникли питання? <b>«💬 Підтримка»</b> — і ми відповімо."
    )
