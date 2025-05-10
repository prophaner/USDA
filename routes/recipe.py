from fastapi import APIRouter, HTTPException
from typing import List, Dict

from routes.ingredient import get_ingredient
from models import IngredientInput, RecipeOutput
from helpers import NUTRIENT_MAP

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
    # Initialize totals for all tracked nutrients
    totals: Dict[str, float] = {key: 0.0 for key in NUTRIENT_MAP.values()}
    details_list = []

    for itm in items:
        try:
            ing = get_ingredient(
                q=itm.q,
                fdc_id=itm.fdc_id,
                amount=itm.amount,
                unit=itm.unit
            )
        except HTTPException as e:
            # propagate ingredient lookup errors
            raise e
        # Append per-item details
        details_list.append(ing)
        # Sum nutrients
        for nut in ing.nutrients:
            totals[nut.key] += nut.value

    return RecipeOutput(total=totals, items=details_list)
