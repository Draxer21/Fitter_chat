"""Heuristic diet composer.

Provides a simple greedy composer that, given a target kcal and a food catalog,
creates a diet split into meals approximating the energy target. This is
intended as a pragmatic, explainable fallback before training a ML model.

API:
  compose_diet(target_kcal, n_meals=3, catalog_path=None, exclude_allergens=None)

Returns a dict with keys: diet_id, header, summary, meals (list of meals with items).
"""
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict
import uuid
from math import floor
import os

TAG_KEYWORDS: Dict[str, List[str]] = {
    "fruit": [
        "fruit",
        "fruta",
        "frutos",
        "berries",
        "berry",
        "banana",
        "manzana",
        "apple",
        "naranja",
        "orange",
    ],
    "vegetable": [
        "vegetable",
        "verdura",
        "ensalada",
        "salad",
        "brocoli",
        "brócoli",
        "broccoli",
        "espinaca",
        "spinach",
        "zanahoria",
        "carrot",
        "lechuga",
        "greens",
        "wok",
    ],
    "nut_or_seed": [
        "almendra",
        "almendras",
        "almond",
        "almonds",
        "nuez",
        "nueces",
        "walnut",
        "walnuts",
        "nut",
        "nuts",
        "pistacho",
        "pistachio",
        "semilla",
        "semillas",
        "seed",
        "seeds",
        "chia",
        "linaza",
        "flax",
    ],
    "animal_protein": [
        "pollo",
        "pechuga",
        "pescado",
        "salmon",
        "salmón",
        "atun",
        "atún",
        "carne",
        "vacuno",
        "beef",
        "turkey",
        "cerdo",
        "pork",
        "huevo",
        "huevos",
        "egg",
        "milk",
        "leche",
        "queso",
        "yogur",
        "yogurt",
    ],
    "plant_protein": [
        "lenteja",
        "lentejas",
        "garbanzo",
        "garbanzos",
        "legumbre",
        "legumbres",
        "tofu",
        "soja",
        "soya",
        "quinoa",
        "hummus",
    ],
}

TAG_DIVERSITY_TARGETS: Dict[str, int] = {
    "fruit": 8,
    "vegetable": 8,
    "plant_protein": 6,
    "animal_protein": 6,
    "nut_or_seed": 4,
}

from .catalog import get_catalog

# Plantillas de comidas para forzar variedad y asignar periodos específicos
MEAL_TEMPLATES = [
    {
        "name": "Desayuno",
        "keywords": [
            "desayuno",
            "breakfast",
            "oat",
            "avena",
            "granola",
            "yogur",
            "yogurt",
            "fruit",
            "fruta",
            "banana",
            "pan",
            "bread",
            "leche",
            "milk",
            "smoothie",
            "cereal",
            "huevo",
            "egg",
        ],
        "allow_sweets": False,
        "note": "Energía ligera para partir el día.",
        "required_tags": ["fruit"],
    },
    {
        "name": "Almuerzo",
        "keywords": [
            "almuerzo",
            "lunch",
            "meal",
            "rice",
            "arroz",
            "pasta",
            "quinoa",
            "ensalada",
            "salad",
            "vegetable",
            "verdura",
            "pollo",
            "chicken",
            "pavo",
            "turkey",
            "carne",
            "beef",
            "vacuno",
            "cerdo",
            "pork",
            "pescado",
            "fish",
            "salmon",
            "atun",
            "legumbre",
            "garbanzo",
            "lenteja",
            "sopa",
            "soup",
        ],
        "allow_sweets": False,
        "note": "Plato principal equilibrado.",
        "required_tags": ["vegetable"],
    },
    {
        "name": "Merienda",
        "keywords": [
            "snack",
            "colacion",
            "merienda",
            "fruit",
            "fruta",
            "nuez",
            "nut",
            "almendra",
            "almond",
            "yogur",
            "yogurt",
            "queso",
            "cheese",
            "proteina",
            "protein",
            "granola",
            "hummus",
        ],
        "allow_sweets": True,
        "note": "Colación ligera para mantener energía estable.",
        "required_tags": ["fruit"],
        "meal_tag_limits": {"nut_or_seed": 1},
    },
    {
        "name": "Cena",
        "keywords": [
            "cena",
            "dinner",
            "sopa",
            "soup",
            "crema",
            "pescado",
            "fish",
            "pollo",
            "chicken",
            "tofu",
            "omelette",
            "omelet",
            "huevo",
            "egg",
            "verdura",
            "vegetable",
            "ensalada",
            "salad",
            "wok",
        ],
        "allow_sweets": False,
        "note": "Preparaciones ligeras para apoyar el descanso.",
        "required_tags": ["vegetable", "animal_protein", "plant_protein"],
    },
]

