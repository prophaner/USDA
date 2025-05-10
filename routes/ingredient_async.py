"""
Async ingredient route for USDA API.
"""
from fastapi import APIRouter, Query, HTTPException, Request
from typing import Optional, List

from helpers_async import _clean, _search_usda, _get_food, NUTRIENT_MAP
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
               429: {"description": "Rate limit exceeded"},
               500: {"description": "USDA API error"}
           }, summary="Fetch detailed ingredient data")
async def get_ingredient(
    request: Request,
    q: Optional[str] = Query(None, min_length=1, description="Free‑text search for ingredient"),
    fdc_id: Optional[int] = Query(None, description="Exact USDA FDC ID for ingredient"),
    amount: Optional[float] = Query(None, gt=0, description="Desired serving amount"),
    unit: Optional[str] = Query(None, description="Desired serving unit (e.g. 'cup', 'oz')")
) -> Ingredient:
    """
    Retrieve full ingredient details from USDA, normalize portions,
    and optionally rescale nutrients to the requested amount/unit.
    Provide either `q` or `fdc_id`.
    
    This endpoint is rate-limited to 1,000 requests per hour per IP address.
    """
    # Resolve fdc_id via search if q provided
    if q and not fdc_id:
        cleaned = _clean(q)
        try:
            results = await _search_usda(request, cleaned, limit=1)
        except ValueError as e:
            raise HTTPException(status_code=502, detail=str(e))
        except HTTPException:
            # Re-raise HTTPExceptions (like 429 Too Many Requests)
            raise
            
        if not results:
            raise HTTPException(status_code=404, detail=f"No USDA match for '{q}'")
        fdc_id = results[0]["fdcId"]

    if not fdc_id:
        raise HTTPException(status_code=422, detail="Must provide q or fdc_id")

    # Fetch raw details JSON
    try:
        details = await _get_food(request, fdc_id)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=502, detail=str(e))
    except HTTPException:
        # Re-raise HTTPExceptions (like 429 Too Many Requests)
        raise

    # Extract portions
    portions: List[Portion] = []
    
    # Default 100g portion
    portions.append(Portion(
        unit="g",
        amount=100.0,
        grams=100.0,
        description="100 g"
    ))
    
    # Add any food-specific portions
    for portion in details.get("foodPortions", []):
        # Skip if missing required data
        if not portion.get("gramWeight"):
            continue
            
        # Extract unit from measureUnit if available
        unit_name = "g"  # Default to grams
        if portion.get("measureUnit", {}).get("name"):
            unit_name = portion["measureUnit"]["name"]
            
        # Create the portion
        portions.append(Portion(
            unit=unit_name,
            amount=portion.get("amount", 1.0),
            grams=portion.get("gramWeight"),
            description=portion.get("portionDescription") or portion.get("modifier")
        ))
    
    # Extract nutrients
    nutrients: List[Nutrient] = []
    for item in details.get("foodNutrients", []):
        # Skip if missing nutrient info
        if not item.get("nutrient"):
            continue
            
        # Get the nutrient number and map to our key
        number = item.get("nutrient", {}).get("number")
        key = NUTRIENT_MAP.get(number, item.get("nutrient", {}).get("name", "").lower().replace(" ", "_"))
        
        # Create the nutrient
        nutrients.append(Nutrient(
            key=key,
            name=item.get("nutrient", {}).get("name", ""),
            value=item.get("amount", 0.0),  # Use 'amount' field, not 'value'
            unit=item.get("nutrient", {}).get("unitName", ""),
            min=item.get("min"),
            max=item.get("max")
        ))
    
    # Create the ingredient
    ingredient = Ingredient(
        fdc_id=details.get("fdcId"),
        description=details.get("description", ""),
        category=details.get("foodCategory"),
        data_type=details.get("dataType"),
        serving=portions[0],  # Default to first portion (100g)
        portions=portions,
        nutrients=nutrients
    )
    
    # Optionally apply scaling
    if amount is not None and unit:
        ingredient.scale(amount, unit)
    
    return ingredient