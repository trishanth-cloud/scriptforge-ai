"""
ScriptForge AI — Configuration
All settings are loaded from environment variables or .env file.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    APP_NAME: str = "ScriptForge AI"
    DEBUG: bool = False

    # Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    OUTPUT_DIR: Path = BASE_DIR / "outputs"
    DB_PATH: Path = BASE_DIR / "scriptforge.db"

    # AI Engine
    GEMINI_API_KEY: str = ""
    AI_MODEL: str = "gemini-2.5-pro"
    AI_MAX_TOKENS: int = 8192
    AI_TEMPERATURE: float = 0.3

    # Execution Sandbox
    EXECUTION_TIMEOUT: int = 30  # seconds
    MAX_MEMORY_MB: int = 256
    MAX_OUTPUT_SIZE: int = 1_000_000  # 1 MB max output capture

    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
    MAX_FILES_PER_UPLOAD: int = 10
    ALLOWED_EXTENSIONS: list[str] = [
        ".txt", ".md", ".csv", ".json", ".xml", ".log", ".yaml", ".yml",
    ]

    # Self-Correction
    MAX_REPAIR_ATTEMPTS: int = 3

    # Security
    SANDBOX_ENABLED: bool = True
    NETWORK_ACCESS_ENABLED: bool = False

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

# Ensure required directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
