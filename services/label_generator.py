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
TEMP_DIR = Path("C:/Users/LuisRamos/PycharmProjects/CuradoUSDA/temp")

# Ensure temp directory exists
TEMP_DIR.mkdir(exist_ok=True)

# Set up Jinja2 environment
template_loader = jinja2.FileSystemLoader(searchpath="C:/Users/LuisRamos/PycharmProjects/CuradoUSDA/templates")
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
    
    # Create nutrition facts table data
    table_data = [
        ["Amount Per Serving", ""],
        ["Calories", f"{label_data['nutrition_adjustments']['calories']}"],
        ["% Daily Value*", ""],
        ["Total Fat", f"{label_data['nutrition_adjustments']['fat']}g", f"{int(label_data['nutrition_adjustments']['fat'] * 100 / 65)}%"],
        ["Saturated Fat", f"{label_data['nutrition_adjustments']['saturated_fat']}g", f"{int(label_data['nutrition_adjustments']['saturated_fat'] * 100 / 20)}%"],
        ["Trans Fat", f"{label_data['nutrition_adjustments']['trans_fat']}g", ""],
        ["Cholesterol", f"{label_data['nutrition_adjustments']['cholesterol']}mg", f"{int(label_data['nutrition_adjustments']['cholesterol'] * 100 / 300)}%"],
        ["Sodium", f"{label_data['nutrition_adjustments']['sodium']}mg", f"{int(label_data['nutrition_adjustments']['sodium'] * 100 / 2400)}%"],
        ["Total Carbohydrate", f"{label_data['nutrition_adjustments']['carbohydrates']}g", f"{int(label_data['nutrition_adjustments']['carbohydrates'] * 100 / 300)}%"],
        ["Dietary Fiber", f"{label_data['nutrition_adjustments']['dietary_fiber']}g", f"{int(label_data['nutrition_adjustments']['dietary_fiber'] * 100 / 25)}%"],
        ["Total Sugars", f"{label_data['nutrition_adjustments']['sugars']}g", ""],
        ["Protein", f"{label_data['nutrition_adjustments']['protein']}g", ""]
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
    draw.text((width - 100, y_pos), f"{label_data['nutrition_adjustments']['calories']}", fill=txt_color, font=normal_font)
    y_pos += 25
    
    # Draw a line
    draw.line((30, y_pos, width - 30, y_pos), fill=txt_color, width=2)
    y_pos += 10
    
    # Draw % Daily Value
    draw.text((width - 150, y_pos), "% Daily Value*", fill=txt_color, font=normal_font)
    y_pos += 25
    
    # Draw nutrition facts
    nutrients = [
        ("Total Fat", f"{label_data['nutrition_adjustments']['fat']}g", f"{int(label_data['nutrition_adjustments']['fat'] * 100 / 65)}%"),
        ("Saturated Fat", f"{label_data['nutrition_adjustments']['saturated_fat']}g", f"{int(label_data['nutrition_adjustments']['saturated_fat'] * 100 / 20)}%"),
        ("Trans Fat", f"{label_data['nutrition_adjustments']['trans_fat']}g", ""),
        ("Cholesterol", f"{label_data['nutrition_adjustments']['cholesterol']}mg", f"{int(label_data['nutrition_adjustments']['cholesterol'] * 100 / 300)}%"),
        ("Sodium", f"{label_data['nutrition_adjustments']['sodium']}mg", f"{int(label_data['nutrition_adjustments']['sodium'] * 100 / 2400)}%"),
        ("Total Carbohydrate", f"{label_data['nutrition_adjustments']['carbohydrates']}g", f"{int(label_data['nutrition_adjustments']['carbohydrates'] * 100 / 300)}%"),
        ("Dietary Fiber", f"{label_data['nutrition_adjustments']['dietary_fiber']}g", f"{int(label_data['nutrition_adjustments']['dietary_fiber'] * 100 / 25)}%"),
        ("Total Sugars", f"{label_data['nutrition_adjustments']['sugars']}g", ""),
        ("Protein", f"{label_data['nutrition_adjustments']['protein']}g", "")
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
    templates_dir = Path("C:/Users/LuisRamos/PycharmProjects/CuradoUSDA/templates")
    templates_dir.mkdir(exist_ok=True)
    
    # Check if the template exists, if not create it
    template_path = templates_dir / "label_template.html"
    if not template_path.exists():
        create_html_template(template_path)
    
    # Load the template
    template = template_env.get_template("label_template.html")
    
    # Calculate daily values percentages
    daily_values = {
        "fat": int(label_data['nutrition_adjustments']['fat'] * 100 / 65),
        "saturated_fat": int(label_data['nutrition_adjustments']['saturated_fat'] * 100 / 20),
        "cholesterol": int(label_data['nutrition_adjustments']['cholesterol'] * 100 / 300),
        "sodium": int(label_data['nutrition_adjustments']['sodium'] * 100 / 2400),
        "carbohydrates": int(label_data['nutrition_adjustments']['carbohydrates'] * 100 / 300),
        "dietary_fiber": int(label_data['nutrition_adjustments']['dietary_fiber'] * 100 / 25)
    }
    
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
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: {{ label_data.label_style.background_color|default('#FFFFFF') }};
            color: {{ label_data.label_style.text_color|default('#000000') }};
        }
        .label-container {
            max-width: 600px;
            margin: 20px auto;
            padding: 20px;
            border: 2px solid #000;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        .recipe-title {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
            text-align: center;
        }
        .nutrition-header {
            font-size: 20px;
            font-weight: bold;
            margin: 15px 0;
            border-bottom: 8px solid #000;
            padding-bottom: 5px;
        }
        .serving-info {
            font-size: 16px;
            margin-bottom: 10px;
        }
        .amount-per-serving {
            font-weight: bold;
            font-size: 16px;
            margin: 10px 0;
            border-bottom: 4px solid #000;
            padding-bottom: 5px;
        }
        .calories-row {
            display: flex;
            justify-content: space-between;
            font-size: 16px;
            margin: 5px 0;
            padding: 5px 0;
            border-bottom: 1px solid #000;
        }
        .daily-value-header {
            font-weight: bold;
            font-size: 16px;
            text-align: right;
            margin: 10px 0;
            padding: 5px 0;
            border-bottom: 4px solid #000;
        }
        .nutrient-row {
            display: flex;
            justify-content: space-between;
            font-size: 16px;
            margin: 5px 0;
            padding: 5px 0;
            border-bottom: 1px solid #000;
        }
        .nutrient-name {
            font-weight: bold;
        }
        .sub-nutrient {
            padding-left: 20px;
        }
        .footnote {
            font-size: 12px;
            margin-top: 15px;
        }
        .allergens {
            font-size: 16px;
            margin-top: 15px;
            font-weight: bold;
        }
        .facility-allergens {
            font-size: 14px;
            margin-top: 10px;
        }
        .business-info {
            font-size: 14px;
            margin-top: 20px;
            text-align: center;
        }
        .timestamp {
            font-size: 10px;
            color: #999;
            text-align: right;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="label-container">
        {% if not label_data.label_sections.hide_recipe_title|default(false) %}
        <div class="recipe-title">{{ label_data.recipe_title }}</div>
        {% endif %}
        
        {% if not label_data.label_sections.hide_nutrition_facts|default(false) %}
        <div class="nutrition-header">Nutrition Facts</div>
        
        {% if label_data.label_style.serving_size_en|default('') %}
        <div class="serving-info">
            <div>Serving Size: {{ label_data.label_style.serving_size_en }}</div>
            {% if label_data.label_style.servings_per_package|default('') %}
            <div>Servings Per Container: {{ label_data.label_style.servings_per_package }}</div>
            {% endif %}
        </div>
        {% endif %}
        
        <div class="amount-per-serving">Amount Per Serving</div>
        
        <div class="calories-row">
            <div class="nutrient-name">Calories</div>
            <div>{{ label_data.nutrition_adjustments.calories }}</div>
        </div>
        
        <div class="daily-value-header">% Daily Value*</div>
        
        <div class="nutrient-row">
            <div class="nutrient-name">Total Fat</div>
            <div>{{ label_data.nutrition_adjustments.fat }}g</div>
            <div>{{ daily_values.fat }}%</div>
        </div>
        
        <div class="nutrient-row">
            <div class="nutrient-name sub-nutrient">Saturated Fat</div>
            <div>{{ label_data.nutrition_adjustments.saturated_fat }}g</div>
            <div>{{ daily_values.saturated_fat }}%</div>
        </div>
        
        <div class="nutrient-row">
            <div class="nutrient-name sub-nutrient">Trans Fat</div>
            <div>{{ label_data.nutrition_adjustments.trans_fat }}g</div>
            <div></div>
        </div>
        
        <div class="nutrient-row">
            <div class="nutrient-name">Cholesterol</div>
            <div>{{ label_data.nutrition_adjustments.cholesterol }}mg</div>
            <div>{{ daily_values.cholesterol }}%</div>
        </div>
        
        <div class="nutrient-row">
            <div class="nutrient-name">Sodium</div>
            <div>{{ label_data.nutrition_adjustments.sodium }}mg</div>
            <div>{{ daily_values.sodium }}%</div>
        </div>
        
        <div class="nutrient-row">
            <div class="nutrient-name">Total Carbohydrate</div>
            <div>{{ label_data.nutrition_adjustments.carbohydrates }}g</div>
            <div>{{ daily_values.carbohydrates }}%</div>
        </div>
        
        <div class="nutrient-row">
            <div class="nutrient-name sub-nutrient">Dietary Fiber</div>
            <div>{{ label_data.nutrition_adjustments.dietary_fiber }}g</div>
            <div>{{ daily_values.dietary_fiber }}%</div>
        </div>
        
        <div class="nutrient-row">
            <div class="nutrient-name sub-nutrient">Total Sugars</div>
            <div>{{ label_data.nutrition_adjustments.sugars }}g</div>
            <div></div>
        </div>
        
        <div class="nutrient-row">
            <div class="nutrient-name">Protein</div>
            <div>{{ label_data.nutrition_adjustments.protein }}g</div>
            <div></div>
        </div>
        
        <div class="footnote">
            * The % Daily Value tells you how much a nutrient in a serving of food contributes to a daily diet. 2,000 calories a day is used for general nutrition advice.
        </div>
        {% endif %}
        
        {% if not label_data.label_sections.hide_allergens|default(false) and label_data.allergens %}
        <div class="allergens">
            Contains: {{ label_data.allergens|join(', ') }}
        </div>
        {% endif %}
        
        {% if not label_data.label_sections.hide_facility_allergens|default(false) and label_data.facility_allergens %}
        <div class="facility-allergens">
            Manufactured in a facility that also processes: {{ label_data.facility_allergens|join(', ') }}
        </div>
        {% endif %}
        
        {% if not label_data.label_sections.hide_business_info|default(false) and label_data.business_info %}
        <div class="business-info">
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