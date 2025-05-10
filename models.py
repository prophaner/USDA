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
