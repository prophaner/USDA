"""
curado_usda.routes

Package initializer for API routers. Exposes sub-routers for inclusion in main FastAPI app.
"""

from .search import router as search_router
from .ingredient import router as ingredient_router
from .recipe import router as recipe_router

__all__ = [
    "search_router",
    "ingredient_router",
    "recipe_router",
]
