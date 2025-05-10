"""
Async recipe service for calculating recipe nutrition.
"""
import asyncio
from typing import Dict, List, Any
from fastapi import Request

from models import IngredientInput, RecipeOutput, Ingredient
from routes.ingredient_async import get_ingredient

async def calculate_recipe(request: Request, items: List[IngredientInput]) -> RecipeOutput:
    """
    Calculate total nutrition for a recipe by fetching and aggregating
    multiple ingredients, with optional scaling.
    
    Args:
        request: The FastAPI request object for rate limiting
        items: List of ingredient inputs with optional scaling
        
    Returns:
        RecipeOutput with total nutrition and individual ingredients
        
    Raises:
        ValueError: If there's an error fetching ingredients
    """
    if not items:
        raise ValueError("Empty ingredient list")
    
    # Fetch all ingredients concurrently
    ingredients_tasks = []
    for item in items:
        # Create task for each ingredient
        if item.fdc_id:
            task = get_ingredient(
                request=request,
                fdc_id=item.fdc_id,
                amount=item.amount,
                unit=item.unit
            )
        else:
            task = get_ingredient(
                request=request,
                q=item.q,
                amount=item.amount,
                unit=item.unit
            )
        ingredients_tasks.append(task)
    
    # Wait for all tasks to complete
    ingredients = await asyncio.gather(*ingredients_tasks, return_exceptions=True)
    
    # Check for exceptions
    for i, result in enumerate(ingredients):
        if isinstance(result, Exception):
            raise ValueError(f"Error fetching ingredient {i+1}: {str(result)}")
    
    # Calculate totals
    total_nutrients: Dict[str, Dict[str, Any]] = {}
    
    # Process each ingredient
    for ingredient in ingredients:
        for nutrient in ingredient.nutrients:
            # Initialize if first time seeing this nutrient
            if nutrient.key not in total_nutrients:
                total_nutrients[nutrient.key] = {
                    "name": nutrient.name,
                    "value": 0.0,
                    "unit": nutrient.unit
                }
            
            # Add to total
            total_nutrients[nutrient.key]["value"] += nutrient.value
    
    # Convert to list format for output
    total_list = [
        {
            "key": key,
            "name": data["name"],
            "value": round(data["value"], 2),
            "unit": data["unit"]
        }
        for key, data in total_nutrients.items()
    ]
    
    # Sort by key for consistent output
    total_list.sort(key=lambda x: x["key"])
    
    return RecipeOutput(
        total=total_list,
        items=ingredients
    )