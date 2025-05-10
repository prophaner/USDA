from typing import Optional

from helpers import _clean, _search_usda, _get_food
from models import Ingredient


def get_ingredient(
    q: Optional[str] = None,
    fdc_id: Optional[int] = None,
    amount: Optional[float] = None,
    unit:   Optional[str]  = None,
) -> Ingredient:
    """
    Fetch a single Ingredient from USDA (by name or fdc_id),
    build the Ingredient model, and optionally scale to (amount, unit).
    """
    # 1. Resolve fdc_id if only q provided
    if q and not fdc_id:
        cleaned = _clean(q)
        results = _search_usda(cleaned, limit=1)
        if not results:
            raise ValueError(f"No USDA match for '{q}'")
        fdc_id = results[0]["fdcId"]

    if not fdc_id:
        raise ValueError("Must provide q or fdc_id")

    # 2. Fetch raw details JSON
    details = _get_food(fdc_id)

    # 3. Construct Ingredient from raw data
    ingredient = Ingredient.from_food_details(details)

    # 4. Optionally apply scaling
    if amount is not None and unit:
        ingredient.scale(amount, unit)

    return ingredient
