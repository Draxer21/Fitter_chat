"""Genera un catálogo curado combinando alimentos manuales y el dataset grande.

Selecciona frutas, verduras, proteínas, bebidas, etc., pensado para LATAM
según palabras clave en nombres/categorías. Ejecutar con:

    python scripts/build_curated_catalog.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Any

BASE_DIR = Path(__file__).resolve().parents[1]
MANUAL_PATH = BASE_DIR / "backend" / "data" / "food_catalog_manual.json"
DATASET_PATH = BASE_DIR / "backend" / "data" / "food_catalog.json"
OUTPUT_PATH = BASE_DIR / "backend" / "data" / "food_catalog_curated.json"


GROUP_KEYWORDS: Dict[str, List[str]] = {
    "fruit": ["fruta", "fruit", "manzana", "banana", "platano", "plátano", "naranja", "uva", "berries", "frutos"],
    "vegetable": ["verdura", "vegetal", "vegetable", "ensalada", "brocoli", "brócoli", "espinaca", "zanahoria", "pepino", "tomate", "choclo"],
    "animal_protein": ["pollo", "pescado", "salmon", "salmón", "atun", "atún", "carne", "vacuno", "cerdo", "pavo", "huevo", "leche", "queso", "yogur", "lomo", "filete"],
    "plant_protein": ["lenteja", "garbanzo", "poroto", "legumbre", "soja", "tofu", "quinoa", "quinua", "almendra", "mani", "maní"],
    "nut_or_seed": ["nuez", "almendra", "semilla", "chia", "chía", "linaza", "maní", "pistacho", "avellana"],
    "carbonated": ["gaseosa", "soda", "cola", "carbonatada", "bebida", "refresco", "saborizada"],
    "rehydration": ["isoton", "rehidrat", "electrol", "gatorade", "powerade", "suero", "hidratante"],
    "non_perishable": ["enlat", "lata", "conserva", "instant", "deshidratado", "harina", "arroz", "pasta", "cereal"],
    "juice": ["jugo", "juice", "néctar", "nectar", "pulpa", "concentrado"],
}

GROUP_TARGETS: Dict[str, int] = {
    "fruit": 10,
    "vegetable": 10,
    "animal_protein": 8,
    "plant_protein": 8,
    "nut_or_seed": 6,
    "carbonated": 6,
    "rehydration": 4,
    "non_perishable": 8,
    "juice": 6,
}


def _normalized_text(item: Dict[str, Any]) -> str:
    parts: List[str] = []
    for key in ("name", "name_es", "brands"):
        val = item.get(key)
        if val:
            parts.append(str(val))
    cats = item.get("categories") or []
    parts.extend([str(c) for c in cats])
    return " ".join(parts).lower()


def matches_group(text: str, group: str) -> bool:
    keywords = GROUP_KEYWORDS.get(group, [])
    return any(kw in text for kw in keywords)


def priority(item: Dict[str, Any], group: str) -> float:
    proteins = item.get("proteins_g_100g") or 0.0
    energy = item.get("energy_kcal_100g") or 0.0
    carbs = item.get("carbs_g_100g") or 0.0
    if group in {"animal_protein", "plant_protein"}:
        return proteins * 10 + energy
    if group in {"carbonated", "rehydration", "juice"}:
        return carbs * 5 + energy
    if group in {"fruit", "vegetable"}:
        return energy
    if group == "nut_or_seed":
        return energy + proteins
    if group == "non_perishable":
        return energy + proteins + carbs
    return energy


def main() -> None:
    manual_items = []
    if MANUAL_PATH.exists():
        manual_items = json.loads(MANUAL_PATH.read_text())

    dataset_items = json.loads(DATASET_PATH.read_text())
    dataset_with_text = [(item, _normalized_text(item)) for item in dataset_items]

    selected: List[Dict[str, Any]] = []
    used_ids = set()

    for item in manual_items:
        iid = item.get("id")
        if iid and iid not in used_ids:
            selected.append(item)
            used_ids.add(iid)

    for group, target in GROUP_TARGETS.items():
        pool: List[Dict[str, Any]] = []
        for item, text in dataset_with_text:
            iid = item.get("id")
            if not iid or iid in used_ids:
                continue
            if matches_group(text, group):
                pool.append(item)
        pool.sort(key=lambda it: priority(it, group), reverse=True)
        added = 0
        for item in pool:
            iid = item.get("id")
            if not iid or iid in used_ids:
                continue
            selected.append(item)
            used_ids.add(iid)
            added += 1
            if added >= target:
                break
        print(f"{group}: {added} items añadidos")

    OUTPUT_PATH.write_text(json.dumps(selected, ensure_ascii=False, indent=2))
    print(f"Catálogo curado generado en {OUTPUT_PATH} con {len(selected)} alimentos")


if __name__ == "__main__":
    main()
