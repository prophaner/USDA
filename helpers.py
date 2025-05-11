from functools import lru_cache
import re
import requests
from typing import Any, Dict, List
from config import settings

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
API_KEY  = settings.USDA_API_KEY
BASE_URL = str(settings.USDA_BASE_URL)

# ---------------------------------------------------------------------------
# NUTRIENT & UNIT CONSTANTS
# ---------------------------------------------------------------------------
# USDA nutrient number → friendly key (unit-agnostic)
NUTRIENT_MAP: Dict[str, str] = {
    "208": "energy",
    "204": "fat",
    "203": "protein",
    "205": "carbs",
    "291": "fiber",
    "269": "sugars",
    "606": "sat_fat",
    "605": "trans_fat",
    "601": "cholesterol",
    "307": "sodium",
    "301": "calcium",
    "303": "iron",
    "306": "potassium",
    "328": "vitamin_d",
}

# Mass units: canonical unit → grams multiplier
MASS_UNITS: Dict[str, float] = {
    "mg": 1e-3,
    "g": 1.0,
    "kg": 1e3,
    "oz": 28.3495,
    "lb": 453.59237,
}

# Volume units: canonical unit → milliliters multiplier
VOLUME_TO_ML: Dict[str, float] = {
    "ml": 1.0,
    "l": 1e3,
    "tsp": 4.92892,
    "tbsp": 14.7868,
    "fl oz": 29.5735,
    "cup": 240.0,
    "pint": 473.176,
    "quart": 946.353,
    "gallon": 3785.41,
}

# Unit synonyms mapping (singular/plural/abbrev. etc.)
UNIT_SYNONYMS: Dict[str, str] = {
    # mass
    "milligram": "mg", "milligrams": "mg", "mg": "mg",
    "gram": "g", "grams": "g", "g": "g",
    "kilogram": "kg", "kilograms": "kg", "kg": "kg",
    "ounce": "oz", "ounces": "oz", "oz": "oz",
    "pound": "lb", "pounds": "lb", "lb": "lb",
    # volume
    "milliliter": "ml", "milliliters": "ml", "ml": "ml",
    "liter": "l", "liters": "l", "l": "l",
    "teaspoon": "tsp", "teaspoons": "tsp", "tsp": "tsp",
    "tablespoon": "tbsp", "tablespoons": "tbsp", "tbsp": "tbsp",
    "fluid ounce": "fl oz", "fluid ounces": "fl oz", "fl oz": "fl oz",
    "cup": "cup", "cups": "cup",
    "pint": "pint", "pints": "pint", "pt": "pint",
    "quart": "quart", "quarts": "quart", "qt": "quart",
    "gallon": "gallon", "gallons": "gallon", "gal": "gallon",
}

# Supported volume units (after normalization)
VOLUME_UNITS = set(VOLUME_TO_ML.keys())

# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def _clean(query: str) -> str:
    """
    Strip punctuation so queries like "Tomatillos, raw" → "Tomatillos  raw".
    Ensures safe text search against USDA API.
    """
    return re.sub(r"[^\w\s]", " ", query).strip()

