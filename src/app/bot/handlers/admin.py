"""Admin group handler.

Responsibilities:
1. Forward admin *replies* to the original user (works for order notifications,
   support messages, and any bot-generated prompt).
2. Handle inline-button callbacks on order notifications:
   confirm / cancel / ship (TTN entry) / write (custom message).
"""
import asyncio
import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.api.routes import save_admin_chat_reply
from app.bot.keyboards import order_admin_keyboard, order_shipped_keyboard
from app.bot.states import AdminStates
from app.config import get_settings
from app.db.models import OrderStatus
from app.db.session import SessionLocal
from app.repositories.admin_messages import AdminMessageRepository
from app.repositories.orders import OrderRepository
from app.repositories.support import SupportRepository
from app.repositories.users import UserRepository

router = Router(name="admin")
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

async def _resolve_telegram_user_id(session, replied_message_id: int) -> int | None:
    """Given admin-group message_id, return the Telegram user_id of the related user.

    Checks two tables:
    1. support_message_links  – messages forwarded during live-support sessions
    2. admin_message_links    – order notifications + bot-generated prompts
    """
    support_repo = SupportRepository(session)
    user_repo    = UserRepository(session)

    # 1. Check support_message_links
    internal_id = await support_repo.get_user_id_by_admin_message(replied_message_id)
    if internal_id:
        user = await user_repo.get_by_id(internal_id)
        return user.telegram_user_id if user else None

    # 2. Check admin_message_links (order notifications, prompts)
    admin_msg_repo = AdminMessageRepository(session)
    internal_id = await admin_msg_repo.get_user_id(replied_message_id)
    if internal_id:
        user = await user_repo.get_by_id(internal_id)
        return user.telegram_user_id if user else None

    return None


# ─────────────────────────────────────────────────────────────────────────────
# FSM: admin is entering TTN number
# ─────────────────────────────────────────────────────────────────────────────

@router.message(StateFilter(AdminStates.waiting_ttn))
async def receive_ttn(message: Message, state: FSMContext) -> None:
    settings = get_settings()
    if message.chat.id != settings.admin_group_id:
        return

    data = await state.get_data()
    order_uuid  = data.get("order_uuid")
    notify_msg_id = data.get("notify_msg_id")   # original notification message_id
    user_id     = data.get("user_id")           # internal user_id

    ttn = (message.text or "").strip()
    await state.clear()

    if not ttn:
        await message.reply("⚠️ TTN порожній. Операцію скасовано.")
        return

    async with SessionLocal() as session:
        order_repo = OrderRepository(session)
        user_repo  = UserRepository(session)
        order = await order_repo.get_by_uuid(order_uuid)
        if not order:
            await message.reply("⚠️ Замовлення не знайдено.")
            return
        await order_repo.update_status(order.id, OrderStatus.shipped, ttn=ttn)
        await session.commit()

        user = await user_repo.get_by_id(user_id)
        if user:
            try:
                await message.bot.send_message(
                    chat_id=user.telegram_user_id,
                    text=(
                        f"🚚 Ваше замовлення <b>#{order_uuid[:8]}</b> відправлено!\n\n"
                        f"📦 ТТН: <code>{ttn}</code>\n"
                        f"Відстежити: "
                        f"<a href='https://tracking.novaposhta.ua/#/uk/{ttn}'>Нова Пошта</a>"
                    ),
                    parse_mode="HTML",
                )
            except Exception as exc:
                logger.warning("Failed to notify user about shipment: %s", exc)

    # Update the original notification keyboard
    if notify_msg_id:
        try:
            await message.bot.edit_message_reply_markup(
                chat_id=settings.admin_group_id,
                message_id=notify_msg_id,
                reply_markup=order_shipped_keyboard(order_uuid),
            )
        except Exception:
            pass

    await message.reply(f"✅ TTN <code>{ttn}</code> збережено, клієнта повідомлено.", parse_mode="HTML")


# ─────────────────────────────────────────────────────────────────────────────
# FSM: admin is typing a custom message to client
# ─────────────────────────────────────────────────────────────────────────────

@router.message(StateFilter(AdminStates.waiting_message))
async def receive_admin_message(message: Message, state: FSMContext) -> None:
    settings = get_settings()
    if message.chat.id != settings.admin_group_id:
        return

    data = await state.get_data()
    telegram_user_id = data.get("telegram_user_id")
    await state.clear()

    if not telegram_user_id:
        return

    # Forward to user
    try:
        await message.bot.copy_message(
            chat_id=telegram_user_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
        )
    except Exception as exc:
        await message.reply(f"⚠️ Не вдалось надіслати: {exc}")
        return

    content = message.text or message.caption or "[медіа]"
    asyncio.create_task(save_admin_chat_reply(telegram_user_id, content))
    await message.reply("✅ Повідомлення надіслано клієнту.", parse_mode="HTML")