SWEET_KEYWORDS = {
    "chocolate",
    "galleta",
    "cookie",
    "dulce",
    "candy",
    "caramelo",
    "wafer",
    "postre",
    "helado",
    "torta",
    "cake",
    "brownie",
    "alfajor",
    "confite",
}

MAX_DUPLICATES_PER_ITEM = 1
MIN_MEAL_KCAL = 60.0


def _normalized_text(item: Dict[str, Any], cache: Dict[str, str]) -> str:
    cache_key = item.get("id") or item.get("name")
    if cache_key and cache_key in cache:
        return cache[cache_key]
    parts: List[str] = []
    for key in ("name", "name_es", "brands"):
        val = item.get(key)
        if val:
            parts.append(str(val))
    categories = item.get("categories") or []
    parts.extend([str(c) for c in categories])
    text = " ".join(parts).lower()
    if cache_key:
        cache[cache_key] = text
    return text


def _matches_keywords(text: str, keywords: List[str]) -> bool:
    if not keywords:
        return True
    return any(k in text for k in keywords)


def _is_sweet(text: str) -> bool:
    return any(sw in text for sw in SWEET_KEYWORDS)


def _tags_for_text(text: str) -> Set[str]:
    tags: Set[str] = set()
    for tag, kws in TAG_KEYWORDS.items():
        if any(k in text for k in kws):
            tags.add(tag)
    return tags


