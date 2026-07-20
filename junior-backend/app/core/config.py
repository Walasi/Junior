from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os
import logging

logger = logging.getLogger(__name__)

load_dotenv()

class Settings(BaseSettings):
    app_name: str = "Junior API"
    debug: bool = True
    main_database_url: str = os.getenv("MAIN_DATABASE_URL", "sqlite:///./junior.db")
    qa_database_url: str = os.getenv("QA_DATABASE_URL", "")
    jwt_secret: str = os.getenv("JWT_SECRET", "change-this-secret-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    secret_key: str = os.getenv("SECRET_KEY", "")
    hf_token: str = os.getenv("HF_TOKEN", "")
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    fireworks_api_key: str = os.getenv("FIREWORKS_API_KEY", "")
    fireworks_base_url: str = os.getenv("FIREWORKS_BASE_URL", "https://api.fireworks.ai/inference/v1")
    resend_api_key: str = os.getenv("RESEND_API_KEY", "")
    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_phone_number: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    from_email: str = os.getenv("FROM_EMAIL", "alerts@junior.app")
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.tavily_api_key:
            logger.warning("TAVILY_API_KEY not set – web search will be disabled.")


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()