# curado_usda/core/config.py

"""
Configuration settings for the Curado USDA API.

Uses Pydantic's BaseSettings for environment variable loading and validation.
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, HttpUrl


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables with defaults.
    
    Attributes:
        USDA_API_KEY: Your USDA FoodData Central API key
        USDA_BASE_URL: Base URL for USDA FoodData Central
        DEBUG: Enable debug mode
        LOG_LEVEL: Logging level
        CORS_ALLOW_ORIGINS: Allowed CORS origins
        CORS_ALLOW_METHODS: Allowed CORS methods
        CORS_ALLOW_HEADERS: Allowed CORS headers
        CORS_ALLOW_CREDENTIALS: Allow CORS credentials
        DEFAULT_PAGE_SIZE: Default page size for list endpoints
        MAX_CACHE_SIZE: Max LRU cache size for USDA lookups
    """
    # ─── USDA / FDC ────────────────────────────────────────────────────────
    USDA_API_KEY: str = Field(
        ...,
        description="Your USDA FoodData Central API key"
    )
    USDA_BASE_URL: HttpUrl = Field(
        "https://api.nal.usda.gov/fdc/v1",
        description="Base URL for USDA FoodData Central"
    )

    # ─── FastAPI / CORS / Logging ───────────────────────────────────────────
    DEBUG: bool = Field(
        False,
        description="Enable debug mode"
    )
    LOG_LEVEL: str = Field(
        "info",
        description="Logging level"
    )

    CORS_ALLOW_ORIGINS: List[str] = Field(
        ["*"],
        description="Allowed CORS origins"
    )
    CORS_ALLOW_METHODS: List[str] = Field(
        ["*"],
        description="Allowed CORS methods"
    )
    CORS_ALLOW_HEADERS: List[str] = Field(
        ["*"],
        description="Allowed CORS headers"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(
        True,
        description="Allow CORS credentials"
    )

    DEFAULT_PAGE_SIZE: int = Field(
        25,
        description="Default page size for list endpoints"
    )
    MAX_CACHE_SIZE: int = Field(
        1024,
        description="Max LRU cache size for USDA lookups"
    )

    # In Pydantic v2, Config is replaced with model_config
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # Ignore extra fields in the .env file
    }


# Create a singleton instance for importing
settings = Settings()