def _pick_candidate(
    items: List[Dict[str, Any]],
    used_counts: Dict[str, int],
    used_in_meal: Set[str],
    keywords: List[str],
    allow_sweets: bool,
    text_cache: Dict[str, str],
    max_repeats: int,
    pending_tags: Optional[Set[str]] = None,
    meal_tag_counts: Optional[Dict[str, int]] = None,
    meal_tag_limits: Optional[Dict[str, int]] = None,
) -> Optional[Dict[str, Any]]:
    pending_tags = pending_tags or set()
    meal_tag_counts = meal_tag_counts or {}
    meal_tag_limits = meal_tag_limits or {}
    for candidate in items:
        cid = candidate.get("id") or candidate.get("name")
        if not cid:
            continue
        if used_counts.get(cid, 0) >= max_repeats:
            continue
        if cid in used_in_meal:
            continue
        text = _normalized_text(candidate, text_cache)
        tags = _tags_for_text(text)
        if any(meal_tag_counts.get(tag, 0) >= meal_tag_limits.get(tag, 999) for tag in tags):
            continue
        if keywords and not _matches_keywords(text, keywords):
            continue
        if not allow_sweets and _is_sweet(text):
            continue
        if pending_tags and not tags.intersection(pending_tags):
            continue
        return candidate
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
    used_counts: Dict[str, int] = {}
    text_cache: Dict[str, str] = {}

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

    # pre-sort items according to objective to bias selection
    if objetivo_norm in {'hipertrofia', 'ganar masa', 'ganar_masa'}:
        # prefer high energy density and reasonable protein
        items.sort(key=lambda it: ((it.get('energy_kcal_100g') or 0.0) * 0.7 + (it.get('proteins_g_100g') or 0.0) * 8.0), reverse=True)
    elif objetivo_norm in {'bajar_grasa', 'perder_peso', 'perder_grasa'}:
        # prefer higher protein and lower energy density
        items.sort(key=lambda it: ((it.get('proteins_g_100g') or 0.0) * 12.0 - (it.get('energy_kcal_100g') or 0.0) * 0.5), reverse=True)
    else:
        items.sort(key=score_item, reverse=True)

    def meal_template_for_index(idx: int) -> Dict[str, Any]:
        if idx < len(MEAL_TEMPLATES):
            return MEAL_TEMPLATES[idx]
        # fallback template for extra snacks/comidas
        return {
            "name": f"Comida {idx + 1}",
            "keywords": [],
            "allow_sweets": False,
            "note": None,
            "required_tags": [],
        }

    for m in range(n_meals):
        template = meal_template_for_index(m)
        remaining = meal_target
        meal_items: List[Dict[str, Any]] = []
        used_in_meal: Set[str] = set()
        meal_tag_counts: Dict[str, int] = defaultdict(int)
        pending_tags: Set[str] = set(template.get("required_tags", []))
        deferred_items: List[Dict[str, Any]] = []
        attempts = 0

        # limit items per meal
        while remaining > MIN_MEAL_KCAL and attempts < 12 and len(meal_items) < 5:
            attempts += 1
            candidate = _pick_candidate(
                items,
                used_counts,
                used_in_meal,
                template.get("keywords", []),
                template.get("allow_sweets", False),
                text_cache,
                MAX_DUPLICATES_PER_ITEM,
                pending_tags=pending_tags,
                meal_tag_counts=meal_tag_counts,
                meal_tag_limits=template.get("meal_tag_limits"),
                )
            if not candidate:
                # relax keyword restriction, then sweets restriction as last resort
                candidate = _pick_candidate(
                    items,
                    used_counts,
                    used_in_meal,
                    [],
                    template.get("allow_sweets", False),
                    text_cache,
                    MAX_DUPLICATES_PER_ITEM,
                    pending_tags=pending_tags,
                    meal_tag_counts=meal_tag_counts,
                    meal_tag_limits=template.get("meal_tag_limits"),
                )
            if not candidate and not template.get("allow_sweets", False):
                candidate = _pick_candidate(
                    items,
                    used_counts,
                    used_in_meal,
                    [],
                    True,
                    text_cache,
                    MAX_DUPLICATES_PER_ITEM,
                    pending_tags=pending_tags,
                    meal_tag_counts=meal_tag_counts,
                    meal_tag_limits=template.get("meal_tag_limits"),
                )
            if not candidate:
                break

            ek = candidate.get('energy_kcal_100g') or 0.0
            if ek <= 0:
                try:
                    items.remove(candidate)
                except ValueError:
                    pass
                continue

            if objetivo_norm in {'hipertrofia', 'ganar masa', 'ganar_masa'}:
                frac = 0.55
            elif objetivo_norm in {'bajar_grasa', 'perder_peso', 'perder_grasa'}:
                frac = 0.3
            else:
                frac = 0.4

            qty = floor((remaining * frac) / ek * 100)
            if qty < 30:
                qty = 30
            if qty > 450:
                qty = 450

            kcal_added = ek * qty / 100.0
            item_id = candidate.get('id') or candidate.get('name')
            meal_items.append({
                'id': candidate.get('id'),
                'name': candidate.get('name'),
                'qty_g': int(qty),
                'kcal': round(kcal_added, 1),
                'energy_kcal_100g': ek,
            })
            tags = _tags_for_text(_normalized_text(candidate, text_cache))
            for tag in tags:
                if tag in pending_tags:
                    pending_tags.discard(tag)
                    break
            for tag in tags:
                meal_tag_counts[tag] += 1
            if item_id:
                used_counts[item_id] = used_counts.get(item_id, 0) + 1
                used_in_meal.add(item_id)
                if used_counts[item_id] >= MAX_DUPLICATES_PER_ITEM:
                    try:
                        items.remove(candidate)
                    except ValueError:
                        pass
            remaining -= kcal_added

        meal_kcal = round(sum(it['kcal'] for it in meal_items), 1)
        meals.append({
            'name': template.get('name', f'Comida {m+1}'),
            'items': meal_items,
            'kcal': meal_kcal,
            'notes': template.get('note'),
        })

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
