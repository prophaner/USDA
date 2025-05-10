"""
Test fixtures for the USDA Nutrition Proxy API tests.
"""
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server import app
from config import settings


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI app.
    This fixture provides a TestClient instance for making requests to the API.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_usda_api():
    """
    Mock the USDA API calls to avoid making real external requests during tests.
    This fixture patches the helpers module functions that make API calls.
    """
    # Sample search response data - this is what _search_usda returns
    search_results = [
        {
            "fdcId": 167774,
            "description": "Tomatillos, raw",
            "dataType": "SR Legacy",
            "foodCategory": "Vegetables and Vegetable Products"
        },
        {
            "fdcId": 168409,
            "description": "Tomatoes, red, ripe, raw, year round average",
            "dataType": "SR Legacy",
            "foodCategory": "Vegetables and Vegetable Products"
        }
    ]
    
    # Sample food details response - this is what _get_food returns
    food_details_response = {
        "fdcId": 167774,
        "description": "Tomatillos, raw",
        "dataType": "SR Legacy",
        "foodCategory": "Vegetables and Vegetable Products",
        "foodPortions": [
            {
                "id": 1234,
                "amount": 1.0,
                "gramWeight": 34.0,
                "portionDescription": "1 medium"
            },
            {
                "id": 5678,
                "amount": 1.0,
                "gramWeight": 120.0,
                "portionDescription": "1 cup, chopped"
            }
        ],
        "foodNutrients": [
            {
                "nutrient": {"id": 1003, "name": "Protein", "unitName": "g"},
                "amount": 1.0
            },
            {
                "nutrient": {"id": 1004, "name": "Total lipid (fat)", "unitName": "g"},
                "amount": 0.3
            },
            {
                "nutrient": {"id": 1005, "name": "Carbohydrate, by difference", "unitName": "g"},
                "amount": 5.8
            }
        ]
    }
    
    # Create a mock Ingredient class with from_food_details method
    class MockIngredient:
        @classmethod
        def from_food_details(cls, details):
            # Create a basic ingredient with the necessary fields
            portion = {
                "unit": "g",
                "amount": 100.0,
                "grams": 100.0,
                "description": "100 g"
            }
            
            nutrients = [
                {
                    "key": "protein",
                    "name": "Protein",
                    "value": details["foodNutrients"][0]["amount"],
                    "unit": "g"
                },
                {
                    "key": "fat",
                    "name": "Total lipid (fat)",
                    "value": details["foodNutrients"][1]["amount"],
                    "unit": "g"
                },
                {
                    "key": "carbs",
                    "name": "Carbohydrate",
                    "value": details["foodNutrients"][2]["amount"],
                    "unit": "g"
                }
            ]
            
            return {
                "fdc_id": details["fdcId"],
                "description": details["description"],
                "category": details["foodCategory"],
                "data_type": details["dataType"],
                "serving": portion,
                "portions": [portion],
                "nutrients": nutrients,
                "scale": lambda amount, unit: None  # Mock scale method
            }
    
    # Create mock objects for the API calls
    search_mock = MagicMock(return_value=search_results)
    food_mock = MagicMock(return_value=food_details_response)
    
    # Apply the patches
    with patch('helpers._search_usda', search_mock), \
         patch('helpers._get_food', food_mock), \
         patch('models.Ingredient.from_food_details', MockIngredient.from_food_details):
        yield {
            'search_mock': search_mock,
            'food_mock': food_mock,
            'search_data': search_results,
            'food_data': food_details_response
        }