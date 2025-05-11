"""
Label generator service.

This service handles the generation of USDA Approved Labels in different formats:
- PDF
- PNG
- HTML
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Tuple, Optional
from pathlib import Path
import json

# PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

# Image generation
from PIL import Image, ImageDraw, ImageFont

# HTML generation
import jinja2

# Base directory for temporary files
# Use a relative path from the project root for better portability
TEMP_DIR = Path(__file__).parent.parent / "temp"

# Ensure temp directory exists
TEMP_DIR.mkdir(exist_ok=True)

# Set up Jinja2 environment
template_loader = jinja2.FileSystemLoader(searchpath=Path(__file__).parent.parent / "templates")
template_env = jinja2.Environment(loader=template_loader)


def generate_label_files(label_data: Dict) -> Tuple[str, str, str]:
    """
    Generate label files in different formats.
    
    Args:
        label_data: The label data
        
    Returns:
        Tuple containing:
            - Path to the PDF file
            - Path to the PNG file
            - Path to the HTML file
    """
    # Ensure nutrition_adjustments exists and has default values
    if 'nutrition_adjustments' not in label_data:
        label_data['nutrition_adjustments'] = {}
    
    # Set default values for all nutrition fields
    default_nutrition = {
        'calories': 0,
        'fat': 0,
        'saturated_fat': 0,
        'trans_fat': 0,
        'cholesterol': 0,
        'sodium': 0,
        'carbohydrates': 0,
        'dietary_fiber': 0,
        'sugars': 0,
        'added_sugars': 0,
        'protein': 0,
        'vitamin_d': 0,
        'calcium': 0,
        'iron': 0,
        'potassium': 0,
        'vitamin_a': 0,
        'vitamin_c': 0,
        'vitamin_e': 0,
        'vitamin_k': 0
    }
    
    # Update nutrition_adjustments with default values for missing fields
    for key, default_value in default_nutrition.items():
        if key not in label_data['nutrition_adjustments'] or label_data['nutrition_adjustments'][key] is None:
            label_data['nutrition_adjustments'][key] = default_value
    
    # Ensure label_sections exists
    if 'label_sections' not in label_data:
        label_data['label_sections'] = {}
    
    # Ensure label_style exists
    if 'label_style' not in label_data:
        label_data['label_style'] = {}
    
    # Generate a unique ID for the files
    label_id = label_data.get("id", str(uuid.uuid4()))
    
    # Generate the files
    pdf_path = generate_pdf(label_data, label_id)
    png_path = generate_png(label_data, label_id)
    html_path = generate_html(label_data, label_id)
    
    return pdf_path, png_path, html_path


def generate_pdf(label_data: Dict, label_id: str) -> str:
    """
    Generate a PDF version of the label.
    
    Args:
        label_data: The label data
        label_id: Unique identifier for the label
        
    Returns:
        Path to the generated PDF file
    """
    # Create the PDF file path
    pdf_path = TEMP_DIR / f"{label_id}.pdf"
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading_style = styles["Heading1"]
    normal_style = styles["Normal"]
    
    # Create the content
    content = []
    
    # Add the title
    content.append(Paragraph(label_data["recipe_title"], title_style))
    content.append(Spacer(1, 12))
    
    # Add the Nutrition Facts header
    content.append(Paragraph("Nutrition Facts", heading_style))
    content.append(Spacer(1, 12))
    
    # Add serving size information if available
    if "label_style" in label_data and "serving_size_en" in label_data["label_style"]:
        content.append(Paragraph(f"Serving Size: {label_data['label_style']['serving_size_en']}", normal_style))
        if "servings_per_package" in label_data["label_style"]:
            content.append(Paragraph(f"Servings Per Container: {label_data['label_style']['servings_per_package']}", normal_style))
        content.append(Spacer(1, 12))
    
    # Get nutrition adjustments with defaults
    nutrition = label_data.get('nutrition_adjustments', {})
    calories = nutrition.get('calories', 0)
    if calories is None: calories = 0
    
    fat = nutrition.get('fat', 0)
    if fat is None: fat = 0
    
    saturated_fat = nutrition.get('saturated_fat', 0)
    if saturated_fat is None: saturated_fat = 0
    
    trans_fat = nutrition.get('trans_fat', 0)
    if trans_fat is None: trans_fat = 0
    
    cholesterol = nutrition.get('cholesterol', 0)
    if cholesterol is None: cholesterol = 0
    
    sodium = nutrition.get('sodium', 0)
    if sodium is None: sodium = 0
    
    carbohydrates = nutrition.get('carbohydrates', 0)
    if carbohydrates is None: carbohydrates = 0
    
    dietary_fiber = nutrition.get('dietary_fiber', 0)
    if dietary_fiber is None: dietary_fiber = 0
    
    sugars = nutrition.get('sugars', 0)
    if sugars is None: sugars = 0
    
    protein = nutrition.get('protein', 0)
    if protein is None: protein = 0
    
    # Create nutrition facts table data
    table_data = [
        ["Amount Per Serving", ""],
        ["Calories", f"{calories}"],
        ["% Daily Value*", ""],
        ["Total Fat", f"{fat}g", f"{int(fat * 100 / 65)}%" if fat > 0 else "0%"],
        ["Saturated Fat", f"{saturated_fat}g", f"{int(saturated_fat * 100 / 20)}%" if saturated_fat > 0 else "0%"],
        ["Trans Fat", f"{trans_fat}g", ""],
        ["Cholesterol", f"{cholesterol}mg", f"{int(cholesterol * 100 / 300)}%" if cholesterol > 0 else "0%"],
        ["Sodium", f"{sodium}mg", f"{int(sodium * 100 / 2400)}%" if sodium > 0 else "0%"],
        ["Total Carbohydrate", f"{carbohydrates}g", f"{int(carbohydrates * 100 / 300)}%" if carbohydrates > 0 else "0%"],
        ["Dietary Fiber", f"{dietary_fiber}g", f"{int(dietary_fiber * 100 / 25)}%" if dietary_fiber > 0 else "0%"],
        ["Total Sugars", f"{sugars}g", ""],
        ["Protein", f"{protein}g", ""]
    ]
    
    # Create the table
    table = Table(table_data, colWidths=[200, 100, 100])
    
    # Style the table
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BACKGROUND', (0, 2), (-1, 2), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTNAME', (0, 3), (0, -1), 'Helvetica-Bold'),
    ])
    table.setStyle(table_style)
    
    # Add the table to the content
    content.append(table)
    content.append(Spacer(1, 12))
    
    # Add footnote
    content.append(Paragraph("* The % Daily Value tells you how much a nutrient in a serving of food contributes to a daily diet. 2,000 calories a day is used for general nutrition advice.", normal_style))
    
    # Add allergen information if available
    if "allergens" in label_data and label_data["allergens"]:
        content.append(Spacer(1, 12))
        content.append(Paragraph("Contains: " + ", ".join(label_data["allergens"]), normal_style))
    
    # Add facility allergen information if available
    if "facility_allergens" in label_data and label_data["facility_allergens"]:
        content.append(Spacer(1, 12))
        content.append(Paragraph("Manufactured in a facility that also processes: " + ", ".join(label_data["facility_allergens"]), normal_style))
    
    # Add business information if not hidden
    if not (label_data.get("label_sections", {}).get("hide_business_info", False)):
        if "business_info" in label_data and label_data["business_info"]:
            content.append(Spacer(1, 24))
            business_name = label_data["business_info"].get("business_name", "")
            business_address = label_data["business_info"].get("address", "")
            content.append(Paragraph(f"{business_name}", normal_style))
            if business_address:
                content.append(Paragraph(f"{business_address}", normal_style))
    
    # Build the PDF
    doc.build(content)
    
    return str(pdf_path)


def generate_png(label_data: Dict, label_id: str) -> str:
    """
    Generate a PNG version of the label.
    
    Args:
        label_data: The label data
        label_id: Unique identifier for the label
        
    Returns:
        Path to the generated PNG file
    """
    # Create the PNG file path
    png_path = TEMP_DIR / f"{label_id}.png"
    
    # Create a blank image
    width, height = 600, 800
    background_color = label_data.get("label_style", {}).get("background_color", "#FFFFFF")
    text_color = label_data.get("label_style", {}).get("text_color", "#000000")
    
    # Convert hex colors to RGB
    bg_color = tuple(int(background_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    txt_color = tuple(int(text_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    
    # Create the image
    image = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(image)
    
    # Try to load fonts, use default if not available
    try:
        title_font = ImageFont.truetype("arial.ttf", 24)
        heading_font = ImageFont.truetype("arial.ttf", 20)
        normal_font = ImageFont.truetype("arial.ttf", 16)
        small_font = ImageFont.truetype("arial.ttf", 12)
    except IOError:
        title_font = ImageFont.load_default()
        heading_font = ImageFont.load_default()
        normal_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Draw the title
    draw.text((30, 30), label_data["recipe_title"], fill=txt_color, font=title_font)
    
    # Draw the Nutrition Facts header
    draw.text((30, 70), "Nutrition Facts", fill=txt_color, font=heading_font)
    
    # Draw serving size information if available
    y_pos = 110
    if "label_style" in label_data and "serving_size_en" in label_data["label_style"]:
        draw.text((30, y_pos), f"Serving Size: {label_data['label_style']['serving_size_en']}", fill=txt_color, font=normal_font)
        y_pos += 25
        if "servings_per_package" in label_data["label_style"]:
            draw.text((30, y_pos), f"Servings Per Container: {label_data['label_style']['servings_per_package']}", fill=txt_color, font=normal_font)
            y_pos += 25
    
    # Draw a line
    draw.line((30, y_pos, width - 30, y_pos), fill=txt_color, width=2)
    y_pos += 10
    
    # Draw Amount Per Serving
    draw.text((30, y_pos), "Amount Per Serving", fill=txt_color, font=normal_font)
    y_pos += 25
    
    # Draw Calories
    draw.text((30, y_pos), "Calories", fill=txt_color, font=normal_font)
    calories = label_data.get('nutrition_adjustments', {}).get('calories', 0)
    if calories is None: calories = 0
    draw.text((width - 100, y_pos), f"{calories}", fill=txt_color, font=normal_font)
    y_pos += 25
    
    # Draw a line
    draw.line((30, y_pos, width - 30, y_pos), fill=txt_color, width=2)
    y_pos += 10
    
    # Draw % Daily Value
    draw.text((width - 150, y_pos), "% Daily Value*", fill=txt_color, font=normal_font)
    y_pos += 25
    
    # Get nutrition adjustments with defaults
    nutrition = label_data.get('nutrition_adjustments', {})
    fat = nutrition.get('fat', 0)
    if fat is None: fat = 0
    
    saturated_fat = nutrition.get('saturated_fat', 0)
    if saturated_fat is None: saturated_fat = 0
    
    trans_fat = nutrition.get('trans_fat', 0)
    if trans_fat is None: trans_fat = 0
    
    cholesterol = nutrition.get('cholesterol', 0)
    if cholesterol is None: cholesterol = 0
    
    sodium = nutrition.get('sodium', 0)
    if sodium is None: sodium = 0
    
    carbohydrates = nutrition.get('carbohydrates', 0)
    if carbohydrates is None: carbohydrates = 0
    
    dietary_fiber = nutrition.get('dietary_fiber', 0)
    if dietary_fiber is None: dietary_fiber = 0
    
    sugars = nutrition.get('sugars', 0)
    if sugars is None: sugars = 0
    
    protein = nutrition.get('protein', 0)
    if protein is None: protein = 0
    
    # Draw nutrition facts
    nutrients = [
        ("Total Fat", f"{fat}g", f"{int(fat * 100 / 65)}%" if fat > 0 else "0%"),
        ("Saturated Fat", f"{saturated_fat}g", f"{int(saturated_fat * 100 / 20)}%" if saturated_fat > 0 else "0%"),
        ("Trans Fat", f"{trans_fat}g", ""),
        ("Cholesterol", f"{cholesterol}mg", f"{int(cholesterol * 100 / 300)}%" if cholesterol > 0 else "0%"),
        ("Sodium", f"{sodium}mg", f"{int(sodium * 100 / 2400)}%" if sodium > 0 else "0%"),
        ("Total Carbohydrate", f"{carbohydrates}g", f"{int(carbohydrates * 100 / 300)}%" if carbohydrates > 0 else "0%"),
        ("Dietary Fiber", f"{dietary_fiber}g", f"{int(dietary_fiber * 100 / 25)}%" if dietary_fiber > 0 else "0%"),
        ("Total Sugars", f"{sugars}g", ""),
        ("Protein", f"{protein}g", "")
    ]
    
    for nutrient, value, daily_value in nutrients:
        draw.text((30, y_pos), nutrient, fill=txt_color, font=normal_font)
        draw.text((width - 200, y_pos), value, fill=txt_color, font=normal_font)
        if daily_value:
            draw.text((width - 100, y_pos), daily_value, fill=txt_color, font=normal_font)
        y_pos += 25
    
    # Draw a line
    draw.line((30, y_pos, width - 30, y_pos), fill=txt_color, width=1)
    y_pos += 15
    
    # Draw footnote
    footnote = "* The % Daily Value tells you how much a nutrient in a serving of food contributes to a daily diet. 2,000 calories a day is used for general nutrition advice."
    # Wrap text to fit width
    words = footnote.split()
    lines = []
    line = []
    for word in words:
        if draw.textlength(" ".join(line + [word]), font=small_font) <= width - 60:
            line.append(word)
        else:
            lines.append(" ".join(line))
            line = [word]
    if line:
        lines.append(" ".join(line))
    
    for line in lines:
        draw.text((30, y_pos), line, fill=txt_color, font=small_font)
        y_pos += 15
    
    y_pos += 10
    
    # Draw allergen information if available
    if "allergens" in label_data and label_data["allergens"]:
        draw.text((30, y_pos), "Contains: " + ", ".join(label_data["allergens"]), fill=txt_color, font=normal_font)
        y_pos += 25
    
    # Draw facility allergen information if available
    if "facility_allergens" in label_data and label_data["facility_allergens"]:
        facility_text = "Manufactured in a facility that also processes: " + ", ".join(label_data["facility_allergens"])
        # Wrap text to fit width
        words = facility_text.split()
        lines = []
        line = []
        for word in words:
            if draw.textlength(" ".join(line + [word]), font=small_font) <= width - 60:
                line.append(word)
            else:
                lines.append(" ".join(line))
                line = [word]
        if line:
            lines.append(" ".join(line))
        
        for line in lines:
            draw.text((30, y_pos), line, fill=txt_color, font=small_font)
            y_pos += 15
    
    # Draw business information if not hidden
    if not (label_data.get("label_sections", {}).get("hide_business_info", False)):
        if "business_info" in label_data and label_data["business_info"]:
            y_pos += 10
            business_name = label_data["business_info"].get("business_name", "")
            business_address = label_data["business_info"].get("address", "")
            draw.text((30, y_pos), business_name, fill=txt_color, font=normal_font)
            y_pos += 25
            if business_address:
                draw.text((30, y_pos), business_address, fill=txt_color, font=normal_font)
    
    # Save the image
    image.save(png_path)
    
    return str(png_path)


def generate_html(label_data: Dict, label_id: str) -> str:
    """
    Generate an HTML version of the label.
    
    Args:
        label_data: The label data
        label_id: Unique identifier for the label
        
    Returns:
        Path to the generated HTML file
    """
    # Create the HTML file path
    html_path = TEMP_DIR / f"{label_id}.html"
    
    # Create templates directory if it doesn't exist
    templates_dir = Path(__file__).parent.parent / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    # Check if the template exists, if not create it
    template_path = templates_dir / "label_template.html"
    if not template_path.exists():
        create_html_template(template_path)
    
    # Load the template
    template = template_env.get_template("label_template.html")
    
    # Get the nutrition adjustments (already defaulted in generate_label_files)
    nutrition_adjustments = label_data.get('nutrition_adjustments', {})
    
    # Calculate daily values percentages
    try:
        fat = nutrition_adjustments.get('fat', 0)
        if fat is None: fat = 0
        
        saturated_fat = nutrition_adjustments.get('saturated_fat', 0)
        if saturated_fat is None: saturated_fat = 0
        
        cholesterol = nutrition_adjustments.get('cholesterol', 0)
        if cholesterol is None: cholesterol = 0
        
        sodium = nutrition_adjustments.get('sodium', 0)
        if sodium is None: sodium = 0
        
        carbohydrates = nutrition_adjustments.get('carbohydrates', 0)
        if carbohydrates is None: carbohydrates = 0
        
        dietary_fiber = nutrition_adjustments.get('dietary_fiber', 0)
        if dietary_fiber is None: dietary_fiber = 0
        
        vitamin_d = nutrition_adjustments.get('vitamin_d', 0)
        if vitamin_d is None: vitamin_d = 0
        
        calcium = nutrition_adjustments.get('calcium', 0)
        if calcium is None: calcium = 0
        
        iron = nutrition_adjustments.get('iron', 0)
        if iron is None: iron = 0
        
        potassium = nutrition_adjustments.get('potassium', 0)
        if potassium is None: potassium = 0
        
        daily_values = {
            "fat": int(fat * 100 / 65) if fat > 0 else 0,
            "saturated_fat": int(saturated_fat * 100 / 20) if saturated_fat > 0 else 0,
            "cholesterol": int(cholesterol * 100 / 300) if cholesterol > 0 else 0,
            "sodium": int(sodium * 100 / 2400) if sodium > 0 else 0,
            "carbohydrates": int(carbohydrates * 100 / 300) if carbohydrates > 0 else 0,
            "dietary_fiber": int(dietary_fiber * 100 / 25) if dietary_fiber > 0 else 0,
            "vitamin_d": int(vitamin_d * 100 / 20) if vitamin_d > 0 else 0,
            "calcium": int(calcium * 100 / 1300) if calcium > 0 else 0,
            "iron": int(iron * 100 / 18) if iron > 0 else 0,
            "potassium": int(potassium * 100 / 4700) if potassium > 0 else 0
        }
    except Exception as e:
        # If any calculation fails, use default values
        print(f"Error calculating daily values: {str(e)}")
        daily_values = {
            "fat": 0, "saturated_fat": 0, "cholesterol": 0, "sodium": 0,
            "carbohydrates": 0, "dietary_fiber": 0, "vitamin_d": 0,
            "calcium": 0, "iron": 0, "potassium": 0
        }
    
    # Ensure label_style exists
    if 'label_style' not in label_data:
        label_data['label_style'] = {}
    
    # Ensure label_sections exists
    if 'label_sections' not in label_data:
        label_data['label_sections'] = {}
    
    # Render the template with the label data
    html_content = template.render(
        label_data=label_data,
        daily_values=daily_values,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    
    # Write the HTML file
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return str(html_path)


def create_html_template(template_path: Path) -> None:
    """
    Create the HTML template file.
    
    Args:
        template_path: Path to the template file
    """
    template_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ label_data.recipe_title }} - Nutrition Facts</title>
    <style>
        body {
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: {{ label_data.label_style.background_color|default('#FFFFFF') }};
            color: {{ label_data.label_style.text_color|default('#000000') }};
        }
        .label-container {
            width: 300px;
            margin: 20px auto;
            padding: 0;
            box-sizing: border-box;
        }
        .recipe-title {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
            text-align: center;
        }
        #newnutritionfactstable {
            width: 100%;
            border: 0;
            padding: 0;
            margin-bottom: 20px;
        }
        #newnutritionheading {
            font-size: 28px;
            font-weight: 900;
            line-height: 1.1;
            padding-bottom: 4px;
        }
        .hairlineseparator {
            height: 1px;
            background-color: #000;
            margin: 2px 0;
        }
        .thickseparator {
            height: 10px;
            background-color: #000;
            margin: 2px 0;
        }
        .separator {
            height: 1px;
            background-color: #000;
            margin: 2px 0;
        }
        .servingsize {
            padding: 5px 0;
        }
        .servingsizenew {
            padding-top: 2px;
            padding-bottom: 6px;
        }
        .servingsizenew-bold {
            font-weight: 900;
            font-size: 16px;
            padding-top: 3px;
        }
        .servings-per-container-div {
            display: block;
            padding-bottom: 6px;
        }
        .clearfix {
            clear: both;
        }
        .nutrient {
            font-weight: 700;
            padding: 2px 0;
        }
        .new-calories {
            font-size: 16px;
            font-weight: 900;
            padding: 6px 0;
            position: relative;
        }
        .calories {
            position: absolute;
            right: 0;
            top: 0;
            font-size: 32px;
            font-weight: 900;
        }
        .newdailyvalue {
            text-align: right;
            font-weight: 700;
            padding: 6px 0;
        }
        .new-vertical-row {
            position: relative;
            padding: 2px 0;
        }
        .pull-left {
            float: left;
            width: 75%;
        }
        .pull-right {
            float: right;
            width: 25%;
            text-align: right;
        }
        .nutrientsubgroup {
            padding-left: 20px;
            font-weight: 400;
        }
        .nutrientsubsubgroup {
            padding-left: 40px;
            font-weight: 400;
        }
        .nutrientcontent {
            float: right;
            padding-right: 10px;
        }
        .subsubhairlineseparator {
            height: 1px;
            background-color: #000;
            margin: 2px 0;
            opacity: 0.5;
        }
        .label-footnote-section {
            padding-top: 10px;
        }
        .footnote-separator {
            height: 1px;
            background-color: #000;
            margin: 5px 0;
        }
        .asterisksection-new-vertical {
            position: relative;
            padding: 5px 0;
            font-size: 12px;
        }
        .asterisk {
            position: absolute;
            left: 0;
            top: 5px;
        }
        .asterisk_text {
            margin-left: 10px;
            font-size: 10px;
        }
        #ingredientsandallergens {
            margin-top: 20px;
        }
        #recipe-show-ingredient-list {
            margin-bottom: 10px;
            font-size: 14px;
            text-transform: uppercase;
            text-align: justify;
        }
        #allergen-list {
            margin-bottom: 10px;
            font-size: 14px;
            text-transform: uppercase;
            font-weight: bold;
        }
        #facility-allergen-list {
            margin-bottom: 10px;
            font-size: 12px;
            text-transform: uppercase;
        }
        #manufacture-address {
            margin-top: 20px;
            font-size: 12px;
            text-transform: uppercase;
        }
        .timestamp {
            font-size: 10px;
            color: #999;
            text-align: right;
            margin-top: 20px;
        }
        /* Added styles for vitamins section */
        #newverticalvitaminsection {
            margin-top: 10px;
        }
        /* Added styles for added sugars */
        .added-sugar-grams {
            white-space: nowrap;
        }
    </style>
</head>
<body>
    <div class="label-container">
        {% if not label_data.label_sections.hide_recipe_title|default(false) %}
        <div class="recipe-title">{{ label_data.recipe_title }}</div>
        {% endif %}
        
        {% if not label_data.label_sections.hide_nutrition_facts|default(false) %}
        <div id="newnutritionfactstable">
            <div id="newnutritionheading">
                Nutrition Facts
            </div>
            <div class="hairlineseparator"></div>
            <div class="servingsize servingsizenew">
                <span class="servings-per-container-div">
                    <span class="servings-per-container">
                        {{ label_data.label_style.servings_per_package|default('1') }}
                    </span>
                    servings per container
                </span>
                <div class="servingsizenew-bold">
                    <div style="float:left;">Serving size</div>
                    <div style="float:right;">
                        {{ label_data.label_style.serving_size_en|default('1 serving') }}
                        {% if label_data.label_style.serving_size_weight|default('') %}
                        ({{ label_data.label_style.serving_size_weight }})
                        {% endif %}
                    </div>
                    <div class="clearfix"></div>
                </div>
            </div>
            <div class="thickseparator"></div>
            <div class="nutrient">Amount Per Serving</div>
            <div class="nutrient new-calories">
                Calories
                <div class="calories">{{ label_data.nutrition_adjustments.calories }}</div>
            </div>
            <div class="separator"></div>
            <div class="newdailyvalue">
                % Daily Value*
            </div>
            <div class="clearfix"></div>
            
            <!-- Total Fat -->
            <div class="new-vertical-row">
                <div class="hairlineseparator"></div>
                <div class="pull-left">
                    <div class="nutrient">
                        <span>Total Fat</span>
                        <span class="nutrientcontent">{{ label_data.nutrition_adjustments.fat }}g</span>
                    </div>
                </div>
                <div class="pull-right">
                    <div class="nutrient">%</div>
                    <div class="nutrient">{{ daily_values.fat }}</div>
                </div>
                <div class="clearfix"></div>
            </div>
            
            <!-- Saturated Fat -->
            <div class="new-vertical-row">
                <div class="hairlineseparator"></div>
                <div class="pull-left">
                    <div class="nutrientsubgroup">
                        <span>Saturated Fat</span>
                        <span class="nutrientcontent">{{ label_data.nutrition_adjustments.saturated_fat }}g</span>
                    </div>
                </div>
                <div class="pull-right">
                    <div class="nutrient">%</div>
                    <div class="nutrient">{{ daily_values.saturated_fat }}</div>
                </div>
                <div class="clearfix"></div>
            </div>
            
            <!-- Trans Fat -->
            <div class="new-vertical-row">
                <div class="hairlineseparator"></div>
                <div class="pull-left">
                    <div class="nutrientsubgroup">
                        <span><i>Trans</i> Fat</span>
                        <span class="nutrientcontent">{{ label_data.nutrition_adjustments.trans_fat }}g</span>
                    </div>
                </div>
                <div class="clearfix"></div>
            </div>
            
            <!-- Cholesterol -->
            <div class="new-vertical-row">
                <div class="hairlineseparator"></div>
                <div class="pull-left">
                    <div class="nutrient">
                        <span>Cholesterol</span>
                        <span class="nutrientcontent">{{ label_data.nutrition_adjustments.cholesterol }}mg</span>
                    </div>
                </div>
                <div class="pull-right">
                    <div class="nutrient">%</div>
                    <div class="nutrient">{{ daily_values.cholesterol }}</div>
                </div>
                <div class="clearfix"></div>
            </div>
            
            <!-- Sodium -->
            <div class="new-vertical-row">
                <div class="hairlineseparator"></div>
                <div class="pull-left">
                    <div class="nutrient">
                        <span>Sodium</span>
                        <span class="nutrientcontent">{{ label_data.nutrition_adjustments.sodium }}mg</span>
                    </div>
                </div>
                <div class="pull-right">
                    <div class="nutrient">%</div>
                    <div class="nutrient">{{ daily_values.sodium }}</div>
                </div>
                <div class="clearfix"></div>
            </div>
            
            <!-- Total Carbohydrate -->
            <div class="new-vertical-row">
                <div class="hairlineseparator"></div>
                <div class="pull-left">
                    <div class="nutrient">
                        <span>Total Carbohydrate</span>
                        <span class="nutrientcontent">{{ label_data.nutrition_adjustments.carbohydrates }}g</span>
                    </div>
                </div>
                <div class="pull-right">
                    <div class="nutrient">%</div>
                    <div class="nutrient">{{ daily_values.carbohydrates }}</div>
                </div>
                <div class="clearfix"></div>
            </div>
            
            <!-- Dietary Fiber -->
            <div class="new-vertical-row">
                <div class="hairlineseparator"></div>
                <div class="pull-left">
                    <div class="nutrientsubgroup">
                        <span>Dietary Fiber</span>
                        <span class="nutrientcontent">{{ label_data.nutrition_adjustments.dietary_fiber }}g</span>
                    </div>
                </div>
                <div class="pull-right">
                    <div class="nutrient">%</div>
                    <div class="nutrient">{{ daily_values.dietary_fiber }}</div>
                </div>
                <div class="clearfix"></div>
            </div>
            
            <!-- Total Sugars -->
            <div class="new-vertical-row">
                <div class="hairlineseparator"></div>
                <div class="pull-left">
                    <div class="nutrientsubgroup">
                        <span>Total Sugars</span>
                        <span class="nutrientcontent">{{ label_data.nutrition_adjustments.sugars }}g</span>
                    </div>
                </div>
                <div class="clearfix"></div>
            </div>
            
            <!-- Added Sugars (if available) -->
            {% if label_data.nutrition_adjustments.added_sugars|default(0) > 0 %}
            <div class="new-vertical-row">
                <div class="subsubhairlineseparator"></div>
                <div class="pull-left">
                    <div class="nutrientsubsubgroup added-sugar-grams">
                        <span>Includes</span>
                        <span class="nutrientcontent">{{ label_data.nutrition_adjustments.added_sugars }}g</span>
                        <span>Added Sugars</span>
                    </div>
                </div>
                <div class="pull-right">
                    <div class="nutrient">%</div>
                    <div class="nutrient">{{ (label_data.nutrition_adjustments.added_sugars * 100 / 50)|int }}</div>
                </div>
                <div class="clearfix"></div>
            </div>
            {% endif %}
            
            <!-- Protein -->
            <div class="new-vertical-row">
                <div class="hairlineseparator"></div>
                <div class="pull-left">
                    <div class="nutrient">
                        Protein
                        <span class="nutrientcontent">{{ label_data.nutrition_adjustments.protein }}g</span>
                    </div>
                </div>
                <div class="clearfix"></div>
            </div>
            
            <!-- Vitamins and Minerals Section -->
            <div id="newverticalvitaminsection">
                <div class="thickseparator"></div>
                {% if label_data.nutrition_adjustments.vitamin_d|default(0) > 0 %}
                <div class="new-vertical-row">
                    <div class="pull-left">
                        <div class="nutrientcontent">Vitamin D {{ label_data.nutrition_adjustments.vitamin_d }}mcg</div>
                    </div>
                    <div class="pull-right">
                        <div class="nutrientcontent">{{ (label_data.nutrition_adjustments.vitamin_d * 100 / 20)|int }}%</div>
                    </div>
                    <div class="clearfix"></div>
                </div>
                <div class="hairlineseparator"></div>
                {% endif %}
                
                {% if label_data.nutrition_adjustments.calcium|default(0) > 0 %}
                <div class="new-vertical-row">
                    <div class="pull-left">
                        <div class="nutrientcontent">Calcium {{ label_data.nutrition_adjustments.calcium }}mg</div>
                    </div>
                    <div class="pull-right">
                        <div class="nutrientcontent">{{ (label_data.nutrition_adjustments.calcium * 100 / 1300)|int }}%</div>
                    </div>
                    <div class="clearfix"></div>
                </div>
                <div class="hairlineseparator"></div>
                {% endif %}
                
                {% if label_data.nutrition_adjustments.iron|default(0) > 0 %}
                <div class="new-vertical-row">
                    <div class="pull-left">
                        <div class="nutrientcontent">Iron {{ label_data.nutrition_adjustments.iron }}mg</div>
                    </div>
                    <div class="pull-right">
                        <div class="nutrientcontent">{{ (label_data.nutrition_adjustments.iron * 100 / 18)|int }}%</div>
                    </div>
                    <div class="clearfix"></div>
                </div>
                <div class="hairlineseparator"></div>
                {% endif %}
                
                {% if label_data.nutrition_adjustments.potassium|default(0) > 0 %}
                <div class="new-vertical-row">
                    <div class="pull-left">
                        <div class="nutrientcontent">Potassium {{ label_data.nutrition_adjustments.potassium }}mg</div>
                    </div>
                    <div class="pull-right">
                        <div class="nutrientcontent">{{ (label_data.nutrition_adjustments.potassium * 100 / 4700)|int }}%</div>
                    </div>
                    <div class="clearfix"></div>
                </div>
                {% endif %}
            </div>
            
            <!-- Footnote Section -->
            <div class="label-footnote-section">
                <div class="footnote-separator"></div>
                <div class="asterisksection-new-vertical">
                    <div class="asterisk">*</div>
                    <div class="asterisk_text">The % Daily Value (DV) tells you how much a nutrient in a serving of food contributes to a daily diet. 2,000 calories a day is used for general nutrition advice.</div>
                    <div class="clearfix"></div>
                </div>
            </div>
        </div>
        {% endif %}
        
        <!-- Ingredients and Allergens Section -->
        <div id="ingredientsandallergens">
            {% if not label_data.label_sections.hide_ingredient_list|default(false) and label_data.ingredients_list|default('') %}
            <div id="recipe-show-ingredient-list">
                Ingredients: {{ label_data.ingredients_list }}
            </div>
            {% endif %}
            
            {% if not label_data.label_sections.hide_allergens|default(false) and label_data.allergens %}
            <div id="allergen-list">
                Contains: {{ label_data.allergens|join(', ') }}
            </div>
            {% endif %}
            
            {% if not label_data.label_sections.hide_facility_allergens|default(false) and label_data.facility_allergens %}
            <div id="facility-allergen-list">
                Manufactured in a facility that also processes: {{ label_data.facility_allergens|join(', ') }}
            </div>
            {% endif %}
        </div>
        
        <!-- Business Information Section -->
        {% if not label_data.label_sections.hide_business_info|default(false) and label_data.business_info %}
        <div id="manufacture-address">
            <div>{{ label_data.business_info.business_name }}</div>
            {% if label_data.business_info.address %}
            <div>{{ label_data.business_info.address }}</div>
            {% endif %}
        </div>
        {% endif %}
        
        <div class="timestamp">Generated: {{ timestamp }}</div>
    </div>
</body>
</html>
"""
    
    # Create the templates directory if it doesn't exist
    template_path.parent.mkdir(exist_ok=True)
    
    # Write the template file
    with open(template_path, "w", encoding="utf-8") as f:
        f.write(template_content)