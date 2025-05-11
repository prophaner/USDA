# curado_usda/models.py

"""
Pydantic models for USDA nutrition API:
- Suggestion: type‑ahead results
- Portion: unit ↔ grams mapping
- Nutrient: nutrient entry with conversion helper
- Ingredient: full ingredient detail, portions, serving, nutrients, scaling
- IngredientInput & RecipeOutput for recipe aggregation
"""

from typing import Dict, List, Optional, Union, Literal
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
                    
                    # Get the nutrient number for mapping
                    num = nutrient_info.get("number")
                    
                    # Import NUTRIENT_MAP from helpers
                    from helpers import NUTRIENT_MAP
                    
                    # Try to get the key from NUTRIENT_MAP first
                    key = NUTRIENT_MAP.get(num)
                    
                    # If not in the map, use a fallback approach
                    if not key:
                        key = nutrient_info.get("name", "").lower().replace(" ", "_")
                        
                        # Map common nutrients to simpler keys
                        if "protein" in key:
                            key = "protein"
                        elif "lipid" in key or "fat" in key:
                            key = "fat"
                        elif "carbohydrate" in key:
                            key = "carbs"
                        elif "energy" in key and "kcal" in nutrient_info.get("unitName", "").lower():
                            key = "energy"
                    
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


class LabelSections(BaseModel):
    """Label section visibility options."""
    hide_recipe_title: bool = Field(False, description="Hide recipe title")
    hide_nutrition_facts: bool = Field(False, description="Hide nutrition facts")
    hide_ingredient_list: bool = Field(False, description="Hide ingredient list")
    french_first: bool = Field(False, description="French first")
    english_only: bool = Field(False, description="English only")
    french_only: bool = Field(False, description="French only")
    hide_allergens: bool = Field(False, description="Hide allergens")
    hide_facility_allergens: bool = Field(False, description="Hide facility allergens")
    hide_business_info: bool = Field(False, description="Hide business info")
    hide_bioengineered_claim: bool = Field(False, description="Hide bioengineered claim")
    indicate_bioengineered_food: bool = Field(False, description="Indicate bioengineered food")
    show_caloric_conversion: bool = Field(False, description="Show caloric conversion")
    move_footnote_section: bool = Field(False, description="Move footnote section")
    shorten_footnote_section: bool = Field(False, description="Shorten footnote section")


class LabelStyle(BaseModel):
    """Label style options."""
    language: Literal["english", "french"] = Field("english", description="Language selector")
    serving_size_en: Optional[str] = Field(None, description="Serving size in English")
    serving_size_fr: Optional[str] = Field(None, description="Serving size in French")
    as_sold_description_en: Optional[str] = Field(None, description="As sold description in English")
    as_sold_description_fr: Optional[str] = Field(None, description="As sold description in French")
    as_prepared_description_en: Optional[str] = Field(None, description="As prepared description in English")
    as_prepared_description_fr: Optional[str] = Field(None, description="As prepared description in French")
    servings_per_package: Optional[float] = Field(None, description="Servings per package")
    varied_servings: bool = Field(False, description="Varied Servings")
    compact_vitamins: bool = Field(False, description="Compact vitamins")
    alignment: Literal["left", "center"] = Field("left", description="Text alignment")
    text_case: Literal["default", "lowercase", "titlecase"] = Field("default", description="Text case")
    width: int = Field(300, description="Label width in pixels")
    text_color: str = Field("#000000", description="Label text color")
    background_color: str = Field("#FFFFFF", description="Label background color")
    transparent_background: bool = Field(False, description="Transparent background")


class OptionalNutrients(BaseModel):
    """Optional nutrients to display."""
    show_saturated_fat_calories: bool = Field(False, description="Show saturated fat calories")
    show_unsaturated_fats: bool = Field(False, description="Show unsaturated fats")
    show_potassium: bool = Field(False, description="Show potassium")
    show_other_carbs: bool = Field(False, description="Show other carbs")
    show_sugar_alcohols: bool = Field(False, description="Show sugar alcohols")
    show_protein_percentage: bool = Field(False, description="Show protein percentage")
    protein_score: float = Field(1.0, description="Protein Score", ge=0.0, le=1.0)


class OptionalVitamins(BaseModel):
    """Optional vitamins to display."""
    toggle_all: bool = Field(False, description="Toggle all vitamins")
    show_vitamin_a: bool = Field(False, description="Show Vitamin A")
    show_vitamin_c: bool = Field(False, description="Show Vitamin C")
    show_vitamin_d: bool = Field(False, description="Show Vitamin D")
    show_vitamin_e: bool = Field(False, description="Show Vitamin E")
    show_vitamin_k: bool = Field(False, description="Show Vitamin K")
    show_thiamin: bool = Field(False, description="Show Thiamin")
    show_riboflavin: bool = Field(False, description="Show Riboflavin")
    show_niacin: bool = Field(False, description="Show Niacin")
    show_vitamin_b6: bool = Field(False, description="Show Vitamin B6")
    show_folate: bool = Field(False, description="Show Folate")
    show_vitamin_b12: bool = Field(False, description="Show Vitamin B12")
    show_pantothenic_acid: bool = Field(False, description="Show Pantothenic Acid")
    show_phosphorus: bool = Field(False, description="Show Phosphorus")
    show_magnesium: bool = Field(False, description="Show Magnesium")
    show_zinc: bool = Field(False, description="Show Zinc")
    show_selenium: bool = Field(False, description="Show Selenium")
    show_copper: bool = Field(False, description="Show Copper")
    show_manganese: bool = Field(False, description="Show Manganese")


