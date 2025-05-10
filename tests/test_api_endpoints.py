"""
Tests for the FastAPI endpoints in the USDA Nutrition Proxy API.
"""
import pytest
from fastapi import status
from unittest.mock import patch

# Root endpoint test
def test_root_endpoint(client):
    """Test the root health check endpoint."""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert "message" in response.json()
    assert "API running" in response.json()["message"]

# Search endpoint tests
def test_search_endpoint_success(client, mock_usda_api):
    """Test the search endpoint with a valid query."""
    response = client.get("/search?q=tomatillo&limit=5")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "fdc_id" in data[0]
    assert "description" in data[0]

def test_search_endpoint_empty_query(client):
    """Test the search endpoint with an empty query."""
    response = client.get("/search?q=")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_search_endpoint_limit(client, mock_usda_api):
    """Test the search endpoint with a custom limit."""
    response = client.get("/search?q=tomato&limit=1")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) <= 1

# Ingredient endpoint tests
@patch('services.ingredient_service.get_ingredient')
def test_ingredient_by_query_success(mock_get_ingredient, client, mock_usda_api):
    """Test getting ingredient details by query string."""
    # Mock the get_ingredient function to return a dictionary
    mock_get_ingredient.return_value = {
        "fdc_id": 167774,
        "description": "Tomatillos, raw",
        "category": "Vegetables and Vegetable Products",
        "data_type": "SR Legacy",
        "serving": {"unit": "g", "amount": 100.0, "grams": 100.0},
        "portions": [{"unit": "g", "amount": 100.0, "grams": 100.0}],
        "nutrients": [{"key": "protein", "name": "Protein", "value": 1.0, "unit": "g"}]
    }
    
    response = client.get("/ingredient?q=Tomatillos, raw")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "fdc_id" in data
    assert "description" in data
    assert "nutrients" in data
    assert "portions" in data

@patch('services.ingredient_service.get_ingredient')
def test_pineapple_juice_nutrients(mock_get_ingredient, client, mock_usda_api):
    """Test getting pineapple juice with proper nutrient values."""
    # Mock the get_ingredient function to return a dictionary with pineapple juice data
    mock_get_ingredient.return_value = {
        "fdc_id": 168885,
        "description": "Pineapple juice, canned, not from concentrate, unsweetened, with added vitamins A, C and E",
        "category": "Fruits and Fruit Juices",
        "data_type": "SR Legacy",
        "serving": {"unit": "g", "amount": 100.0, "grams": 100.0},
        "portions": [
            {"unit": "g", "amount": 100.0, "grams": 100.0},
            {"unit": "cup", "amount": 1.0, "grams": 250.0}
        ],
        "nutrients": [
            {"key": "energy", "name": "Energy", "value": 50.0, "unit": "kcal"},
            {"key": "protein", "name": "Protein", "value": 0.4, "unit": "g"},
            {"key": "fat", "name": "Total lipid (fat)", "value": 0.14, "unit": "g"},
            {"key": "carbs", "name": "Carbohydrate, by difference", "value": 12.18, "unit": "g"},
            {"key": "sodium", "name": "Sodium, Na", "value": 3.0, "unit": "mg"}
        ]
    }
    
    response = client.get("/ingredient?q=Pineapple juice, canned, not from concentrate, unsweetened, with added vitamins A, C and E")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify the response contains the expected data
    assert data["description"] == "Pineapple juice, canned, not from concentrate, unsweetened, with added vitamins A, C and E"
    
    # Check that nutrients have proper values (not zero)
    nutrients = {n["key"]: n["value"] for n in data["nutrients"]}
    assert nutrients["energy"] == 50.0
    assert nutrients["fat"] == 0.14
    assert nutrients["sodium"] == 3.0
    assert nutrients["carbs"] == 12.18

