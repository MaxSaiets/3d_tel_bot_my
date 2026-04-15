from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.handlers import admin, start, support, webapp


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    # Order matters: specific handlers first, admin router at the end.
    dp.include_router(start.router)
    dp.include_router(webapp.router)
    dp.include_router(support.router)
    dp.include_router(admin.router)
    return dp

