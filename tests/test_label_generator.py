"""
Tests for the label generator service.
"""

import os
import pytest
from pathlib import Path
import json
import uuid

from services.label_generator import (
    generate_label_files,
    generate_pdf,
    generate_png,
    generate_html,
    TEMP_DIR
)


@pytest.fixture
def sample_label_data():
    """Create sample label data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "recipe_title": "Test Recipe",
        "recipe_data": {
            "items": [
                {
                    "fdc_id": 123,
                    "description": "Test Ingredient",
                    "category": "Test Category",
                    "data_type": "Test Data Type",
                    "nutrients": [
                        {
                            "key": "energy",
                            "name": "Energy",
                            "value": 100.0,
                            "unit": "kcal"
                        },
                        {
                            "key": "fat",
                            "name": "Total lipid (fat)",
                            "value": 10.0,
                            "unit": "g"
                        }
                    ]
                }
            ],
            "total": {
                "Energy": 100.0,
                "Total lipid (fat)": 10.0
            }
        },
        "business_info": {
            "business_name": "Test Business",
            "address": "123 Test St, Test City, TS 12345"
        },
        "label_type": "USDA (Old FDA) Vertical",
        "nutrition_adjustments": {
            "calories": 100.0,
            "fat": 10.0,
            "saturated_fat": 2.0,
            "trans_fat": 0.0,
            "cholesterol": 0.0,
            "sodium": 100.0,
            "carbohydrates": 20.0,
            "dietary_fiber": 5.0,
            "sugars": 5.0,
            "protein": 5.0
        },
        "label_sections": {
            "hide_recipe_title": False,
            "hide_nutrition_facts": False,
            "hide_ingredient_list": False,
            "hide_allergens": False,
            "hide_facility_allergens": False,
            "hide_business_info": False
        },
        "label_style": {
            "language": "english",
            "serving_size_en": "1 cup (240g)",
            "servings_per_package": 4,
            "alignment": "left",
            "text_color": "#000000",
            "background_color": "#FFFFFF"
        },
        "allergens": ["Milk", "Eggs"],
        "facility_allergens": ["Peanuts", "Tree Nuts"]
    }


def test_generate_pdf(sample_label_data):
    """Test PDF generation."""
    label_id = sample_label_data["id"]
    pdf_path = generate_pdf(sample_label_data, label_id)
    
    # Check that the file exists
    assert os.path.exists(pdf_path)
    
    # Check that it's a PDF file
    with open(pdf_path, "rb") as f:
        header = f.read(4)
        assert header == b"%PDF"
    
    # Clean up
    os.remove(pdf_path)


def test_generate_png(sample_label_data):
    """Test PNG generation."""
    label_id = sample_label_data["id"]
    png_path = generate_png(sample_label_data, label_id)
    
    # Check that the file exists
    assert os.path.exists(png_path)
    
    # Check that it's a PNG file
    with open(png_path, "rb") as f:
        header = f.read(8)
        assert header == b"\x89PNG\r\n\x1a\n"
    
    # Clean up
    os.remove(png_path)


def test_generate_html(sample_label_data):
    """Test HTML generation."""
    label_id = sample_label_data["id"]
    html_path = generate_html(sample_label_data, label_id)
    
    # Check that the file exists
    assert os.path.exists(html_path)
    
    # Check that it's an HTML file
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "<!DOCTYPE html>" in content
        assert "<html" in content
        assert sample_label_data["recipe_title"] in content
    
    # Clean up
    os.remove(html_path)


def test_generate_label_files(sample_label_data):
    """Test generating all label files."""
    pdf_path, png_path, html_path = generate_label_files(sample_label_data)
    
    # Check that all files exist
    assert os.path.exists(pdf_path)
    assert os.path.exists(png_path)
    assert os.path.exists(html_path)
    
    # Clean up
    os.remove(pdf_path)
    os.remove(png_path)
    os.remove(html_path)


def test_label_with_hidden_business_info(sample_label_data):
    """Test label generation with hidden business info."""
    # Modify the sample data to hide business info
    sample_label_data["label_sections"]["hide_business_info"] = True
    
    label_id = sample_label_data["id"]
    html_path = generate_html(sample_label_data, label_id)
    
    # Check that the file exists
    assert os.path.exists(html_path)
    
    # Check that business info is not in the HTML
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert sample_label_data["business_info"]["business_name"] not in content
    
    # Clean up
    os.remove(html_path)


def test_label_with_allergens(sample_label_data):
    """Test label generation with allergens."""
    label_id = sample_label_data["id"]
    html_path = generate_html(sample_label_data, label_id)
    
    # Check that the file exists
    assert os.path.exists(html_path)
    
    # Check that allergens are in the HTML
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
        for allergen in sample_label_data["allergens"]:
            assert allergen in content
    
    # Clean up
    os.remove(html_path)


def test_label_with_custom_colors(sample_label_data):
    """Test label generation with custom colors."""
    # Modify the sample data to use custom colors
    sample_label_data["label_style"]["text_color"] = "#FF0000"
    sample_label_data["label_style"]["background_color"] = "#0000FF"
    
    label_id = sample_label_data["id"]
    html_path = generate_html(sample_label_data, label_id)
    
    # Check that the file exists
    assert os.path.exists(html_path)
    
    # Check that custom colors are in the HTML
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "#FF0000" in content
        assert "#0000FF" in content
    
    # Clean up
    os.remove(html_path)