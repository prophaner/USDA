"""
Tests specifically for the ingredient route and nutrient extraction.
"""
import pytest
from fastapi import status
from unittest.mock import patch, MagicMock

# We'll test the service layer instead of the route directly
from services.ingredient_service import get_ingredient


@patch('helpers._search_usda')
@patch('helpers._get_food')
def test_nutrient_extraction_from_amount_field(mock_get_food, mock_search_usda):
    """
    Test that nutrient values are correctly extracted from the 'amount' field
    in the USDA API response, not the 'value' field.
    """
    # Mock the search results
    mock_search_usda.return_value = [{
        "fdcId": 168885,
        "description": "Pineapple juice, canned",
    }]
    
    # Mock the USDA API response with a structure similar to the real API
    mock_get_food.return_value = {
        "fdcId": 168885,
        "description": "Pineapple juice, canned",
        "dataType": "SR Legacy",
        "foodCategory": "Fruits and Fruit Juices",
        "foodNutrients": [
            {
                "nutrient": {
                    "id": 1008,
                    "number": "208",
                    "name": "Energy",
                    "unitName": "kcal"
                },
                "amount": 50.0,  # This is the field we should be using
                "value": None,   # This field might not exist or be None
            },
            {
                "nutrient": {
                    "id": 1003,
                    "number": "203",
                    "name": "Protein",
                    "unitName": "g"
                },
                "amount": 0.4,
                "value": None,
            },
            {
                "nutrient": {
                    "id": 1004,
                    "number": "204",
                    "name": "Total lipid (fat)",
                    "unitName": "g"
                },
                "amount": 0.14,
                "value": None,
            }
        ]
    }
    
    # Call the service function
    result = get_ingredient(q="Pineapple juice")
    
    # Print all nutrients for debugging
    print("\nAll nutrients in result:")
    for n in result.nutrients:
        print(f"{n.key}: {n.value} {n.unit}")
    
    # Find nutrients by key
    energy_nutrient = next((n for n in result.nutrients if n.key == "energy"), None)
    protein_nutrient = next((n for n in result.nutrients if n.key == "protein"), None)
    fat_nutrient = next((n for n in result.nutrients if n.key == "fat"), None)
    
    # Print found nutrients
    print("\nFound nutrients:")
    print(f"Energy: {energy_nutrient}")
    print(f"Protein: {protein_nutrient}")
    print(f"Fat: {fat_nutrient}")
    
    # Verify nutrients exist
    assert energy_nutrient is not None, "Energy nutrient not found"
    assert protein_nutrient is not None, "Protein nutrient not found"
    assert fat_nutrient is not None, "Fat nutrient not found"
    
    # Verify the values were taken from the 'amount' field
    assert energy_nutrient.value == 50.0
    assert protein_nutrient.value == 0.4
    assert fat_nutrient.value == 0.14


@patch('services.ingredient_service.get_ingredient')
def test_pineapple_juice_integration(mock_get_ingredient, client):
    """
    Integration test for the pineapple juice example to ensure
    nutrient values are correctly populated.
    """
    # Mock the get_ingredient service to return a properly formatted response
    mock_get_ingredient.return_value = {
        "fdc_id": 168885,
        "description": "Pineapple juice, canned, not from concentrate",
        "category": "Fruits and Fruit Juices",
        "data_type": "SR Legacy",
        "serving": {"unit": "g", "amount": 100.0, "grams": 100.0, "description": "100 g"},
        "portions": [
            {"unit": "g", "amount": 100.0, "grams": 100.0, "description": "100 g"},
            {"unit": "cup", "amount": 1.0, "grams": 250.0, "description": "1 cup"}
        ],
        "nutrients": [
            {"key": "energy", "name": "Energy", "value": 50.0, "unit": "kcal", "min": None, "max": None},
            {"key": "protein", "name": "Protein", "value": 0.4, "unit": "g", "min": None, "max": None},
            {"key": "fat", "name": "Total lipid (fat)", "value": 0.14, "unit": "g", "min": None, "max": None},
            {"key": "carbs", "name": "Carbohydrate, by difference", "value": 12.18, "unit": "g", "min": None, "max": None},
            {"key": "sodium", "name": "Sodium, Na", "value": 3.0, "unit": "mg", "min": None, "max": None}
        ]
    }
    
    # Make the request
    response = client.get("/ingredient/?q=Pineapple%20juice")
    assert response.status_code == status.HTTP_200_OK
    
    # Check the response
    data = response.json()
    nutrients = {n["key"]: n["value"] for n in data["nutrients"]}
    
    # Verify nutrient values are not zero
    assert nutrients.get("energy", 0) > 0, "Energy should be greater than 0"
    assert nutrients.get("protein", 0) > 0, "Protein should be greater than 0"
    assert nutrients.get("fat", 0) > 0, "Fat should be greater than 0"
    assert nutrients.get("carbs", 0) > 0, "Carbs should be greater than 0"
    assert nutrients.get("sodium", 0) > 0, "Sodium should be greater than 0"
    
    # Verify specific values
    assert nutrients.get("energy") == 50.0
    assert nutrients.get("protein") == 0.4
    assert nutrients.get("fat") == 0.14
    assert nutrients.get("carbs") == 12.18
    assert nutrients.get("sodium") == 3.0