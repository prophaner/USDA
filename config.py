# curado_usda/config.py

from typing import List
# In Pydantic v2, BaseSettings has moved to pydantic-settings
from pydantic_settings import BaseSettings
from pydantic import Field, HttpUrl


class Settings(BaseSettings):
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
        # In v2, environment variables are automatically mapped by field name
    }

# singleton settings for import
settings = Settings()
