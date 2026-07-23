from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    TG_BOT_TOKEN: str = ""
    INTERNAL_API_SECRET: str = ""
    MAX_UPLOAD_SIZE_MB: int = 20
    VAPID_PRIVATE_KEY_PATH: str = "keys/private_key.pem"
    VAPID_SUBJECT: str = "mailto:support@xpro.com"

settings = Settings()