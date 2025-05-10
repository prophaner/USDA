# curado_usda/models.py

"""
Pydantic models for USDA nutrition API:
- Suggestion: type‑ahead results
- Portion: unit ↔ grams mapping
- Nutrient: nutrient entry with conversion helper
- Ingredient: full ingredient detail, portions, serving, nutrients, scaling
- IngredientInput & RecipeOutput for recipe aggregation
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator
from helpers import convert_units


class Suggestion(BaseModel):
    """Ingredient suggestion for live search."""
    fdc_id: int = Field(..., description="Food Data Central ID")
    description: str = Field(..., description="Food description")
    category: Optional[str] = Field(None, description="Food category")
    data_type: str = Field(..., description="USDA data type (e.g. Branded, Survey)")

    @validator("description", pre=True, always=True)
    def titlecase(cls, v: str) -> str:
        return v.title()


class Portion(BaseModel):
    """Represents a portion option and its gram equivalent."""
    unit: str = Field(..., description="Canonical unit (e.g. 'cup', 'g')")
    amount: float = Field(..., description="Number of units")
    grams: float = Field(..., description="Equivalent weight in grams")
    description: Optional[str] = Field(None, description="Optional display label")

    @validator("unit", pre=True)
    def normalize_unit(cls, v: str) -> str:
        return v.strip().lower()


class Nutrient(BaseModel):
    """Single nutrient entry with conversion support."""
    key: str = Field(..., description="Friendly key, e.g. 'fat', 'protein'")
    name: str = Field(..., description="Official USDA nutrient name")
    value: float = Field(..., description="Amount per serving, in `unit`")
    unit: str = Field(..., description="Unit of measure, e.g. 'G', 'MG'")
    min: Optional[float] = Field(None, description="Minimum observed value")
    max: Optional[float] = Field(None, description="Maximum observed value")

    def convert(self, to_unit: str) -> float:
        """
        Convert this nutrient's `value` from self.unit → to_unit.
        Returns a new float rounded to 4 decimals.
        """
        return round(convert_units(self.value, self.unit, to_unit), 4)


class Ingredient(BaseModel):
    """Detailed ingredient with portions, serving, and scaled nutrients."""
    fdc_id: int = Field(..., description="Food Data Central ID")
    description: str = Field(..., description="Food description")
    category: Optional[str] = Field(None, description="Food category")
    data_type: Optional[str] = Field(None, description="USDA data type")

    serving: Portion = Field(..., description="The chosen serving for scaling")
    portions: List[Portion] = Field(..., description="Available portion options")
    nutrients: List[Nutrient] = Field(..., description="Scaled nutrients for serving")
    
    @classmethod
    def from_food_details(cls, details):
        """
        Factory method to create an Ingredient from USDA FoodData Central API response.
        
        Args:
            details: Raw JSON response from USDA API
            
        Returns:
            Ingredient: Fully populated ingredient with portions and nutrients
        """
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
                if "amount" in p and "gramWeight" in p:
                    unit = "serving"
                    if "portionDescription" in p:
                        desc = p["portionDescription"]
                        if "cup" in desc.lower():
                            unit = "cup"
                        elif "tbsp" in desc.lower() or "tablespoon" in desc.lower():
                            unit = "tbsp"
                        elif "tsp" in desc.lower() or "teaspoon" in desc.lower():
                            unit = "tsp"
                        elif "oz" in desc.lower() or "ounce" in desc.lower():
                            unit = "oz"
                    
                    portion = Portion(
                        unit=unit,
                        amount=float(p["amount"]),
                        grams=float(p["gramWeight"]),
                        description=p.get("portionDescription", f"{p['amount']} {unit}")
                    )
                    portions.append(portion)
        
        # Extract nutrients
        nutrients = []
        if "foodNutrients" in details:
            for n in details["foodNutrients"]:
                if "nutrient" in n and "amount" in n and n["amount"]:
                    nutrient_info = n["nutrient"]
                    key = nutrient_info.get("name", "").lower().replace(" ", "_")
                    
                    # Map common nutrients to simpler keys
                    if "protein" in key:
                        key = "protein"
                    elif "lipid" in key or "fat" in key:
                        key = "fat"
                    elif "carbohydrate" in key:
                        key = "carbs"
                    elif "energy" in key and "kcal" in nutrient_info.get("unitName", "").lower():
                        key = "calories"
                    
                    nutrients.append(Nutrient(
                        key=key,
                        name=nutrient_info.get("name", ""),
                        value=float(n["amount"]),
                        unit=nutrient_info.get("unitName", "g").lower(),
                        min=None,
                        max=None
                    ))
        
        # Handle foodCategory which can be a string or a dict
        food_category = details.get("foodCategory")
        if isinstance(food_category, dict):
            food_category = food_category.get("description", "")
            
        # Create the ingredient
        return cls(
            fdc_id=details["fdcId"],
            description=details["description"],
            category=food_category,
            data_type=details.get("dataType"),
            serving=default_portion,
            portions=portions,
            nutrients=nutrients
        )

    def scale(self, amount: float, unit: str) -> None:
        """
        Rescale to a new serving:
          - finds a matching Portion by unit
          - or falls back to mass conversion g↔unit
          - updates self.serving and multiplies each nutrient.value
        """
        unit_norm = unit.strip().lower()
        old_grams = self.serving.grams

        # Determine new gram weight
        match = next((p for p in self.portions if p.unit == unit_norm), None)
        if match:
            new_grams = amount / match.amount * match.grams
        else:
            new_grams = convert_units(amount, unit_norm, "g")

        # Update serving to the new portion
        self.serving = Portion(
            unit=unit_norm,
            amount=amount,
            grams=new_grams,
            description=f"{amount} {unit_norm}"
        )

        # Compute scale factor relative to the old serving
        factor = (new_grams / old_grams) if old_grams and new_grams else 1.0

        # Scale each nutrient value
        for nut in self.nutrients:
            nut.value = round(nut.value * factor, 4)


class IngredientInput(BaseModel):
    """Input schema for recipe aggregation."""
    fdc_id: Optional[int] = Field(None, description="Optional FDC ID; used if provided")
    q: Optional[str] = Field(None, description="Optional search query; used if fdc_id missing")
    amount: Optional[float] = Field(None, description="Desired serving amount")
    unit: Optional[str] = Field(None, description="Desired serving unit")

    @validator("unit", pre=True, always=True)
    def unit_lower(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().lower() if v else v


class RecipeOutput(BaseModel):
    """Aggregated nutritional totals for a recipe."""
    items: List[Ingredient] = Field(..., description="Per-ingredient details")
    total: Dict[str, float] = Field(..., description="Summed nutrient values by key")
