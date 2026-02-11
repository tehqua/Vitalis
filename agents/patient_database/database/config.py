"""Database configuration and connection settings."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    database_url: str = "postgresql://postgres:password@localhost:5432/medscreening"
    database_pool_size: int = 20
    database_max_overflow: int = 10
    log_level: str = "INFO"
    echo: bool = False

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"


Base = declarative_base()
settings = DatabaseSettings()

engine = create_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.echo,
)
