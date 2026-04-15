from pydantic import BaseModel, Field


class TelegramWebhookResponse(BaseModel):
    ok: bool = True


class HealthResponse(BaseModel):
    status: str = "ok"


class ReadyResponse(BaseModel):
    status: str = "ready"
    db: str = Field(default="up")

