"""Heuristic diet composer.

Provides a simple greedy composer that, given a target kcal and a food catalog,
creates a diet split into meals approximating the energy target. This is
intended as a pragmatic, explainable fallback before training a ML model.

API:
  compose_diet(target_kcal, n_meals=3, catalog_path=None, exclude_allergens=None)

Returns a dict with keys: diet_id, header, summary, meals (list of meals with items).
"""
from typing import List, Dict, Any, Optional
import uuid
from math import floor

from .catalog import get_catalog


def _choose_candidate(items: List[Dict[str, Any]], used_ids: set) -> Optional[Dict[str, Any]]:
    """Pick a candidate item from items preferring high kcal density but not already heavily used."""
    # Respect the current ordering of 'items' (caller may pre-sort by objective)
    for c in items:
        if not c.get('energy_kcal_100g'):
            continue
        cid = c.get('id')
        if list(used_ids).count(cid) >= 3:
            continue
        return c
    return None


def compose_diet(target_kcal: int, n_meals: int = 3, catalog_path: Optional[str] = None, exclude_allergens: Optional[List[str]] = None, objetivo: Optional[str] = None, weight_kg: Optional[float] = None) -> Dict[str, Any]:
    """Compose a simple diet close to target_kcal split in n_meals.

    Strategy (greedy): for each meal, target meal_kcal = target_kcal / n_meals.
    Repeatedly select high-kcal-density items and compute a grams portion so the
    item contributes a significant share toward remaining meal kcal.
    """
    cat = get_catalog(path=catalog_path)
    items = cat.all()
    # apply allergen filter
    if exclude_allergens:
        items = cat.filter_allergens(exclude_allergens)

    # Remove items without kcal info
    items = [it for it in items if it.get('energy_kcal_100g')]
    if not items:
        return {
            'diet_id': str(uuid.uuid4()),
            'header': 'Dieta generada',
            'summary': {'target_kcal': target_kcal},
            'meals': []
        }

    meals: List[Dict[str, Any]] = []
    used_ids = []

    meal_target = float(target_kcal) / max(1, n_meals)

    # normalize objective
    objetivo_norm = (objetivo or '').strip().lower()

    # scoring: build a simple score per item depending on objective
    def score_item(it: Dict[str, Any]) -> float:
        ek = it.get('energy_kcal_100g') or 0.0
        prot = it.get('proteins_g_100g') or 0.0
        # base score favors energy density
        if objetivo_norm in {'hipertrofia', 'ganar masa', 'ganar_masa'}:
            # favor high energy and decent protein
            return ek * 0.7 + prot * 10.0
        elif objetivo_norm in {'bajar_grasa', 'perder_peso', 'perder_grasa'}:
            # favor high protein and lower energy
            return prot * 15.0 - ek * 0.3
        else:
            # balanced
            return ek * 0.5 + prot * 8.0

    # compute median energy to help objective-specific filtering
    energies = sorted([it.get('energy_kcal_100g') or 0.0 for it in items])
    median_ek = energies[len(energies) // 2] if energies else 0.0

    # pre-sort items according to objective to bias selection
    if objetivo_norm in {'hipertrofia', 'ganar masa', 'ganar_masa'}:
        # prefer high energy density and reasonable protein
        items.sort(key=lambda it: ((it.get('energy_kcal_100g') or 0.0) * 0.7 + (it.get('proteins_g_100g') or 0.0) * 8.0), reverse=True)
    elif objetivo_norm in {'bajar_grasa', 'perder_peso', 'perder_grasa'}:
        # prefer higher protein and lower energy density
        items.sort(key=lambda it: ((it.get('proteins_g_100g') or 0.0) * 12.0 - (it.get('energy_kcal_100g') or 0.0) * 0.5), reverse=True)
    else:
        items.sort(key=score_item, reverse=True)

    for m in range(n_meals):
        remaining = meal_target
        meal_items: List[Dict[str, Any]] = []
        attempts = 0
        # limit items per meal
        while remaining > 40 and attempts < 10 and len(meal_items) < 5:
            attempts += 1
            # choose a candidate
            candidate = _choose_candidate(items, set(used_ids))
            if not candidate:
                break

            ek = candidate.get('energy_kcal_100g') or 0.0
            if ek <= 0:
                # skip invalid
                items.remove(candidate)
                continue
            # decide fraction/qty based on objective
            if objetivo_norm in {'hipertrofia', 'ganar masa', 'ganar_masa'}:
                frac = 0.55
            elif objetivo_norm in {'bajar_grasa', 'perder_peso', 'perder_grasa'}:
                frac = 0.3
            else:
                frac = 0.4

            qty = floor((remaining * frac) / ek * 100)
            # enforce reasonable qty bounds
            if qty < 30:
                qty = 30
            if qty > 500:
                qty = 500

            kcal_added = ek * qty / 100.0
            meal_items.append({
                'id': candidate.get('id'),
                'name': candidate.get('name'),
                'qty_g': int(qty),
                'kcal': round(kcal_added, 1),
                'energy_kcal_100g': ek,
            })
            used_ids.append(candidate.get('id'))
            remaining -= kcal_added

            # small optimization: remove candidate if we've used it many times
            if used_ids.count(candidate.get('id')) >= 3:
                try:
                    items.remove(candidate)
                except ValueError:
                    pass

        meals.append({'name': f'Comida {m+1}', 'items': meal_items, 'kcal': round(meal_target - max(0, remaining), 1)})

    total_kcal = sum(m['kcal'] for m in meals)

    return {
        'diet_id': str(uuid.uuid4()),
        'header': 'Dieta generada heurísticamente',
        'summary': {'target_kcal': target_kcal, 'approx_kcal': round(total_kcal, 1)},
        'meals': meals,
    }


if __name__ == '__main__':
    # quick manual demo
    d = compose_diet(2000, n_meals=3)
    import json
    print(json.dumps(d, ensure_ascii=False, indent=2))
