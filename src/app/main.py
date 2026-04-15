import logging
from contextlib import asynccontextmanager

from aiogram import Bot
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware import InMemoryRateLimitMiddleware
from app.api.routes import router as api_router
from app.api.webhook import router as webhook_router
from app.bot.dispatcher import build_dispatcher
from app.config import get_settings
from app.db.session import engine
from app.logging import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)

    bot = Bot(token=settings.bot_token)
    dispatcher = build_dispatcher()
    app.state.bot = bot
    app.state.dispatcher = dispatcher

    await bot.set_webhook(
        url=settings.webhook_url,
        secret_token=settings.webhook_secret,
        allowed_updates=dispatcher.resolve_used_update_types(),
    )
    logger.info("Webhook configured", extra={"request_id": "startup"})
    try:
        yield
    finally:
        await bot.delete_webhook(drop_pending_updates=False)
        await bot.session.close()
        await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Telegram Ecommerce Bot", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        InMemoryRateLimitMiddleware, max_requests_per_minute=settings.api_order_rate_limit_per_minute
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    app.include_router(webhook_router)
    return app


app = create_app()
