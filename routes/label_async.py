"""
Async label generation routes.

This module defines the API endpoints for generating USDA Approved Labels.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict

from models import LabelInput, LabelOutput, LabelValidationError
from services.label_service_async import generate_label, check_label_requirements

router = APIRouter(
    prefix="/label",
    tags=["label"],
)


@router.post("/", response_model=LabelOutput, summary="Generate USDA Approved Label")
async def create_label(label_input: LabelInput) -> LabelOutput:
    """
    Generate a USDA Approved Label based on the provided recipe data and formatting options.
    
    The payload should include:
    - Recipe title
    - Recipe nutritional data
    - Label section visibility options
    - Label style options
    - Optional nutrients to display
    - Optional vitamins to display
    - Nutrition value adjustments
    - Label type
    - Business information
    - Allergens
    - Facility allergens
    
    Returns a URL to the generated label and the label data used for generation.
    If any required elements are missing, returns a 422 error with the list of missing elements.
    """
    # Check if the label input meets all requirements
    is_valid, validation_error = await check_label_requirements(label_input)
    
    if not is_valid:
        raise HTTPException(
            status_code=422,
            detail={
                "message": validation_error.detail,
                "missing_elements": validation_error.missing_elements
            }
        )
    
    try:
        return await generate_label(label_input)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating label: {str(e)}")