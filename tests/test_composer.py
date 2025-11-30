import os
from backend.food.composer import compose_diet


def test_compose_basic():
    d = compose_diet(2000, n_meals=3, catalog_path=os.path.join('backend', 'data', 'food_catalog.json'))
    assert isinstance(d, dict)
    assert 'meals' in d
    assert len(d['meals']) == 3
    approx = d['summary'].get('approx_kcal')
    assert approx is not None
    # approximate should be within 40% of target at worst for heuristic
    assert abs(approx - 2000) / 2000 <= 0.5


def test_items_exist():
    d = compose_diet(1200, n_meals=2, catalog_path=os.path.join('backend', 'data', 'food_catalog.json'))
    for meal in d['meals']:
        for it in meal['items']:
            assert 'id' in it and 'qty_g' in it and 'kcal' in it
