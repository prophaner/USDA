"""
Label generation routes.

This module defines the API endpoints for generating USDA Approved Labels.
"""

import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse, HTMLResponse
from typing import Dict

from models import LabelInput, LabelOutput, LabelValidationError
from services.label_service import generate_label, check_label_requirements

# Base directory for temporary files
TEMP_DIR = Path("C:/Users/LuisRamos/PycharmProjects/CuradoUSDA/temp")

router = APIRouter(
    prefix="/label",
    tags=["label"],
)


@router.post("/", response_model=LabelOutput, summary="Generate USDA Approved Label")
def create_label(label_input: LabelInput) -> LabelOutput:
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
    
    Returns URLs for accessing the generated label in different formats:
    - label_url: URL to view the label
    - pdf_download_url: URL to download the label as PDF
    - png_download_url: URL to download the label as PNG
    - embedded_html: HTML code to embed the label in a UI
    
    If any required elements are missing, returns a 422 error with the list of missing elements.
    """
    # Check if the label input meets all requirements
    is_valid, validation_error = check_label_requirements(label_input)
    
    if not is_valid:
        raise HTTPException(
            status_code=422,
            detail={
                "message": validation_error.detail,
                "missing_elements": validation_error.missing_elements
            }
        )
    
    try:
        return generate_label(label_input)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating label: {str(e)}")


@router.get("/{label_id}/download/pdf", summary="Download label as PDF")
def download_pdf(label_id: str):
    """
    Download the generated label as a PDF file.
    
    Args:
        label_id: The unique identifier of the label
        
    Returns:
        The PDF file for download
    """
    pdf_path = TEMP_DIR / f"{label_id}.pdf"
    
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Label not found")
    
    return FileResponse(
        path=str(pdf_path),
        filename=f"{label_id}.pdf",
        media_type="application/pdf"
    )


@router.get("/{label_id}/download/png", summary="Download label as PNG")
def download_png(label_id: str):
    """
    Download the generated label as a PNG image.
    
    Args:
        label_id: The unique identifier of the label
        
    Returns:
        The PNG image for download
    """
    png_path = TEMP_DIR / f"{label_id}.png"
    
    if not png_path.exists():
        raise HTTPException(status_code=404, detail="Label not found")
    
    return FileResponse(
        path=str(png_path),
        filename=f"{label_id}.png",
        media_type="image/png"
    )


@router.get("/{label_id}/embed", response_class=HTMLResponse, summary="Embed label as HTML")
def embed_label(label_id: str):
    """
    Get the HTML version of the label for embedding in a UI.
    
    Args:
        label_id: The unique identifier of the label
        
    Returns:
        The HTML content of the label
    """
    html_path = TEMP_DIR / f"{label_id}.html"
    
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Label not found")
    
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    return HTMLResponse(content=html_content)