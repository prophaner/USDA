import pytest

from models import Suggestion, Portion, Nutrient, Ingredient, IngredientInput, RecipeOutput
from helpers import convert_units


def test_suggestion_fields():
    s = Suggestion(fdc_id=123, description='Apple', category='Fruits', data_type='Survey')
    assert s.fdc_id == 123
    assert s.description == 'Apple'
    assert s.category == 'Fruits'
    assert s.data_type == 'Survey'


def test_portion_unit_lowercase():
    p = Portion(unit='CUP', amount=2.0, grams=480.0, description='2 cups')
    assert p.unit == 'cup'
    assert p.amount == 2.0
    assert p.grams == 480.0


def test_nutrient_convert():
    # nutrient value 100 g -> oz
    nut = Nutrient(key='fat', name='Total lipid', value=100.0, unit='g', min=None, max=None)
    oz = nut.convert('oz')
    expected = convert_units(100.0, 'g', 'oz')
    assert pytest.approx(oz, rel=1e-4) == expected


def test_ingredient_scale():
    # Create dummy ingredient with 1 portion: 100g
    portion = Portion(unit='g', amount=100.0, grams=100.0)
    nut1 = Nutrient(key='protein', name='Protein', value=10.0, unit='g', min=None, max=None)
    ing = Ingredient(
        fdc_id=1,
        description='TestFood',
        category=None,
        data_type=None,
        serving=portion,
        portions=[portion],
        nutrients=[nut1]
    )
    # Scale to 200g
    ing.scale(200.0, 'g')
    assert ing.serving.amount == 200.0
    assert ing.serving.unit == 'g'
    # Nutrient should double
    assert ing.nutrients[0].value == pytest.approx(20.0)


def test_ingredient_input_unit_normalization():
    inp = IngredientInput(unit='TbSp')
    assert inp.unit == 'tbsp'


def test_recipe_output_sum():
    # Dummy recipe output structure
    items = []
    total = {'fat': 5.0, 'protein': 2.0}
    ro = RecipeOutput(total=total, items=items)
    assert ro.total['fat'] == 5.0
    assert ro.total['protein'] == 2.0
    assert ro.items == []
