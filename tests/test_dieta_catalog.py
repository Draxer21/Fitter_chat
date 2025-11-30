import pytest
from backend.food.catalog import FoodCatalog, get_catalog
import os


def test_load_sample_catalog():
    # Ensure the sample catalog loads and has expected items
    c = FoodCatalog(path=os.path.join(os.path.dirname(__file__), "..", "backend", "data", "food_catalog_sample.json"))
    items = c.all()
    assert isinstance(items, list)
    assert len(items) >= 4


def test_filter_allergens():
    c = get_catalog(path=os.path.join(os.path.dirname(__file__), "..", "backend", "data", "food_catalog_sample.json"))
    # filter out nuts
    filtered = c.filter_allergens(["nuts"]) 
    ids = [it['id'] for it in filtered]
    assert "0004" not in ids


def test_find_by_kcal_approx():
    c = get_catalog(path=os.path.join(os.path.dirname(__file__), "..", "backend", "data", "food_catalog_sample.json"))
    # look for a ~130 kcal item per 100g -> should find arroz (130)
    results = c.find_by_kcal_approx(130, tolerance_pct=10, per_serving=False)
    assert any(r['id'] == '0002' for r in results)
