from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from app.config import get_settings


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    settings = get_settings()
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Відкрити магазин", web_app=WebAppInfo(url=settings.webapp_url))],
            [KeyboardButton(text="📋 Мої замовлення"), KeyboardButton(text="💬 Підтримка")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def support_active_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard shown while user is in live-support mode."""
    settings = get_settings()
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Відкрити магазин", web_app=WebAppInfo(url=settings.webapp_url))],
            [KeyboardButton(text="❌ Завершити підтримку")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def order_admin_keyboard(order_uuid: str) -> InlineKeyboardMarkup:
    """Inline keyboard attached to order notification in admin group."""
    short = order_uuid[:8]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Підтвердити", callback_data=f"order:confirm:{order_uuid}"),
                InlineKeyboardButton(text="❌ Скасувати",   callback_data=f"order:cancel:{order_uuid}"),
            ],
            [
                InlineKeyboardButton(text="🚚 Введіть TTN", callback_data=f"order:ship:{order_uuid}"),
                InlineKeyboardButton(text="💬 Написати",    callback_data=f"order:write:{order_uuid}"),
            ],
        ]
    )


def order_shipped_keyboard(order_uuid: str) -> InlineKeyboardMarkup:
    """Inline keyboard after TTN is entered — just cancel remaining."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Скасувати", callback_data=f"order:cancel:{order_uuid}"),
                InlineKeyboardButton(text="💬 Написати",  callback_data=f"order:write:{order_uuid}"),
            ],
        ]
    )
