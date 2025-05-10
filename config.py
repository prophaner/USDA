# curado_usda/config.py

from typing import List
from pydantic import BaseSettings, Field, HttpUrl


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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # map each field name to its exact ENV var
        fields = {
            "USDA_API_KEY":         {"env": "USDA_API_KEY"},
            "USDA_BASE_URL":        {"env": "USDA_BASE_URL"},
            "DEBUG":                {"env": "DEBUG"},
            "LOG_LEVEL":            {"env": "LOG_LEVEL"},
            "CORS_ALLOW_ORIGINS":   {"env": "CORS_ALLOW_ORIGINS"},
            "CORS_ALLOW_METHODS":   {"env": "CORS_ALLOW_METHODS"},
            "CORS_ALLOW_HEADERS":   {"env": "CORS_ALLOW_HEADERS"},
            "CORS_ALLOW_CREDENTIALS":{"env": "CORS_ALLOW_CREDENTIALS"},
            "DEFAULT_PAGE_SIZE":    {"env": "DEFAULT_PAGE_SIZE"},
            "MAX_CACHE_SIZE":       {"env": "MAX_CACHE_SIZE"},
        }

# singleton settings for import
settings = Settings()
