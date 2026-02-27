# app/config.py — 환경 변수 설정
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    환경 변수 기반 앱 설정.
    .env 파일 또는 시스템 환경 변수에서 값을 자동으로 읽습니다.
    """
    app_name: str = "Todo API"
    debug: bool = False
    database_url: str = "sqlite:///./app.db"
    secret_key: str = "change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


settings = Settings()
