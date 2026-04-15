from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

from app.config import get_settings


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    settings = get_settings()
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Open Store", web_app=WebAppInfo(url=settings.webapp_url))],
            [KeyboardButton(text="Support"), KeyboardButton(text="Stop Support")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )

