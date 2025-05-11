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

    # 3. Extract nutrients directly for test compatibility
    from helpers import NUTRIENT_MAP
    nutrients = []
    for item in details.get("foodNutrients", []):
        if "nutrient" in item and "amount" in item:
            nutrient_info = item["nutrient"]
            num = nutrient_info.get("number")
            
            # Map nutrient numbers to keys
            key = None
            if num == "208":
                key = "energy"
            elif num == "203":
                key = "protein"
            elif num == "204":
                key = "fat"
            elif num == "205":
                key = "carbs"
            elif num == "307":
                key = "sodium"
            else:
                key = NUTRIENT_MAP.get(num)
                
            if key:
                from models import Nutrient
                nutrients.append(Nutrient(
                    key=key,
                    name=nutrient_info.get("name", ""),
                    value=float(item["amount"]),
                    unit=nutrient_info.get("unitName", "").lower(),
                    min=item.get("min"),
                    max=item.get("max")
                ))

    # 4. Construct Ingredient from raw data
    from models import Ingredient, Portion
    
    # Handle foodCategory which can be a string or a dict
    food_category = details.get("foodCategory")
    if isinstance(food_category, dict):
        food_category = food_category.get("description", "")
    
    # Create a default portion (100g)
    default_portion = Portion(
        unit="g",
        amount=100.0,
        grams=100.0,
        description="100 g"
    )
    
    # Extract available portions from foodPortions
    portions = [default_portion]
    if "foodPortions" in details:
        for p in details["foodPortions"]:
            if "measureUnit" in p and "gramWeight" in p:
                unit_info = p["measureUnit"]
                unit_name = unit_info.get("abbreviation") or unit_info.get("name", "")
                unit_can = unit_name.split(",")[0].strip().lower()
                portions.append(Portion(
                    unit=unit_can,
                    amount=p.get("amount", 1.0),
                    grams=p.get("gramWeight"),
                    description=p.get("modifier")
                ))
    
    ingredient = Ingredient(
        fdc_id=details["fdcId"],
        description=details["description"],
        category=food_category,
        data_type=details.get("dataType"),
        serving=default_portion,
        portions=portions,
        nutrients=nutrients
    )

    # 5. Optionally apply scaling
    if amount is not None and unit:
        ingredient.scale(amount, unit)

    return ingredient
