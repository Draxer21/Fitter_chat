#!/usr/bin/env python3
"""
Importador de productos alimenticios específicamente de Chile desde OpenFoodFacts
Filtra por país de venta: Chile

Uso:
    python scripts/import_openfoodfacts_chile.py --limit 3000 --output backend/data/food_catalog_chile.json
"""
import argparse
import json
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


def pick_name(product: Dict[str, Any]) -> str:
    """Prioriza nombre en español"""
    # Intenta nombre en español primero
    if "product_name_es" in product and product["product_name_es"]:
        return product["product_name_es"]
    if "product_name" in product and product["product_name"]:
        return product["product_name"]
    return product.get("code", "unknown")


def normalize_product(product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normaliza un producto de OpenFoodFacts al formato del catálogo"""
    nutriments = product.get("nutriments", {})
    
    # Energía en kcal por 100g
    energy = None
    if "energy-kcal_100g" in nutriments:
        energy = to_float(nutriments.get("energy-kcal_100g"))
    elif "energy_100g" in nutriments:
        v = to_float(nutriments.get("energy_100g"))
        if v is not None:
            # Si v > 1000 asume kJ, convierte a kcal
            energy = v / 4.184 if v > 1000 else v

    # Macros por 100g
    proteins = to_float(nutriments.get("proteins_100g"))
    carbs = to_float(nutriments.get("carbohydrates_100g"))
    fats = to_float(nutriments.get("fat_100g"))

    # Filtro: necesita al menos energía y un macro
    if energy is None or (proteins is None and carbs is None and fats is None):
        return None

    # Serving size
    serving_size = None
    serving_str = product.get("serving_size", "")
    if serving_str:
        import re
        match = re.search(r"(\d+\.?\d*)\s*g", serving_str, re.IGNORECASE)
        if match:
            serving_size = to_float(match.group(1))

    # Alérgenos
    allergens_tags = product.get("allergens_tags", [])
    allergens = [a for a in allergens_tags if a]

    # Categorías
    categories_tags = product.get("categories_tags", [])
    categories = [c for c in categories_tags if c]

    # Marcas
    brands = product.get("brands", "")

    # URL del producto
    code = product.get("code", "")
    url = f"https://world.openfoodfacts.org/product/{code}" if code else ""

    name = pick_name(product)
    
    return {
        "id": code,
        "name": name,
        "name_es": name,  # Ya priorizamos español
        "categories": categories,
        "energy_kcal_100g": energy,
        "proteins_g_100g": proteins,
        "carbs_g_100g": carbs,
        "fats_g_100g": fats,
        "serving_size_g": serving_size,
        "allergens": allergens,
        "brands": brands,
        "url": url,
        "source": "openfoodfacts_chile"
    }


def fetch_products_chile(page: int = 1, page_size: int = 100, timeout: int = 30) -> Dict[str, Any]:
    """
    Busca productos vendidos en Chile
    """
    params = {
        "search_terms": "",
        "search_simple": 1,
        "action": "process",
        "tagtype_0": "countries",
        "tag_contains_0": "contains",
        "tag_0": "chile",  # Filtro por país Chile
        "page": page,
        "page_size": page_size,
        "json": 1,
    }
    r = requests.get(API_SEARCH_URL, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()


def import_openfoodfacts_chile(limit: int, output: str, page_size: int = 100, timeout: int = 30, retries: int = 3):
    """
    Importa productos de Chile desde OpenFoodFacts
    """
    page = 1
    per_page = page_size
    collected: List[Dict[str, Any]] = []
    
    print(f"🇨🇱 Iniciando importación de productos de CHILE desde OpenFoodFacts")
    print(f"   Límite: {limit} productos")
    print(f"   Página: {per_page} items por página")
    print(f"   Timeout: {timeout}s")
    print(f"   Reintentos: {retries}")
    print()
    
    while len(collected) < limit:
        print(f"📥 Obteniendo página {page}...")
        attempt = 0
        
        while True:
            try:
                data = fetch_products_chile(page=page, page_size=per_page, timeout=timeout)
                break
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                attempt += 1
                if attempt > retries:
                    print(f"❌ Falló página {page} después de {retries} reintentos: {e}")
                    break
                wait = 2 ** attempt
                print(f"⏳ Error de conexión, reintento {attempt}/{retries}, esperando {wait}s...")
                import time
                time.sleep(wait)
        
        products = data.get("products", [])
        if not products:
            print(f"⚠️  No se encontraron más productos en la página {page}")
            break
        
        for product in products:
            if len(collected) >= limit:
                break
            item = normalize_product(product)
            if item is None:
                continue
            collected.append(item)
        
        print(f"   ✅ Página {page}: {len(products)} productos obtenidos, total acumulado: {len(collected)}")
        page += 1
    
    print(f"\n📊 Recolectados {len(collected)} productos chilenos")
    print(f"💾 Guardando en {output}...")
    
    with open(output, "w", encoding="utf-8") as f:
        json.dump(collected, f, ensure_ascii=False, indent=2)
    
    print(f"✅ ¡Completado! Archivo guardado exitosamente.")


def main():
    parser = argparse.ArgumentParser(description='Importar productos de Chile desde OpenFoodFacts')
    parser.add_argument("--limit", type=int, default=3000, help="Número máximo de productos a importar")
    parser.add_argument("--output", default="backend/data/food_catalog_chile.json", help="Archivo de salida")
    parser.add_argument("--page-size", type=int, default=100, help="Items por página")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout en segundos")
    parser.add_argument("--retries", type=int, default=3, help="Reintentos por página")
    
    args = parser.parse_args()
    
    import_openfoodfacts_chile(
        args.limit, 
        args.output, 
        page_size=args.page_size, 
        timeout=args.timeout, 
        retries=args.retries
    )


if __name__ == "__main__":
    main()
