"""
curado_usda

USDA Nutrition Proxy API

Provides:
- FastAPI application instance (`app`)
- Core modules: helpers, models, server
"""

__version__ = "0.1.0"

# Expose FastAPI app for ASGI servers
from .server import app  # noqa

# Package exports
__all__ = [
    "app",
    "__version__",
]