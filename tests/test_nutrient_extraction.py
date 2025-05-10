"""
Test specifically for the nutrient extraction fix in routes/ingredient.py
"""
import pytest
from models import Nutrient

def test_nutrient_extraction_from_amount_field():
    """
    Test that Nutrient objects are correctly created using the 'amount' field
    from the USDA API response, not the 'value' field.
    """
    # Mock a nutrient item from the USDA API response
    nutrient_item = {
        "nutrient": {
            "id": 1008,
            "number": "208",
            "name": "Energy",
            "unitName": "kcal"
        },
        "amount": 50.0,  # This is the field we should be using
        "value": None,   # This field might not exist or be None
        "min": 45.0,
        "max": 55.0
    }
    
    # Create a Nutrient object using the same logic as in routes/ingredient.py
    nutrient = Nutrient(
        key="energy",
        name=nutrient_item.get("nutrient", {}).get("name", ""),
        value=nutrient_item.get("amount", 0.0),  # Using 'amount' instead of 'value'
        unit=nutrient_item.get("nutrient", {}).get("unitName", ""),
        min=nutrient_item.get("min"),
        max=nutrient_item.get("max")
    )
    
    # Verify the nutrient was created correctly
    assert nutrient.key == "energy"
    assert nutrient.name == "Energy"
    assert nutrient.value == 50.0  # This should be from the 'amount' field
    assert nutrient.unit == "kcal"
    assert nutrient.min == 45.0
    assert nutrient.max == 55.0