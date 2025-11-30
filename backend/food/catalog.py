"""Loader y utilidades para el catálogo de alimentos.
Este módulo carga `backend/data/food_catalog.json` (o el path configurado) y ofrece funciones
simples de búsqueda y filtrado para `ActionGenerarDieta`.
"""
from typing import List, Dict, Any, Optional
import json
import os

DEFAULT_CATALOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "food_catalog_sample.json")


class FoodCatalog:
    def __init__(self, path: Optional[str] = None):
        self.path = path or DEFAULT_CATALOG_PATH
        self._items: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self._items = json.load(f)
        except FileNotFoundError:
            self._items = []

    def all(self) -> List[Dict[str, Any]]:
        return self._items

    def filter_allergens(self, allergens: List[str]) -> List[Dict[str, Any]]:
        if not allergens:
            return self._items
        normalized = [a.lower() for a in allergens]
        out = []
        for it in self._items:
            item_all = [a.lower() for a in it.get("allergens", [])]
            if any(a in item_all for a in normalized):
                continue
            out.append(it)
        return out

    def by_category(self, category_tag: str) -> List[Dict[str, Any]]:
        out = []
        for it in self._items:
            cats = it.get("categories", []) or []
            if any(category_tag.lower() in c.lower() for c in cats):
                out.append(it)
        return out

    def find_by_kcal_approx(self, target_kcal: float, tolerance_pct: float = 30.0, per_serving: bool = False) -> List[Dict[str, Any]]:
        """Return items whose energy_kcal_100g is within tolerance of target_kcal (interpreting per 100g).
        If per_serving is True and serving_size_g exists, compare portion kcal.
        """
        if not self._items:
            return []
        tol = tolerance_pct / 100.0
        out = []
        for it in self._items:
            ek = it.get("energy_kcal_100g")
            if ek is None:
                continue
            # compute kcal per serving if required
            kcal_value = ek
            if per_serving:
                serving = it.get("serving_size_g")
                if serving:
                    kcal_value = ek * (serving / 100.0)
                else:
                    # can't compute serving, skip
                    continue
            low = target_kcal * (1 - tol)
            high = target_kcal * (1 + tol)
            if low <= kcal_value <= high:
                out.append(it)
        return out


# convenience: module-level catalog instance
_catalog_instance: Optional[FoodCatalog] = None


def get_catalog(path: Optional[str] = None) -> FoodCatalog:
    global _catalog_instance
    if _catalog_instance is None or (path and _catalog_instance.path != path):
        _catalog_instance = FoodCatalog(path)
    return _catalog_instance
