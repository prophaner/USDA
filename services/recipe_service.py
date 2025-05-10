from typing import List

from models import IngredientInput, RecipeOutput
from services.ingredient_service import get_ingredient

def calculate_recipe(items: List[IngredientInput]) -> RecipeOutput:
    """
    Given a list of IngredientInput,
    fetch & scale each ingredient, then sum all nutrients.
    """
    ingredients = []
    for inp in items:
        ing = get_ingredient(
            q      = getattr(inp, "q", None),
            fdc_id = getattr(inp, "fdc_id", None),
            amount = inp.amount,
            unit   = inp.unit,
        )
        ingredients.append(ing)

    # Sum totals across all ingredients
    total = {}
    for ing in ingredients:
        for nut in ing.nutrients:
            total[nut.name] = total.get(nut.name, 0) + nut.value

    return RecipeOutput(
        items = ingredients,
        total = total
    )
