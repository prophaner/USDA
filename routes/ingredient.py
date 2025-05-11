from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List

from helpers import _clean, _search_usda, _get_food
from models import Ingredient, Portion, Nutrient
from config import settings

router = APIRouter(
    prefix="/ingredient",
    tags=["ingredient"],
)

@router.get("/", response_model=Ingredient, responses={
               200: {"description": "Successful response with ingredient details"},
               404: {"description": "Ingredient not found"},
               422: {"description": "Invalid parameters"},
               500: {"description": "USDA API error"}
           }, summary="Fetch detailed ingredient data")
def get_ingredient(
    q: Optional[str] = Query(None, min_length=1, description="Free‑text search for ingredient"),
    fdc_id: Optional[int] = Query(None, description="Exact USDA FDC ID for ingredient"),
    amount: Optional[float] = Query(None, gt=0, description="Desired serving amount"),
    unit: Optional[str] = Query(None, description="Desired serving unit (e.g. 'cup', 'oz')")
) -> Ingredient:
    """
    Retrieve full ingredient details from USDA, normalize portions,
    and optionally rescale nutrients to the requested amount/unit.
    Provide either `q` or `fdc_id`.
    """
    # Resolve fdc_id via search if q provided
    if not fdc_id:
        if not q:
            raise HTTPException(422, detail="Provide either 'q' or 'fdc_id'.")
        hits = _search_usda(_clean(q), limit=1)
        if not hits:
            raise HTTPException(404, detail="Ingredient not found for query.")
        fdc_id = hits[0].get("fdcId")

    # Fetch raw details
    try:
        details = _get_food(fdc_id)
    except Exception:
        raise HTTPException(502, detail="Upstream USDA lookup failed.")

    # Build Portion list
    portions: List[Portion] = []
    for p in details.get("foodPortions", []):
        raw = p["measureUnit"].get("abbreviation") or p["measureUnit"].get("name")
        unit_can = raw.split(",")[0].strip().lower()
        gram_weight = p.get("gramWeight")
        if unit_can and gram_weight:
            portions.append(Portion(
                unit=unit_can,
                amount=p.get("amount", 1.0),
                grams=gram_weight,
                description=p.get("modifier")
            ))
    # Branded default if no portions found
    if not portions and details.get("dataType") == "Branded":
        su = details.get("servingSizeUnit", "").strip().lower()
        sg = details.get("servingSize")
        if su and sg:
            portions.append(Portion(unit=su, amount=1.0, grams=sg, description=None))

    # Determine default serving
    if portions:
        serving = portions[0]
    else:
        serving = Portion(unit="g", amount=100.0, grams=100.0, description=None)

    # Extract nutrients
    nutrients: List[Nutrient] = []
    for item in details.get("foodNutrients", []):
        if "nutrient" in item and "amount" in item:
            nutrient_info = item["nutrient"]
            num = nutrient_info.get("number")
            # Use the NUTRIENT_MAP from helpers
            from helpers import NUTRIENT_MAP
            key = NUTRIENT_MAP.get(num)
            if key:
                nutrients.append(Nutrient(
                    key=key,
                    name=nutrient_info.get("name", ""),
                    value=float(item["amount"]),  # Ensure we're using the amount field and converting to float
                    unit=nutrient_info.get("unitName", "").lower(),
                    min=item.get("min"),
                    max=item.get("max")
                ))

    # Assemble Ingredient
    # Handle foodCategory which can be a string or a dict
    food_category = details.get("foodCategory")
    if isinstance(food_category, dict):
        food_category = food_category.get("description", "")
    
    ingredient = Ingredient(
        fdc_id=fdc_id,
        description=details.get("description", ""),
        category=food_category,
        data_type=details.get("dataType"),
        serving=serving,
        portions=portions,
        nutrients=nutrients
    )

    # Apply scaling if requested
    if amount is not None and unit is not None:
        try:
            ingredient.scale(amount, unit)
        except ValueError as ve:
            raise HTTPException(400, detail=str(ve))

    return ingredient
