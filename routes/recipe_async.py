"""
Async recipe route for USDA API.
"""
from fastapi import APIRouter, HTTPException, Request
from typing import List

from models import IngredientInput, RecipeOutput
from services.recipe_service_async import calculate_recipe

router = APIRouter(
    prefix="/recipe",
    tags=["recipe"],
)

@router.post("/", response_model=RecipeOutput, responses={
                429: {"description": "Rate limit exceeded"},
                400: {"description": "Invalid request"},
                422: {"description": "Validation error"}
            }, summary="Aggregate recipe nutrition")
async def recipe(
    request: Request,
    items: List[IngredientInput]
) -> RecipeOutput:
    """
    Aggregate a list of ingredients (with optional scaling) into total nutrients.
    Each IngredientInput may provide fdc_id or q plus optional amount/unit.
    
    This endpoint is rate-limited to 1,000 requests per hour per IP address.
    """
    if not items:
        raise HTTPException(status_code=422, detail="Empty ingredient list")
    
    try:
        return await calculate_recipe(request, items)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        # Re-raise HTTPExceptions (like 429 Too Many Requests)
        raise