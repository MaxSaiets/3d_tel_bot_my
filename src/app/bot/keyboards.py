from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

from app.config import get_settings


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    settings = get_settings()
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Відкрити магазин", web_app=WebAppInfo(url=settings.webapp_url))],
            [KeyboardButton(text="💬 Підтримка"), KeyboardButton(text="❌ Стоп підтримка")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def support_active_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard shown when user is in support mode."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Стоп підтримка")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
