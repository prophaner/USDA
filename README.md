# curado\_usda

USDA Nutrition Proxy API

Wraps the USDA FoodData Central API to provide:

* **Ingredient search** (`GET /search?q=`)
* **Ingredient details** (`GET /ingredient?q=` or `fdc_id=` with optional scaling)
* **Recipe aggregation** (`POST /recipe`)
* **Unit conversions** (weight & volume)
* **USDA Approved Label generation** (`POST /label/`)

---

## Features

* **Type-ahead** ingredient lookup
* **Normalized portions** with gram equivalents
* **Scaled nutrients** per custom serving
* **Aggregated recipe** nutritional totals
* **USDA Approved Label generation** in multiple formats (PDF, PNG, HTML)
* **Pydantic** models and **FastAPI** endpoints
* **Comprehensive tests** with pytest & httpx

---

## Getting Started

1. **Clone the repo**

   ```bash
   git clone https://github.com/yourorg/curado_usda.git
   cd curado_usda
   ```

2. **Create a virtual environment** and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment**

   * Copy `.env.example` to `.env`
   * Fill in your `USDA_API_KEY`

4. **Run the server**

   ```bash
   uvicorn curado_usda.server:app --reload --port 8000
   ```

5. **Interact via web**

   * Health check: `http://127.0.0.1:8000/`
   * Swagger UI: `http://127.0.0.1:8000/docs`

---

## Project Structure

```
curado_usda/
├── __init__.py        # Package entry
├── config.py          # Env-based settings
├── helpers.py         # USDA API & conversions
├── models.py          # Pydantic schemas
├── server.py          # Main FastAPI app
├── routes/            # Endpoint routers
│   ├── __init__.py
│   ├── search.py
│   ├── ingredient.py
│   ├── recipe.py
│   ├── label.py       # Label generation routes
│   └── label_async.py # Async label generation routes
├── services/          # Business logic
│   ├── label_service.py       # Label generation service
│   ├── label_service_async.py # Async label service
│   └── label_generator.py     # PDF/PNG/HTML generator
├── templates/         # HTML templates
│   └── label_template.html    # Label HTML template
├── temp/              # Temporary files (not in git)
│   └── .gitignore     # Ignore all files except this one
├── tests/             # pytest suite
│   ├── test_helpers.py
│   ├── test_models.py
│   ├── test_server.py
│   └── test_label_route.py    # Label API tests
├── requirements.txt   # Dependencies
├── .env.example       # Sample environment
├── .gitignore         # Exclusions
└── README.md          # Project overview
```

---

## Usage Examples

**Search**

```bash
curl -G http://127.0.0.1:8000/search --data-urlencode "q=tomatillo" --data-urlencode "limit=5"
```

**Ingredient**

```bash
curl -G http://127.0.0.1:8000/ingredient --data-urlencode "q=Tomatillos, raw" --data-urlencode "amount=0.5" --data-urlencode "unit=cup"
```

**Recipe**

```bash
curl -X POST http://127.0.0.1:8000/recipe \
  -H "Content-Type: application/json" \
  -d '[{ "q": "Chicken, raw", "amount": 8, "unit": "oz" }, { "q": "Butter", "amount": 2, "unit": "tbsp" }]'
```

**Label Generation**

```bash
curl -X POST http://127.0.0.1:8000/label/ \
  -H "Content-Type: application/json" \
  -d '{
    "recipe_title": "Chicken Salad",
    "recipe_data": {
      "items": [
        {
          "fdc_id": 171115,
          "description": "Chicken Breast",
          "nutrients": [
            {"key": "energy", "name": "Energy", "value": 165.0, "unit": "kcal"},
            {"key": "fat", "name": "Total lipid (fat)", "value": 3.6, "unit": "g"}
          ]
        }
      ],
      "total": {
        "Energy": 165.0,
        "Total lipid (fat)": 3.6
      }
    },
    "business_info": {
      "business_name": "Healthy Meals Inc.",
      "address": "123 Main St, Anytown, USA"
    },
    "label_type": "USDA (Old FDA) Vertical",
    "nutrition_adjustments": {
      "calories": 165.0,
      "fat": 3.6,
      "saturated_fat": 1.0,
      "trans_fat": 0.0,
      "cholesterol": 85.0,
      "sodium": 74.0,
      "carbohydrates": 0.0,
      "dietary_fiber": 0.0,
      "sugars": 0.0,
      "protein": 31.0
    }
  }'
```

**Download Label as PDF**

```bash
curl -o label.pdf http://127.0.0.1:8000/label/{label_id}/download/pdf
```

**Download Label as PNG**

```bash
curl -o label.png http://127.0.0.1:8000/label/{label_id}/download/png
```

