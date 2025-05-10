# curado_usda/server.py

"""
server.py

Main FastAPI application entrypoint. Mounts routers, applies middleware, and includes global settings.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from config import settings
from routes.search import router as search_router
from routes.ingredient import router as ingredient_router
from routes.recipe import router as recipe_router

# ---------------------------------------------------------------------------
# Lifespan context manager for startup/shutdown events
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Code before yield runs on startup, code after yield runs on shutdown.
    """
    # Startup: Validate critical configuration
    if not settings.USDA_API_KEY:
        raise ValueError("USDA_API_KEY environment variable is required")
    
    yield
    
    # Shutdown: Add any cleanup tasks here if needed
    # Example: close database connections, release resources, etc.
    pass

# ---------------------------------------------------------------------------
# FastAPI application setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="USDA Nutrition Proxy API",
    version="1.0.0",
    debug=settings.DEBUG,
    default_response_class=JSONResponse,
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware: CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# ---------------------------------------------------------------------------
# Include Routers
# ---------------------------------------------------------------------------
# Each router already defines its own prefix (e.g. /search, /ingredient, /recipe)
app.include_router(search_router)
app.include_router(ingredient_router)
app.include_router(recipe_router)

# ---------------------------------------------------------------------------
# Root health-check
# ---------------------------------------------------------------------------
@app.get("/", summary="Health check")
def root():
    return {"message": "API running — see /docs for endpoints"}

# Note: The lifespan implementation has been moved to the top of the file
# and integrated with the FastAPI app initialization.
