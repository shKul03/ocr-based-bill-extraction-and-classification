import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    LOG_LEVEL: str = "info"

    MONGO_URI: str = "mongodb://localhost:27017"
    DB_NAME: str = "bill_processing_db"

    TESSERACT_CMD: str | None = None
    
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "llama3"

    EXTERNAL_API_URL: str | None = None

    class Config:
        env_file = ".env"
        # We don't want to error if .env is missing, just use defaults or env vars
        env_file_encoding = "utf-8"

settings = Settings()
