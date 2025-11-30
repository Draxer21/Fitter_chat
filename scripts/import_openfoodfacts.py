#!/usr/bin/env python3
"""
Importador y normalizador básico para OpenFoodFacts.
Ejecutar con: python scripts/import_openfoodfacts.py --lang es --limit 2000 --output backend/data/food_catalog.json

No se ejecuta automáticamente en CI; es un script utilitario para regenerar el catálogo.
"""
import argparse
import json
import math
import sys
from typing import Dict, Any, Optional, List

import requests

API_SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"


def to_float(v: Optional[float]) -> Optional[float]:
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


def pick_name(product: Dict[str, Any], lang: str) -> str:
    # prefer localized name
    name_key = f"product_name_{lang}"
    if name_key in product and product[name_key]:
        return product[name_key]
    if "product_name" in product and product["product_name"]:
        return product["product_name"]
    # fallback to generic code
    return product.get("code", "unknown")


def normalize_product(product: Dict[str, Any], lang: str) -> Optional[Dict[str, Any]]:
    nutriments = product.get("nutriments", {})
    # energy in kcal per 100g
    energy = None
    # OpenFoodFacts sometimes provides energy-kcal_100g or energy_100g in kJ
    if "energy-kcal_100g" in nutriments:
        energy = to_float(nutriments.get("energy-kcal_100g"))
    elif "energy_100g" in nutriments:
        # might be in kJ; try converting if large
        v = to_float(nutriments.get("energy_100g"))
        if v is not None:
            # if v > 1000 assume kJ, convert to kcal
            if v > 1500:
                energy = v / 4.184
            else:
                # could already be kcal
                energy = v
    proteins = to_float(nutriments.get("proteins_100g"))
    carbs = to_float(nutriments.get("carbohydrates_100g"))
    fats = to_float(nutriments.get("fat_100g"))

    # require at least energy or macros
    if energy is None and proteins is None and carbs is None and fats is None:
        return None

    # allergens: try to extract from product.get('allergens') (comma separated)
    allergens_raw = product.get("allergens", "") or product.get("allergens_from_ingredients", "")
    allergens = []
    if allergens_raw:
        for a in allergens_raw.split(","):
            a = a.strip().lower()
            if not a:
                continue
            allergens.append(a)

    serving = product.get("serving_size")
    serving_g = None
    if serving:
        # common formats: '30 g', '1 slice (30g)'
        try:
            parts = serving.split()
            for p in parts:
                if p.endswith("g") and p[:-1].replace('.', '', 1).isdigit():
                    serving_g = float(p[:-1])
                    break
        except Exception:
            serving_g = None

    item = {
        "id": product.get("code") or product.get("id") or product.get("_id"),
        "name": pick_name(product, lang),
        "name_es": product.get("product_name_es") or product.get("product_name"),
        "categories": product.get("categories_tags", []),
        "energy_kcal_100g": energy,
        "proteins_g_100g": proteins,
        "carbs_g_100g": carbs,
        "fats_g_100g": fats,
        "serving_size_g": serving_g,
        "allergens": allergens,
        "brands": product.get("brands"),
        "url": product.get("url"),
        "source": "openfoodfacts"
    }
    return item


def fetch_products(lang: str, page: int = 1, page_size: int = 100, timeout: int = 30) -> Dict[str, Any]:
    params = {
        "search_terms": "",
        "search_simple": 1,
        "action": "process",
        "tagtype_0": "countries",
        "tag_contains_0": "contains",
        "tag_0": lang,
        "page": page,
        "page_size": page_size,
        "json": 1,
    }
    r = requests.get(API_SEARCH_URL, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()


def import_openfoodfacts(lang: str, limit: int, output: str, page_size: int = 100, timeout: int = 30, retries: int = 3):
    page = 1
    per_page = page_size
    collected: List[Dict[str, Any]] = []
    print(f"Starting import from OpenFoodFacts lang={lang} limit={limit} page_size={per_page} timeout={timeout} retries={retries}")
    while len(collected) < limit:
        print(f"Fetching page {page}")
        attempt = 0
        while True:
            try:
                data = fetch_products(lang=lang, page=page, page_size=per_page, timeout=timeout)
                break
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                attempt += 1
                if attempt > retries:
                    print(f"Failed to fetch page {page} after {retries} retries: {e}")
                    return
                wait = 2 ** attempt
                print(f"Timeout/connection error fetching page {page}, retry {attempt}/{retries}, sleeping {wait}s")
                import time
                time.sleep(wait)

        products = data.get("products", [])
        if not products:
            break
        for p in products:
            item = normalize_product(p, lang)
            if item is None:
                continue
            collected.append(item)
            if len(collected) >= limit:
                break
        page += 1
    print(f"Collected {len(collected)} items, writing to {output}")
    with open(output, "w", encoding="utf-8") as f:
        json.dump(collected, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default="es", help="language code for products (es)")
    parser.add_argument("--limit", type=int, default=2000, help="maximum number of items to fetch")
    parser.add_argument("--output", default="backend/data/food_catalog.json")
    parser.add_argument("--page-size", type=int, default=100, help="items per page for API requests")
    parser.add_argument("--timeout", type=int, default=30, help="request timeout in seconds")
    parser.add_argument("--retries", type=int, default=3, help="number of retries per page on failure")
    args = parser.parse_args()
    import_openfoodfacts(args.lang, args.limit, args.output, page_size=args.page_size, timeout=args.timeout, retries=args.retries)


if __name__ == "__main__":
    main()