@patch('services.ingredient_service.get_ingredient')
def test_ingredient_by_id_success(mock_get_ingredient, client, mock_usda_api):
    """Test getting ingredient details by FDC ID."""
    # Mock the get_ingredient function to return a dictionary
    mock_get_ingredient.return_value = {
        "fdc_id": 167774,
        "description": "Tomatillos, raw",
        "category": "Vegetables and Vegetable Products",
        "data_type": "SR Legacy",
        "serving": {"unit": "g", "amount": 100.0, "grams": 100.0},
        "portions": [{"unit": "g", "amount": 100.0, "grams": 100.0}],
        "nutrients": [{"key": "protein", "name": "Protein", "value": 1.0, "unit": "g"}]
    }
    
    response = client.get("/ingredient?fdc_id=167774")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["fdc_id"] == 167774
    assert "description" in data
    assert "nutrients" in data
    assert "portions" in data

@patch('services.ingredient_service.get_ingredient')
def test_ingredient_with_scaling(mock_get_ingredient, client, mock_usda_api):
    """Test getting ingredient details with amount and unit scaling."""
    # Mock the get_ingredient function to return a dictionary with cup units
    mock_get_ingredient.return_value = {
        "fdc_id": 167774,
        "description": "Tomatillos, raw",
        "category": "Vegetables and Vegetable Products",
        "data_type": "SR Legacy",
        "serving": {"unit": "cup", "amount": 2.0, "grams": 240.0},
        "portions": [{"unit": "g", "amount": 100.0, "grams": 100.0}],
        "nutrients": [{"key": "protein", "name": "Protein", "value": 2.0, "unit": "g"}]
    }
    
    response = client.get("/ingredient?q=Tomatillos, raw&amount=2&unit=cup")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "serving" in data
    assert data["serving"]["unit"] == "cup"
    assert data["serving"]["amount"] == 2.0

def test_ingredient_missing_params(client):
    """Test ingredient endpoint with missing parameters."""
    response = client.get("/ingredient")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# Recipe endpoint tests
@patch('services.recipe_service.calculate_recipe')
def test_recipe_endpoint_success(mock_calculate_recipe, client):
    """Test the recipe endpoint with valid ingredients."""
    # Mock the calculate_recipe function
    mock_calculate_recipe.return_value = {
        "total": {"protein": 3.0, "fat": 0.6},
        "items": [
            {
                "fdc_id": 167774,
                "description": "Tomatillos, raw",
                "serving": {"unit": "cup", "amount": 1.0, "grams": 120.0},
                "nutrients": [{"key": "protein", "name": "Protein", "value": 1.0, "unit": "g"}]
            },
            {
                "fdc_id": 168409,
                "description": "Tomatoes, red, ripe, raw",
                "serving": {"unit": "cup", "amount": 2.0, "grams": 240.0},
                "nutrients": [{"key": "protein", "name": "Protein", "value": 2.0, "unit": "g"}]
            }
        ]
    }
    
    recipe_data = [
        {"q": "Tomatillos, raw", "amount": 1, "unit": "cup"},
        {"q": "Tomatoes, red, ripe, raw", "amount": 2, "unit": "cup"}
    ]
    response = client.post("/recipe", json=recipe_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert len(data["items"]) == 2

def test_recipe_endpoint_empty_list(client):
    """Test the recipe endpoint with an empty list."""
    response = client.post("/recipe", json=[])
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# Test with a non-existent ingredient to trigger a 404 error
def test_recipe_endpoint_invalid_data(client):
    """Test the recipe endpoint with invalid data."""
    # Use a non-existent ingredient ID that will cause a 404 error
    invalid_data = [{"fdc_id": 99999999}]
    response = client.post("/recipe", json=invalid_data)
    # The response should be a 400 Bad Request or 404 Not Found
    assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND)

# Error handling tests
def test_not_found_endpoint(client):
    """Test accessing a non-existent endpoint."""
    response = client.get("/nonexistent")
    assert response.status_code == status.HTTP_404_NOT_FOUND