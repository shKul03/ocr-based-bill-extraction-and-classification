from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

if settings.DB_PASSWORD:
    DATABASE_URL = (
        f"mysql+pymysql://{settings.DB_USER}:"
        f"{settings.DB_PASSWORD}@"
        f"{settings.DB_HOST}:"
        f"{settings.DB_PORT}/"
        f"{settings.DB_NAME}"
    )
else:
    DATABASE_URL = (
        f"mysql+pymysql://{settings.DB_USER}@"
        f"{settings.DB_HOST}:"
        f"{settings.DB_PORT}/"
        f"{settings.DB_NAME}"
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()
