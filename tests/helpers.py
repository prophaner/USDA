import pytest

from helpers import _clean, normalize_unit, convert_units


def test_clean_removes_punctuation():
    assert _clean("Tomatillos, raw!") == "Tomatillos  raw"
    assert _clean("Bread (white)") == "Bread  white"


@pytest.mark.parametrize("input_unit,expected", [
    ("Grams", "g"),
    ("milliliters", "ml"),
    ("TBSP", "tbsp"),
    ("fluid ounces", "fl oz"),
    ("Quarts", "quart"),
    ("gal", "gallon"),
])
def test_normalize_unit_synonyms(input_unit, expected):
    assert normalize_unit(input_unit) == expected


@pytest.mark.parametrize("amount,from_u,to_u,expected", [
    (1000, "mg", "g", 1.0),
    (1, "kg", "g", 1000.0),
    (28.3495, "g", "oz", pytest.approx(1.0, rel=1e-4)),
    (2, "cup", "tbsp", pytest.approx(32.0)),
    (1, "gallon", "quart", pytest.approx(4.0)),
    (2, "pint", "cup", pytest.approx(4.0)),
])
def test_convert_units_valid(amount, from_u, to_u, expected):
    result = convert_units(amount, from_u, to_u)
    if isinstance(expected, float):
        assert result == pytest.approx(expected, rel=1e-3)
    else:
        assert result == expected


def test_convert_units_invalid():
    with pytest.raises(ValueError):
        convert_units(1, "g", "cup")

# Note: API-based helpers (_search_usda, _get_food) would require mocking requests.
