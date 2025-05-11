"""
Test script to generate a sample nutrition label using the updated template.
"""

from services.label_generator import generate_html, generate_pdf, generate_png
import webbrowser
import os

def main():
    # Sample test data that matches the example in deleteme.txt
    test_data = {
        'id': 'test123',
        'recipe_title': 'Banana Oatmeal Cookies',
        'nutrition_adjustments': {
            'calories': 110,
            'fat': 4.5,
            'saturated_fat': 2.5,
            'trans_fat': 0,
            'cholesterol': 20,
            'sodium': 80,
            'carbohydrates': 17,
            'dietary_fiber': 1,
            'sugars': 9,
            'added_sugars': 9,
            'protein': 2,
            'vitamin_d': 0,
            'calcium': 10,
            'iron': 0.4,
            'potassium': 40
        },
        'label_style': {
            'serving_size_en': '1 cookie',
            'serving_size_weight': '25g',
            'servings_per_package': '48',
            'background_color': '#FFFFFF',
            'text_color': '#000000'
        },
        'allergens': ['Milk', 'Egg', 'Wheat'],
        'facility_allergens': ['Milk', 'Egg', 'Pecan', 'Wheat', 'Peanuts', 'Soy'],
        'ingredients': 'Wheat flour*, Oat, Butter* (Cream, Natural Flavoring), Brown Sugar, Sugar, Banana*, Eggs, Salts, Baking Soda, Natural Flavor, Spice. * = Organic',
        'business_info': {
            'business_name': 'Manufactured by: Recipal LLC',
            'address': 'New York, NY 10028'
        },
        'label_sections': {
            'hide_recipe_title': False,
            'hide_nutrition_facts': False,
            'hide_allergens': False,
            'hide_facility_allergens': False,
            'hide_business_info': False
        }
    }
    
    # Generate the HTML label
    html_path = generate_html(test_data, 'test_label')
    print(f'HTML label generated at: {html_path}')
    
    # Generate the PDF label
    pdf_path = generate_pdf(test_data, 'test_label')
    print(f'PDF label generated at: {pdf_path}')
    
    # Generate the PNG label
    png_path = generate_png(test_data, 'test_label')
    print(f'PNG label generated at: {png_path}')
    
    # Open the HTML file in the default browser
    webbrowser.open('file://' + os.path.abspath(html_path))

if __name__ == "__main__":
    main()