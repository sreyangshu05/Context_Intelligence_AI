from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    supabase_url: str
    supabase_anon_key: str
    openai_api_key: Optional[str] = None
    liability_cap_threshold: int = 50000
    auto_renewal_notice_days: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