class NutritionAdjustments(BaseModel):
    """Nutrition value adjustments."""
    calories: Optional[float] = Field(None, description="Calories")
    fat: Optional[float] = Field(None, description="Fat")
    saturated_fat: Optional[float] = Field(None, description="Saturated Fat")
    trans_fat: Optional[float] = Field(None, description="Trans Fat")
    polyunsaturated_fat: Optional[float] = Field(None, description="Polyunsaturated Fat")
    monounsaturated_fat: Optional[float] = Field(None, description="Monounsaturated Fat")
    cholesterol: Optional[float] = Field(None, description="Cholesterol")
    sodium: Optional[float] = Field(None, description="Sodium")
    carbohydrates: Optional[float] = Field(None, description="Carbohydrates")
    dietary_fiber: Optional[float] = Field(None, description="Dietary Fiber")
    sugars: Optional[float] = Field(None, description="Sugars")
    added_sugars: Optional[float] = Field(None, description="Added Sugars")
    sugar_alcohol: Optional[float] = Field(None, description="Sugar Alcohol")
    protein: Optional[float] = Field(None, description="Protein")
    vitamin_d: Optional[float] = Field(None, description="Vitamin D")
    calcium: Optional[float] = Field(None, description="Calcium")
    iron: Optional[float] = Field(None, description="Iron")
    potassium: Optional[float] = Field(None, description="Potassium")
    vitamin_a: Optional[float] = Field(None, description="Vitamin A")
    vitamin_c: Optional[float] = Field(None, description="Vitamin C")
    vitamin_e: Optional[float] = Field(None, description="Vitamin E")
    vitamin_k: Optional[float] = Field(None, description="Vitamin K")
    thiamin: Optional[float] = Field(None, description="Thiamin")
    riboflavin: Optional[float] = Field(None, description="Riboflavin")
    niacin: Optional[float] = Field(None, description="Niacin")
    vitamin_b6: Optional[float] = Field(None, description="Vitamin B6")
    folate: Optional[float] = Field(None, description="Folate")
    vitamin_b12: Optional[float] = Field(None, description="Vitamin B12")
    pantothenic_acid: Optional[float] = Field(None, description="Pantothenic Acid")
    phosphorus: Optional[float] = Field(None, description="Phosphorus")
    magnesium: Optional[float] = Field(None, description="Magnesium")
    zinc: Optional[float] = Field(None, description="Zinc")
    selenium: Optional[float] = Field(None, description="Selenium")
    copper: Optional[float] = Field(None, description="Copper")
    manganese: Optional[float] = Field(None, description="Manganese")


class BusinessInfo(BaseModel):
    """Business information."""
    business_name: str = Field(..., description="Business name")
    address: Optional[str] = Field(None, description="Business address")


class LabelInput(BaseModel):
    """Input schema for label generation."""
    recipe_title: str = Field(..., description="Recipe title")
    recipe_data: RecipeOutput = Field(..., description="Recipe nutritional data")
    label_sections: Optional[LabelSections] = Field(None, description="Label section visibility options")
    label_style: Optional[LabelStyle] = Field(None, description="Label style options")
    optional_nutrients: Optional[OptionalNutrients] = Field(None, description="Optional nutrients to display")
    optional_vitamins: Optional[OptionalVitamins] = Field(None, description="Optional vitamins to display")
    nutrition_adjustments: Optional[NutritionAdjustments] = Field(None, description="Nutrition value adjustments")
    label_type: str = Field("USDA (Old FDA) Vertical", description="Label type")
    business_info: Optional[BusinessInfo] = Field(None, description="Business information")
    allergens: Optional[List[str]] = Field(None, description="List of allergens")
    facility_allergens: Optional[List[str]] = Field(None, description="List of facility allergens")


class LabelOutput(BaseModel):
    """Output schema for label generation."""
    label_url: str = Field(..., description="URL to the generated label")
    pdf_download_url: str = Field(..., description="URL to download the label as PDF")
    png_download_url: str = Field(..., description="URL to download the label as PNG")
    embedded_html: str = Field(..., description="HTML code to embed the label in a UI")
    label_data: Dict = Field(..., description="Label data used for generation")
    missing_elements: Optional[List[str]] = Field(None, description="List of missing elements if any")
    
    
class LabelValidationError(BaseModel):
    """Error response for label validation."""
    detail: str = Field(..., description="Error message")
    missing_elements: List[str] = Field(..., description="List of missing required elements")