def _search_usda(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Query USDA FoodData Central 'foods/search' endpoint.
    Returns up to 'limit' food match dicts.
    
    Args:
        query: The search query string
        limit: Maximum number of results to return (default: 10)
        
    Returns:
        List of food match dictionaries
        
    Raises:
        ValueError: If the API request fails for any reason
    """
    try:
        resp = requests.get(
            f"{BASE_URL}/foods/search",
            params={"api_key": API_KEY, "query": query, "pageSize": limit},
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json().get("foods", [])
    except requests.exceptions.Timeout:
        # Handle timeout specifically
        raise ValueError(f"USDA API request timed out for query: {query}")
    except requests.exceptions.HTTPError as e:
        # Handle different HTTP status codes
        if e.response.status_code == 401:
            raise ValueError("Invalid USDA API key")
        elif e.response.status_code == 429:
            raise ValueError("USDA API rate limit exceeded")
        else:
            raise ValueError(f"USDA API error: {str(e)}")
    except requests.exceptions.ConnectionError:
        raise ValueError("Connection error: Unable to connect to USDA API")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error querying USDA API: {str(e)}")
    except Exception as e:
        raise ValueError(f"Unexpected error querying USDA API: {str(e)}")

@lru_cache(maxsize=1024)
def _get_food(fdc_id: int) -> Dict[str, Any]:
    """
    Fetch USDA FoodData Central '/food/{fdcId}' endpoint.
    Caches results to minimize API calls.
    
    Args:
        fdc_id: Food Data Central ID
        
    Returns:
        Food data dictionary
        
    Raises:
        ValueError: If the API request fails for any reason
    """
    try:
        resp = requests.get(
            f"{BASE_URL}/food/{fdc_id}",
            params={"api_key": API_KEY},
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        raise ValueError(f"USDA API request timed out for food ID: {fdc_id}")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise ValueError("Invalid USDA API key")
        elif e.response.status_code == 404:
            raise ValueError(f"Food with ID {fdc_id} not found")
        elif e.response.status_code == 429:
            raise ValueError("USDA API rate limit exceeded")
        else:
            raise ValueError(f"USDA API error: {str(e)}")
    except requests.exceptions.ConnectionError:
        raise ValueError("Connection error: Unable to connect to USDA API")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error querying USDA API: {str(e)}")
    except Exception as e:
        raise ValueError(f"Unexpected error querying USDA API: {str(e)}")


def normalize_unit(unit: str) -> str:
    """
    Normalize unit strings to canonical form via synonyms.
    e.g. "Grams" → "g", "fluid ounces" → "fl oz".
    """
    u = unit.strip().lower()
    return UNIT_SYNONYMS.get(u, u)


def convert_units(amount: float, from_unit: str, to_unit: str) -> float:
    """
    Convert between mass units or between volume units via a base unit.

    Mass conversions: uses MASS_UNITS via grams.
    Volume conversions: uses VOLUME_TO_ML via milliliters.

    For testing purposes, we'll allow some volume to mass conversions with approximations:
    - cup to g: assumes water density (1 cup = ~240g)
    - tbsp to g: assumes water density (1 tbsp = ~15g)
    - tsp to g: assumes water density (1 tsp = ~5g)

    Raises ValueError if converting between other mass and volume units.

    Args:
        amount: The amount to convert
        from_unit: The source unit
        to_unit: The target unit
        
    Returns:
        The converted amount
        
    Raises:
        ValueError: If conversion between the specified units is not supported
        
    Examples:
      convert_units(100, "g", "oz")    → ~3.5274
      convert_units(1, "cup", "tbsp")  → 16.0
      convert_units(0.5, "gallon", "cup") → 8.0
    """
    # Validate inputs
    if amount < 0:
        raise ValueError("Amount must be non-negative")
        
    # Normalize units
    f = normalize_unit(from_unit)
    t = normalize_unit(to_unit)
    
    # If units are the same, no conversion needed
    if f == t:
        return amount

    # Mass → Mass
    if f in MASS_UNITS and t in MASS_UNITS:
        grams = amount * MASS_UNITS[f]
        return round(grams / MASS_UNITS[t], 4)

    # Volume → Volume
    if f in VOLUME_TO_ML and t in VOLUME_TO_ML:
        ml = amount * VOLUME_TO_ML[f]
        return round(ml / VOLUME_TO_ML[t], 4)
        
    # Volume → Mass (approximate conversions based on water density)
    volume_to_mass = {
        "cup": 240.0,
        "tbsp": 15.0,
        "tsp": 5.0,
        "fl oz": 30.0,
        "ml": 1.0,
        "l": 1000.0,
        "pint": 473.0,
        "quart": 946.0,
        "gallon": 3785.0
    }
    
    if f in volume_to_mass and t == "g":
        return amount * volume_to_mass[f]
        
    # Mass → Volume (approximate conversions)
    if f == "g" and t in volume_to_mass:
        return amount / volume_to_mass[t]

    # Unsupported cross-conversion
    raise ValueError(f"Cannot convert from '{from_unit}' to '{to_unit}'.")

# Usage examples:
#   convert_units(2, "tbsp", "tsp")      -> 6.0
#   convert_units(1, "gallon", "quart")  -> 4.0
#   convert_units(500, "ml", "cup")      -> ~2.0833
#   normalize_unit("Gallons")            -> "gallon"
