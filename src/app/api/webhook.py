from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import get_db_session
from app.schemas.telegram import TelegramWebhookResponse

router = APIRouter()


@router.post("/telegram/webhook", response_model=TelegramWebhookResponse)
async def telegram_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> TelegramWebhookResponse:
    settings = get_settings()
    if settings.webhook_secret != x_telegram_bot_api_secret_token:
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    app_state = request.app.state
    bot = app_state.bot
    dispatcher = app_state.dispatcher

    data = await request.json()
    await dispatcher.feed_raw_update(bot=bot, update=data)
    await session.commit()
    return TelegramWebhookResponse(ok=True)
