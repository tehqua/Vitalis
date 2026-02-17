"""
Configuration settings for the backend API.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application settings
    APP_NAME: str = "Medical Chatbot API"
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # CORS settings
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        env="CORS_ORIGINS"
    )
    
    # Security settings
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    SESSION_EXPIRE_MINUTES: int = Field(default=30, env="SESSION_EXPIRE_MINUTES")
    
    # Database settings (MongoDB or PostgreSQL)
    DATABASE_URL: str = Field(
        default="mongodb://localhost:27017",
        env="DATABASE_URL"
    )
    DATABASE_NAME: str = Field(default="medical_chatbot", env="DATABASE_NAME")
    
    # File upload settings
    UPLOAD_DIR: str = Field(default="uploads", env="UPLOAD_DIR")
    MAX_FILE_SIZE_MB: int = Field(default=10, env="MAX_FILE_SIZE_MB")
    ALLOWED_IMAGE_EXTENSIONS: List[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".gif", ".webp"],
        env="ALLOWED_IMAGE_EXTENSIONS"
    )
    ALLOWED_AUDIO_EXTENSIONS: List[str] = Field(
        default=[".wav", ".mp3", ".m4a", ".ogg", ".webm"],
        env="ALLOWED_AUDIO_EXTENSIONS"
    )
    
    # Orchestrator settings
    ORCHESTRATOR_MODEL: str = Field(
        default="thiagomoraes/medgemma-4b-it:Q4_K_S",
        env="ORCHESTRATOR_MODEL"
    )
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434",
        env="OLLAMA_BASE_URL"
    )
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=20, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_PER_HOUR: int = Field(default=100, env="RATE_LIMIT_PER_HOUR")
    
    # Patient database path
    PATIENT_DB_VECTOR_DIR: str = Field(
        default="../agents/patient_database/data/vectordb",
        env="PATIENT_DB_VECTOR_DIR"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings instance
    """
    return Settings()