# ─────────────────────────────────────────────────────────────────────────────
# Callback: order action buttons
# ─────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("order:"))
async def handle_order_callback(call: CallbackQuery, state: FSMContext) -> None:
    settings = get_settings()
    parts = call.data.split(":", 2)
    if len(parts) != 3:
        await call.answer("Невірний формат кнопки.", show_alert=True)
        return

    _, action, order_uuid = parts

    async with SessionLocal() as session:
        order_repo = OrderRepository(session)
        user_repo  = UserRepository(session)

        order = await order_repo.get_by_uuid(order_uuid)
        if not order:
            await call.answer("⚠️ Замовлення не знайдено.", show_alert=True)
            return

        user = await user_repo.get_by_id(order.user_id)
        if not user:
            await call.answer("⚠️ Користувача не знайдено.", show_alert=True)
            return

        short = order_uuid[:8]

        # ── Confirm ──
        if action == "confirm":
            if order.status == OrderStatus.cancelled:
                await call.answer("Замовлення вже скасовано.", show_alert=True)
                return
            await order_repo.update_status(order.id, OrderStatus.confirmed)
            await session.commit()
            try:
                await call.bot.send_message(
                    chat_id=user.telegram_user_id,
                    text=(
                        f"✅ Замовлення <b>#{short}</b> підтверджено!\n\n"
                        f"Очікуйте відправки — ми повідомимо вас з TTN-номером."
                    ),
                    parse_mode="HTML",
                )
            except Exception as exc:
                logger.warning("Failed to notify user about confirmation: %s", exc)
            await call.answer("✅ Підтверджено!")
            # Remove Confirm button, keep Cancel + Ship + Write
            try:
                await call.message.edit_reply_markup(
                    reply_markup=order_admin_keyboard(order_uuid)
                )
            except Exception:
                pass

        # ── Cancel ──
        elif action == "cancel":
            if order.status == OrderStatus.cancelled:
                await call.answer("Вже скасовано.", show_alert=True)
                return
            await order_repo.update_status(order.id, OrderStatus.cancelled)
            await session.commit()
            try:
                await call.bot.send_message(
                    chat_id=user.telegram_user_id,
                    text=(
                        f"❌ На жаль, замовлення <b>#{short}</b> скасовано.\n\n"
                        f"Якщо це помилка — зверніться до підтримки 💬"
                    ),
                    parse_mode="HTML",
                )
            except Exception as exc:
                logger.warning("Failed to notify user about cancellation: %s", exc)
            await call.answer("Скасовано.")
            try:
                await call.message.edit_reply_markup(reply_markup=None)
            except Exception:
                pass

        # ── Ship (ask for TTN) ──
        elif action == "ship":
            await call.answer()
            await state.set_state(AdminStates.waiting_ttn)
            await state.update_data(
                order_uuid=order_uuid,
                notify_msg_id=call.message.message_id,
                user_id=order.user_id,
            )
            prompt = await call.message.reply(
                f"📦 Замовлення <b>#{short}</b>\n\n"
                f"Введіть TTN-номер Нової Пошти у відповідь на це повідомлення:",
                parse_mode="HTML",
            )
            # Map prompt message too, so replying to it also works
            admin_msg_repo = AdminMessageRepository(session)
            await admin_msg_repo.save(order.user_id, prompt.message_id, "prompt")
            await session.commit()

        # ── Write custom message ──
        elif action == "write":
            await call.answer()
            await state.set_state(AdminStates.waiting_message)
            await state.update_data(telegram_user_id=user.telegram_user_id)
            await call.message.reply(
                f"✏️ Пишіть повідомлення клієнту <b>#{short}</b> у відповідь на це:",
                parse_mode="HTML",
            )

        else:
            await call.answer("Невідома дія.", show_alert=True)


# ─────────────────────────────────────────────────────────────────────────────
# General reply handler: admin replies to any mapped message → forward to user
# ─────────────────────────────────────────────────────────────────────────────

@router.message()
async def route_admin_reply(message: Message) -> None:
    settings = get_settings()
    if message.chat.id != settings.admin_group_id:
        return
    if not message.reply_to_message:
        return

    async with SessionLocal() as session:
        telegram_user_id = await _resolve_telegram_user_id(
            session, message.reply_to_message.message_id
        )
        if not telegram_user_id:
            return  # Reply to an unmapped message — ignore

        # Forward message to user
        try:
            await message.bot.copy_message(
                chat_id=telegram_user_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
            )
        except Exception as exc:
            logger.warning("Failed to forward admin reply to user %s: %s", telegram_user_id, exc)
            return

        # Also persist in chat_messages so WebApp displays it
        content = message.text or message.caption or "[медіа]"
        asyncio.create_task(save_admin_chat_reply(telegram_user_id, content))

        # Map THIS reply message so future replies to it also work (thread continuity)
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_user_id(telegram_user_id)
        if user:
            admin_msg_repo = AdminMessageRepository(session)
            await admin_msg_repo.save(user.id, message.message_id, "reply")
            await session.commit()
