from fastapi import APIRouter, HTTPException
from typing import List, Dict

from models import IngredientInput, RecipeOutput
from services.recipe_service import calculate_recipe

router = APIRouter(
    prefix="/recipe",
    tags=["recipe"],
)

@router.post("/", response_model=RecipeOutput, summary="Aggregate recipe nutrition")
def recipe(items: List[IngredientInput]) -> RecipeOutput:
    """
    Aggregate a list of ingredients (with optional scaling) into total nutrients.
    Each IngredientInput may provide fdc_id or q plus optional amount/unit.
    """
    if not items:
        raise HTTPException(status_code=422, detail="Empty ingredient list")
    
    try:
        return calculate_recipe(items)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