**Get Embeddable HTML**

```bash
curl http://127.0.0.1:8000/label/{label_id}/embed
```

---

## Label Maker API

The Label Maker API allows you to generate USDA Approved Nutrition Labels in multiple formats based on recipe data.

### Endpoints

#### Generate Label

```
POST /label/
```

Generates a USDA Approved Label based on the provided recipe data and formatting options.

**Request Body:**

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| recipe_title | string | Title of the recipe | Yes |
| recipe_data | object | Recipe nutritional data | Yes |
| business_info | object | Business information | Conditional* |
| label_sections | object | Label section visibility options | No |
| label_style | object | Label style options | No |
| optional_nutrients | object | Optional nutrients to display | No |
| optional_vitamins | object | Optional vitamins to display | No |
| nutrition_adjustments | object | Nutrition value adjustments | Yes |
| label_type | string | Type of label to generate | Yes |
| allergens | array | List of allergens | No |
| facility_allergens | array | List of facility allergens | No |

\* Required unless `label_sections.hide_business_info` is `true`

**Response:**

```json
{
  "label_url": "/api/labels/{label_id}",
  "pdf_download_url": "/api/labels/{label_id}/download/pdf",
  "png_download_url": "/api/labels/{label_id}/download/png",
  "embedded_html": "<iframe src=\"/api/labels/{label_id}/embed\" width=\"100%\" height=\"600\" frameborder=\"0\" scrolling=\"no\" allowfullscreen></iframe>"
}
```

#### Download Label as PDF

```
GET /label/{label_id}/download/pdf
```

Downloads the generated label as a PDF file.

**Response:**
- Content-Type: application/pdf
- File download

#### Download Label as PNG

```
GET /label/{label_id}/download/png
```

Downloads the generated label as a PNG image.

**Response:**
- Content-Type: image/png
- File download

#### Embed Label as HTML

```
GET /label/{label_id}/embed
```

Returns the HTML version of the label for embedding in a UI.

**Response:**
- Content-Type: text/html
- HTML content

### Label Input Schema

#### Recipe Data

```json
{
  "items": [
    {
      "fdc_id": 171115,
      "description": "Chicken Breast",
      "category": "Poultry",
      "data_type": "SR Legacy",
      "nutrients": [
        {
          "key": "energy",
          "name": "Energy",
          "value": 165.0,
          "unit": "kcal"
        },
        {
          "key": "fat",
          "name": "Total lipid (fat)",
          "value": 3.6,
          "unit": "g"
        }
      ]
    }
  ],
  "total": {
    "Energy": 165.0,
    "Total lipid (fat)": 3.6
  }
}
```

#### Business Info

```json
{
  "business_name": "Healthy Meals Inc.",
  "address": "123 Main St, Anytown, USA"
}
```

#### Label Sections

```json
{
  "hide_recipe_title": false,
  "hide_nutrition_facts": false,
  "hide_ingredient_list": false,
  "hide_allergens": false,
  "hide_facility_allergens": false,
  "hide_business_info": false
}
```

#### Label Style

```json
{
  "language": "english",
  "serving_size_en": "1 cup (240g)",
  "servings_per_package": 4,
  "alignment": "left",
  "text_case": "default",
  "width": 300,
  "text_color": "#000000",
  "background_color": "#FFFFFF"
}
```

#### Nutrition Adjustments

```json
{
  "calories": 165.0,
  "fat": 3.6,
  "saturated_fat": 1.0,
  "trans_fat": 0.0,
  "cholesterol": 85.0,
  "sodium": 74.0,
  "carbohydrates": 0.0,
  "dietary_fiber": 0.0,
  "sugars": 0.0,
  "protein": 31.0
}
```

### Integration Example

Here's how to integrate the Label Maker API in a web application:

```javascript
// Generate a label
fetch('/label/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    recipe_title: "Chicken Salad",
    recipe_data: { /* Recipe data */ },
    business_info: { /* Business info */ },
    label_type: "USDA (Old FDA) Vertical",
    nutrition_adjustments: { /* Nutrition values */ }
  })
})
.then(response => response.json())
.then(data => {
  // Add download buttons
  document.getElementById('pdf-download').href = data.pdf_download_url;
  document.getElementById('png-download').href = data.png_download_url;
  
  // Add the embed code to the page
  document.getElementById('label-container').innerHTML = data.embedded_html;
})
.catch(error => console.error('Error:', error));
```

## Testing

Execute the test suite with:

```bash
pytest
```

To run specific tests for the Label Maker API:

```bash
pytest tests/test_label_route.py -v
```

---

## License

MIT © Your Name or Organization
