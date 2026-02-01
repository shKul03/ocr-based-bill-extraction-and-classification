import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # --------------------
    # API
    # --------------------
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    LOG_LEVEL: str = "info"

    # --------------------
    # Database
    # --------------------
    MONGO_URI: str = "mongodb://localhost:27017"
    DB_NAME: str = "bill_processing_db"

    # --------------------
    # OCR
    # --------------------
    TESSERACT_CMD: str | None = None

    # --------------------
    # LLM (Ollama)
    # --------------------
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "gemma3:4b"

    # --------------------
    # External integrations
    # --------------------
    EXTERNAL_API_URL: str | None = None      # used by /forward
    DASHBOARD_API_URL: str | None = "https://occupational-dale-falling-wearing.trycloudflare.com" + "/api/ingest"     # used by automatic dashboard push

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "documents"
    MINIO_SECURE: bool = False

    # MySQL
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "documents_db"
    DB_USER: str = "root"
    DB_PASSWORD: str | None = None



    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
