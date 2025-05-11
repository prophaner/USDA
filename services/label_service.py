"""
Label generation service.

This service handles the creation of USDA Approved Labels based on recipe data
and user-specified formatting options.
"""

from typing import Dict, List, Optional, Tuple
import json
import uuid
import os
from datetime import datetime
from pathlib import Path

from models import (
    LabelInput, 
    LabelOutput, 
    LabelValidationError,
    RecipeOutput,
    BusinessInfo
)

from services.label_generator import generate_label_files


def validate_label_input(label_input: LabelInput) -> Tuple[bool, Optional[List[str]]]:
    """
    Validate the label input data.
    
    Args:
        label_input: The label input data to validate
        
    Returns:
        Tuple containing:
            - Boolean indicating if the input is valid
            - List of missing elements if any, None otherwise
    """
    missing_elements = []
    
    # Check required fields
    if not label_input.recipe_title:
        missing_elements.append("recipe_title")
    
    # Check recipe data
    if not label_input.recipe_data:
        missing_elements.append("recipe_data")
    elif not label_input.recipe_data.items:
        missing_elements.append("recipe_data.items")
    elif not label_input.recipe_data.total:
        missing_elements.append("recipe_data.total")
    
    # Check business info if not hidden
    if (not label_input.label_sections or 
        not label_input.label_sections.hide_business_info):
        if not label_input.business_info:
            missing_elements.append("business_info")
        elif not label_input.business_info.business_name:
            missing_elements.append("business_info.business_name")
    
    # Check if any required nutrients are missing
    required_nutrients = [
        "calories", "fat", "saturated_fat", "trans_fat", 
        "cholesterol", "sodium", "carbohydrates", 
        "dietary_fiber", "sugars", "protein"
    ]
    
    if label_input.recipe_data and label_input.recipe_data.total:
        for nutrient in required_nutrients:
            # Check if the nutrient is in the recipe data or in the adjustments
            nutrient_in_recipe = any(
                n.lower() == nutrient.replace("_", " ") 
                for n in label_input.recipe_data.total.keys()
            )
            
            nutrient_in_adjustments = (
                label_input.nutrition_adjustments and
                getattr(label_input.nutrition_adjustments, nutrient) is not None
            )
            
            if not nutrient_in_recipe and not nutrient_in_adjustments:
                missing_elements.append(f"nutrient.{nutrient}")
    
    return len(missing_elements) == 0, missing_elements if missing_elements else None


def generate_label(label_input: LabelInput) -> LabelOutput:
    """
    Generate a USDA Approved Label based on the input data.
    
    Args:
        label_input: The label input data
        
    Returns:
        LabelOutput containing the URL to the generated label and the label data
        
    Raises:
        ValueError: If the label input is invalid
    """
    # Validate the input
    is_valid, missing_elements = validate_label_input(label_input)
    if not is_valid:
        raise ValueError(f"Invalid label input: missing {', '.join(missing_elements)}")
    
    # Generate a unique ID for the label
    label_id = str(uuid.uuid4())
    
    # Create a timestamp for the label
    timestamp = datetime.now().isoformat()
    
    # Prepare the label data
    label_data = {
        "id": label_id,
        "timestamp": timestamp,
        "recipe_title": label_input.recipe_title,
        "recipe_data": label_input.recipe_data.model_dump(),
        "label_sections": label_input.label_sections.model_dump() if label_input.label_sections else {},
        "label_style": label_input.label_style.model_dump() if label_input.label_style else {},
        "optional_nutrients": label_input.optional_nutrients.model_dump() if label_input.optional_nutrients else {},
        "optional_vitamins": label_input.optional_vitamins.model_dump() if label_input.optional_vitamins else {},
        "nutrition_adjustments": label_input.nutrition_adjustments.model_dump() if label_input.nutrition_adjustments else {},
        "label_type": label_input.label_type,
        "business_info": label_input.business_info.model_dump() if label_input.business_info else {},
        "allergens": label_input.allergens if label_input.allergens else [],
        "facility_allergens": label_input.facility_allergens if label_input.facility_allergens else []
    }
    
    # Generate the label files
    pdf_path, png_path, html_path = generate_label_files(label_data)
    
    # Convert file paths to URLs
    base_url = "/api/labels"
    label_url = f"{base_url}/{label_id}"
    pdf_download_url = f"{base_url}/{label_id}/download/pdf"
    png_download_url = f"{base_url}/{label_id}/download/png"
    
    # Generate an HTML embed code for the label
    embedded_html = f"""
    <iframe 
        src="{label_url}/embed" 
        width="100%" 
        height="600" 
        frameborder="0" 
        scrolling="no" 
        allowfullscreen>
    </iframe>
    """
    
    return LabelOutput(
        label_url=label_url,
        pdf_download_url=pdf_download_url,
        png_download_url=png_download_url,
        embedded_html=embedded_html,
        label_data=label_data,
        missing_elements=None
    )


def check_label_requirements(label_input: LabelInput) -> Tuple[bool, Optional[LabelValidationError]]:
    """
    Check if the label input meets all requirements.
    
    Args:
        label_input: The label input data to check
        
    Returns:
        Tuple containing:
            - Boolean indicating if the input meets all requirements
            - LabelValidationError if any requirements are not met, None otherwise
    """
    is_valid, missing_elements = validate_label_input(label_input)
    
    if not is_valid:
        return False, LabelValidationError(
            detail="Label input is missing required elements",
            missing_elements=missing_elements
        )
    
    return True, None