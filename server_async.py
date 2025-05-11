"""
Async FastAPI application with rate limiting.

This version of the server uses async routes and includes rate limiting
for USDA API calls (1,000 requests per hour per IP address).
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio

from config import settings
from routes.search_async import router as search_router
from routes.ingredient_async import router as ingredient_router
from routes.recipe_async import router as recipe_router
from routes.label_async import router as label_router
from services.rate_limiter import usda_rate_limiter

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
    
    # Initialize any async resources here
    from helpers_async import http_client
    
    yield
    
    # Shutdown: Close the HTTP client
    await http_client.aclose()

# ---------------------------------------------------------------------------
# FastAPI application setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="USDA Nutrition Proxy API",
    description="A proxy API for USDA FoodData Central with rate limiting (1,000 requests per hour per IP)",
    version="1.1.0",
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
# Rate Limit Middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_rate_limit_headers(request: Request, call_next):
    """
    Add rate limit headers to responses.
    """
    # Get the client's IP address
    client_ip = request.client.host if request.client else "unknown"
    
    # Check current rate limit status (without incrementing)
    allowed, remaining = usda_rate_limiter.check_limit(client_ip)
    
    # Process the request
    response = await call_next(request)
    
    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = str(usda_rate_limiter.max_requests)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(usda_rate_limiter.window_seconds)
    
    return response

# ---------------------------------------------------------------------------
# Include Routers
# ---------------------------------------------------------------------------
# Each router already defines its own prefix (e.g. /search, /ingredient, /recipe, /label)
app.include_router(search_router)
app.include_router(ingredient_router)
app.include_router(recipe_router)
app.include_router(label_router)

# ---------------------------------------------------------------------------
# Root health-check
# ---------------------------------------------------------------------------
@app.get("/", summary="Health check")
async def root():
    return {"message": "API running — see /docs for endpoints"}

# ---------------------------------------------------------------------------
# Rate limit status endpoint
# ---------------------------------------------------------------------------
@app.get("/rate-limit", summary="Check rate limit status")
async def rate_limit_status(request: Request):
    """
    Check the current rate limit status for your IP address.
    This endpoint does not count against your rate limit.
    """
    client_ip = request.client.host if request.client else "unknown"
    allowed, remaining = usda_rate_limiter.check_limit(client_ip)
    
    return {
        "ip": client_ip,
        "limit": usda_rate_limiter.max_requests,
        "remaining": remaining,
        "reset_seconds": usda_rate_limiter.window_seconds
    }