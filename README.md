# curado\_usda

USDA Nutrition Proxy API

Wraps the USDA FoodData Central API to provide:

* **Ingredient search** (`GET /search?q=`)
* **Ingredient details** (`GET /ingredient?q=` or `fdc_id=` with optional scaling)
* **Recipe aggregation** (`POST /recipe`)
* **Unit conversions** (weight & volume)

---

## Features

* **Type-ahead** ingredient lookup
* **Normalized portions** with gram equivalents
* **Scaled nutrients** per custom serving
* **Aggregated recipe** nutritional totals
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
│   └── recipe.py
├── tests/             # pytest suite
│   ├── test_helpers.py
│   ├── test_models.py
│   └── test_server.py
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

---

## Testing

Execute the test suite with:

```bash
pytest
```

---

## License

MIT © Your Name or Organization
