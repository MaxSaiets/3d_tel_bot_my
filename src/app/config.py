from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = Field(default="change_me", alias="BOT_TOKEN")
    webhook_base_url: str = Field(default="https://example.com", alias="WEBHOOK_BASE_URL")
    webhook_secret: str = Field(default="change_me_secret", alias="WEBHOOK_SECRET")
    webhook_path: str = Field(default="/telegram/webhook", alias="WEBHOOK_PATH")
    webapp_url: str = Field(default="https://example.com/webapp", alias="WEBAPP_URL")
    admin_group_id: int = Field(default=-1000000000000, alias="ADMIN_GROUP_ID")

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/telegram_shop",
        alias="DATABASE_URL",
    )

    crm_provider: str = Field(default="espocrm", alias="CRM_PROVIDER")
    crm_url: str = Field(default="https://example-crm.invalid/orders", alias="CRM_URL")
    crm_token: str = Field(default="change_me_crm", alias="CRM_TOKEN")
    crm_timeout_seconds: int = Field(default=10, alias="CRM_TIMEOUT_SECONDS")
    crm_max_retries: int = Field(default=3, alias="CRM_MAX_RETRIES")
    espocrm_base_url: str = Field(default="https://crm.example.com", alias="ESPOCRM_BASE_URL")
    espocrm_api_key: str = Field(default="change_me_espo_key", alias="ESPOCRM_API_KEY")
    espocrm_order_entity: str = Field(default="Lead", alias="ESPOCRM_ORDER_ENTITY")
    espocrm_default_status: str = Field(default="New", alias="ESPOCRM_DEFAULT_STATUS")

    nova_poshta_enabled: bool = Field(default=False, alias="NOVA_POSHTA_ENABLED")
    nova_poshta_api_url: str = Field(
        default="https://api.novaposhta.ua/v2.0/json/", alias="NOVA_POSHTA_API_URL"
    )
    nova_poshta_api_key: str = Field(default="", alias="NOVA_POSHTA_API_KEY")
    nova_poshta_auto_create_ttn: bool = Field(default=False, alias="NOVA_POSHTA_AUTO_CREATE_TTN")
    np_sender_ref: str = Field(default="", alias="NP_SENDER_REF")
    np_sender_contact_ref: str = Field(default="", alias="NP_SENDER_CONTACT_REF")
    np_sender_address_ref: str = Field(default="", alias="NP_SENDER_ADDRESS_REF")
    np_sender_city_ref: str = Field(default="", alias="NP_SENDER_CITY_REF")
    np_sender_phone: str = Field(default="", alias="NP_SENDER_PHONE")

    api_order_rate_limit_per_minute: int = Field(default=30, alias="API_ORDER_RATE_LIMIT_PER_MINUTE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    cors_allow_origins: str = Field(default="*", alias="CORS_ALLOW_ORIGINS")

    @property
    def webhook_url(self) -> str:
        return f"{self.webhook_base_url.rstrip('/')}{self.webhook_path}"

    @property
    def cors_origins(self) -> list[str]:
        if self.cors_allow_origins.strip() == "*":
            return ["*"]
        return [item.strip() for item in self.cors_allow_origins.split(",") if item.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
