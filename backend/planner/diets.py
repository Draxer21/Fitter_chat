"""Planificador de dietas reutilizable."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from urllib.parse import quote

from .common import parse_allergy_list, parse_health_flags

def mifflin_st_jeor(weight_kg: float, height_cm: float, age: int, sex: Optional[str]) -> float:
    """Calcula BMR usando Mifflin-St Jeor. sex: 'f' o 'm' (insensible a mayúsculas)."""
    s = -161 if (str(sex or "").strip().lower().startswith("f")) else 5
    try:
        return 10.0 * float(weight_kg) + 6.25 * float(height_cm) - 5.0 * float(age) + s
    except Exception:
        return 0.0


ACTIVITY_MULTIPLIERS: Dict[str, float] = {
    "sedentario": 1.2,
    "ligero": 1.375,
    "moderado": 1.55,
    "activo": 1.725,
    "muy_activo": 1.9,
}

SOMATOTIPO_TIPS: Dict[str, str] = {
    "ectomorfo": "Enfoca en energía y carbohidratos complejos; comidas frecuentes ayudan.",
    "mesomorfo": "Mantén balance estable de macros; prioriza calidad y timing.",
    "endomorfo": "Prioriza proteína/fibra y controla carbohidratos de alta carga.",
}


def calc_target_kcal_and_macros(
    weight_kg: Optional[float],
    height_cm: Optional[float],
    age: Optional[int],
    sex: Optional[str],
    activity_level: Optional[str],
    objetivo: str,
    somatotipo: Optional[str] = None,
) -> Dict[str, Any]:
    """Retorna dict con bmr, maintenance_kcal, target_kcal y macros en gramos.
    Esta función es opt-in y no altera el flujo por defecto si faltan datos.
    """
    result: Dict[str, Any] = {
        "bmr": None,
        "maintenance_kcal": None,
        "target_kcal": None,
        "proteinas_g": None,
        "carbs_g": None,
        "fats_g": None,
        "note": None,
    }

    if not weight_kg or not height_cm:
        result["note"] = "Insuficientes datos para cálculo (falta peso o altura)."
        return result

    # defaults
    age_val = int(age) if (age is not None) else 30
    sex_val = (sex or "m").strip().lower()
    activity_key = (activity_level or "moderado").strip().lower()
    mult = ACTIVITY_MULTIPLIERS.get(activity_key, ACTIVITY_MULTIPLIERS["moderado"])

    bmr = mifflin_st_jeor(weight_kg, height_cm, age_val, sex_val)
    maintenance = bmr * mult

    # objective adjustment
    objetivo_norm = (objetivo or "").strip().lower()
    if objetivo_norm in {"bajar_grasa", "perder_grasa", "bajar grasa", "perder peso"}:
        target = maintenance - 300
    elif objetivo_norm in {"hipertrofia", "ganar masa", "ganar masa muscular"}:
        target = maintenance + 200
    else:
        target = maintenance

    # Proteínas: g/kg según objetivo
    if objetivo_norm in {"hipertrofia", "ganar masa"}:
        prot_per_kg = 1.8
    elif objetivo_norm in {"bajar_grasa", "bajar grasa"}:
        prot_per_kg = 2.0
    else:
        prot_per_kg = 1.6

    proteinas_g = round(prot_per_kg * weight_kg)
    proteinas_kcal = proteinas_g * 4

    # distribuir resto: 25% kcal a grasas, resto a carbs
    remaining_kcal = max(0, target - proteinas_kcal)
    fats_kcal = remaining_kcal * 0.25
    carbs_kcal = remaining_kcal - fats_kcal

    fats_g = round(fats_kcal / 9)
    carbs_g = round(carbs_kcal / 4)

    somatotipo_norm = (somatotipo or "").strip().lower()
    if somatotipo_norm in {"ectomorfo", "mesomorfo", "endomorfo"}:
        multipliers = {
            "ectomorfo": {"protein": 1.0, "carbs": 1.08, "fats": 0.9},
            "mesomorfo": {"protein": 1.0, "carbs": 1.0, "fats": 1.0},
            "endomorfo": {"protein": 1.05, "carbs": 0.9, "fats": 1.05},
        }.get(somatotipo_norm, {})
        if multipliers:
            protein_kcal = proteinas_g * 4
            carbs_kcal = carbs_g * 4
            fats_kcal = fats_g * 9
            weighted = {
                "protein": protein_kcal * multipliers["protein"],
                "carbs": carbs_kcal * multipliers["carbs"],
                "fats": fats_kcal * multipliers["fats"],
            }
            total_weight = sum(weighted.values()) or target
            target_val = float(target) if target else float(total_weight)
            protein_kcal = target_val * (weighted["protein"] / total_weight)
            carbs_kcal = target_val * (weighted["carbs"] / total_weight)
            fats_kcal = target_val * (weighted["fats"] / total_weight)
            proteinas_g = round(protein_kcal / 4)
            carbs_g = round(carbs_kcal / 4)
            fats_g = round(fats_kcal / 9)

    result.update({
        "bmr": round(bmr),
        "maintenance_kcal": round(maintenance),
        "target_kcal": round(target),
        "proteinas_g": int(proteinas_g),
        "carbs_g": int(carbs_g),
        "fats_g": int(fats_g),
    })

    if age is None or sex is None:
        result["note"] = "Algunos datos (edad/sexo) faltan; resultados aproximados."

    return result




DIET_BASES: Dict[str, Dict[str, Any]] = {
    "hipertrofia": {
        "calorias": "Mantenimiento + 200 kcal",
        "macros": {"proteinas": "2.0 g/kg", "carbohidratos": "5 g/kg", "grasas": "0.9 g/kg"},
        "meals": [
            {
                "name": "Desayuno",
                "items": ["Avena con leche descremada y frutos rojos", "Tortilla de 2 huevos + 2 claras"],
                "notes": "Agrega una fruta extra si entrenas en la manana."
            },
            {
                "name": "Almuerzo",
                "items": ["Pechuga de pollo a la plancha", "Arroz integral", "Ensalada con aceite de oliva"],
                "notes": "Incluye verduras de colores para micronutrientes."
            },
            {
                "name": "Merienda",
                "items": ["Yogur griego natural", "Nueces o mani sin sal"],
                "notes": "Ideal 90 min antes del entrenamiento."
            },
            {
                "name": "Cena",
                "items": ["Salmón u otra proteina grasa", "Batata asada", "Verduras al vapor"],
                "notes": "Añade semillas de chia o lino para omega 3."
            }
        ],
        "hydration": "2.5 L de agua con un vaso adicional por cada 20 min de entrenamiento intenso."
    },
    "fuerza": {
        "calorias": "Mantenimiento ± 0-100 kcal",
        "macros": {"proteinas": "1.8 g/kg", "carbohidratos": "4 g/kg", "grasas": "1 g/kg"},
        "meals": [
            {
                "name": "Desayuno",
                "items": ["Pan integral con palta", "Huevos revueltos", "Cafe sin azucar"],
                "notes": "Añade sal y potasio moderados para rendimiento."
            },
            {
                "name": "Almuerzo",
                "items": ["Carne magra", "Quinoa", "Brocoli al vapor"],
                "notes": "Utiliza hierbas en vez de salsas altas en sodio."
            },
            {
                "name": "Snack post entrenamiento",
                "items": ["Batido de proteina", "Banana"],
                "notes": "Consumir dentro de 45 min tras entrenar."
            },
            {
                "name": "Cena",
                "items": ["Pavo o tofu", "Pure de papas", "Verduras salteadas"],
                "notes": "Prioriza grasas saludables como aceite de oliva."
            }
        ],
        "hydration": "2.2 L de agua + 500 ml durante la sesion con electrolitos ligeros."
    },
    "bajar_grasa": {
        "calorias": "Déficit aproximado -300 kcal",
        "macros": {"proteinas": "2.0 g/kg", "carbohidratos": "3 g/kg", "grasas": "0.8 g/kg"},
        "meals": [
            {
                "name": "Desayuno",
                "items": ["Smoothie verde (espinaca, pepino, manzana)", "Yogur alto en proteina"],
                "notes": "Añade semillas para saciedad."
            },
            {
                "name": "Almuerzo",
                "items": ["Filete de pescado blanco", "Ensalada grande con legumbres"],
                "notes": "Evita aderezos con azúcar."
            },
            {
                "name": "Colacion",
                "items": ["Hummus con zanahoria y apio"],
                "notes": "Buena opcion baja en calorias y alta en fibra."
            },
            {
                "name": "Cena",
                "items": ["Wok de tofu o pollo", "Verduras salteadas", "Arroz de coliflor"],
                "notes": "Mantén las porciones controladas."
            }
        ],
        "hydration": "3.0 L de agua repartidos en el dia (apoyo a saciedad)."
    },
    "resistencia": {
        "calorias": "Mantenimiento + 100 kcal en dias de entrenamiento largo",
        "macros": {"proteinas": "1.6 g/kg", "carbohidratos": "5-7 g/kg", "grasas": "0.8 g/kg"},
        "meals": [
            {
                "name": "Desayuno pre entrenamiento",
                "items": ["Avena con banana y miel", "Bebida isotonica suave"],
                "notes": "Consumir 90 min antes de la sesion."
            },
            {
                "name": "Almuerzo",
                "items": ["Pasta integral con pollo", "Verduras salteadas"],
                "notes": "Agrega sodio controlado si sudas mucho."
            },
            {
                "name": "Snack",
                "items": ["Barra casera de avena y frutos secos"],
                "notes": "Ideal entre sesiones dobles."
            },
            {
                "name": "Cena",
                "items": ["Legumbres (lentejas/ch garbanzos)", "Ensalada variada", "Fruta"],
                "notes": "Recupera glucogeno con carbohidratos complejos."
            }
        ],
        "hydration": "Bebe 35 ml por kg de peso + reposiciona 500 ml por cada hora de cardio."
    },
    "equilibrada": {
        "calorias": "Mantenimiento",
        "macros": {"proteinas": "1.6 g/kg", "carbohidratos": "4 g/kg", "grasas": "0.9 g/kg"},
        "meals": [
            {
                "name": "Desayuno",
                "items": ["Yogur natural con granola", "Fruta de temporada"],
                "notes": "Incluye frutos secos si necesitas energia extra."
            },
            {
                "name": "Almuerzo",
                "items": ["Pechuga de pollo", "Arroz integral", "Ensalada de hojas"],
                "notes": "Sazona con hierbas y limon."
            },
            {
                "name": "Merienda",
                "items": ["Sandwich integral con pavo", "Verduras crudas"],
                "notes": "Buena combinacion de proteina y carbohidrato."
            },
            {
                "name": "Cena",
                "items": ["Omelette de verduras", "Pan integral o quinoa"],
                "notes": "Añade aguacate para grasas saludables."
            }
        ],
        "hydration": "2.0 L de agua al dia como base."
    }
}



def generate_diet_plan(
    *,
    objetivo: str,
    nivel: str,
    alergias: Optional[str],
    dislikes: Optional[str],
    condiciones: Optional[str],
    profile_data: Optional[Dict[str, Any]] = None,
    peso_slot: Optional[float] = None,
    enable_calc: bool = False,
    enable_catalog: bool = False,
    compose_callback: Optional[Callable[..., Dict[str, Any]]] = None,
    catalog_path: Optional[str] = None,
    catalog_items: Optional[List[Dict[str, Any]]] = None,
    catalog_loader: Optional[Callable[[], List[Dict[str, Any]]]] = None,
) -> Dict[str, Any]:
    objetivo_norm = (objetivo or "equilibrada").strip().lower()
    nivel_norm = (nivel or "intermedio").strip().lower()

    plan = DIET_BASES.get(objetivo_norm) or DIET_BASES.get("equilibrada")
    plan_label = objetivo_norm if objetivo_norm in DIET_BASES else "equilibrada"

    health_flags = parse_health_flags(condiciones)
    allergy_list = parse_allergy_list(alergias)
    dislike_list = parse_allergy_list(dislikes)

    adjustments: List[str] = []
    if health_flags.get("hipertension") or health_flags.get("cardiaco"):
        adjustments.append("Reduce sodio: condimenta con hierbas, evita embutidos y frituras.")
    if health_flags.get("diabetes"):
        adjustments.append("Distribuye carbohidratos complejos en porciones moderadas cada 3-4 horas.")
    if health_flags.get("asma"):
        adjustments.append("Incluye alimentos antiinflamatorios (omega 3, frutas variadas).")
    somatotipo = (profile_data.get("somatotipo") if profile_data else None)
    if somatotipo:
        somatotipo_norm = str(somatotipo).strip().lower()
        if somatotipo_norm not in {"no_se", "no se", "no sé", "ninguno", "ninguna"}:
            tip = SOMATOTIPO_TIPS.get(somatotipo_norm)
            if tip:
                adjustments.append(f"Somatotipo (heurístico): {somatotipo_norm}. {tip}")

    meals = plan.get("meals", [])
    filtered_meals: List[Dict[str, Any]] = []
    allergen_hits: List[Dict[str, Any]] = []
    for meal in meals:
        joined = " ".join(meal.get("items", [])).lower()
        if allergy_list and any(token in joined for token in allergy_list):
            allergen_hits.append({"meal": meal.get("name"), "items": meal.get("items", [])})
            continue
        if dislike_list and any(token in joined for token in dislike_list):
            allergen_hits.append({"meal": meal.get("name"), "items": meal.get("items", [])})
            continue
        filtered_meals.append(meal)
    if not filtered_meals:
        filtered_meals = meals

    if (allergy_list or dislike_list) and allergen_hits:
        adjustments.append("Reemplaza ingredientes en las comidas marcadas por alternativas seguras o evitadas.")

    macros = plan.get("macros", {})
    hydration = plan.get("hydration")

    dieta_calc_info: Optional[Dict[str, Any]] = None
    if enable_calc:
        try:
            weight = None
            if profile_data and profile_data.get("weight_kg") is not None:
                weight = float(profile_data.get("weight_kg"))
            elif peso_slot is not None:
                weight = float(peso_slot)
            height = None
            if profile_data and profile_data.get("height_cm") is not None:
                height = float(profile_data.get("height_cm"))
            age = None
            if profile_data and profile_data.get("age") is not None:
                age = int(profile_data.get("age"))
            sex = profile_data.get("sex") if profile_data else None
            activity = profile_data.get("activity_level") if profile_data else None
            somatotipo = profile_data.get("somatotipo") if profile_data else None
            dieta_calc_info = calc_target_kcal_and_macros(
                weight_kg=weight,
                height_cm=height,
                age=age,
                sex=sex,
                activity_level=activity,
                objetivo=objetivo_norm,
                somatotipo=somatotipo,
            )
        except Exception:
            dieta_calc_info = None

    lines: List[str] = [
        f"Plan alimenticio sugerido para objetivo {plan_label} (nivel {nivel_norm}).",
        f"Calorias estimadas: {plan.get('calorias', 'mantenimiento')}",
        "Macros orientativas:",
        f"- Proteinas: {macros.get('proteinas', '-')}",
        f"- Carbohidratos: {macros.get('carbohidratos', '-')}",
        f"- Grasas: {macros.get('grasas', '-')}",
    ]
    if adjustments:
        lines.append("Ajustes y personalización:")
        for note in adjustments:
            lines.append(f"- {note}")
    if allergy_list and not allergen_hits:
        lines.append("Se han considerado tus alergias registradas.")
    if dislike_list and not allergen_hits:
        lines.append("Se han evitado tus alimentos no deseados.")
    if not allergy_list and not dislike_list:
        lines.append("Si tienes alergias o alimentos que no te gusten, avisa para personalizar mas el plan.")
    if profile_data:
        perfil_bits: List[str] = []
        if profile_data.get("weight_kg"):
            perfil_bits.append(f"Peso: {profile_data['weight_kg']} kg")
        if profile_data.get("activity_level"):
            perfil_bits.append(f"Actividad: {profile_data['activity_level']}")
        if profile_data.get("notes"):
            perfil_bits.append("Notas personales consideradas.")
        if perfil_bits:
            lines.append("Datos del perfil: " + " | ".join(perfil_bits))

    diet_payload = {
        "type": "diet_plan",
        "objective": plan_label,
        "summary": {
            "calorias": plan.get("calorias"),
            "macros": macros,
            "somatotipo": (profile_data.get("somatotipo") if profile_data else None),
            **(
                {
                    "target_kcal": dieta_calc_info.get("target_kcal"),
                    "bmr": dieta_calc_info.get("bmr"),
                    "maintenance_kcal": dieta_calc_info.get("maintenance_kcal"),
                    "proteinas_g": dieta_calc_info.get("proteinas_g"),
                    "carbs_g": dieta_calc_info.get("carbs_g"),
                    "fats_g": dieta_calc_info.get("fats_g"),
                    "dieta_note": dieta_calc_info.get("note"),
                }
                if dieta_calc_info
                else {}
            ),
            "hydration": hydration,
            "health_adjustments": adjustments or None,
            "allergies": allergy_list or None,
            "dislikes": dislike_list or None,
            "medical_conditions": condiciones if condiciones and condiciones.lower() not in {"", "ninguna", "ninguno", "no"} else None,
            "allergen_hits": allergen_hits or None,
        },
        "meals": filtered_meals,
    }

    final_meals = filtered_meals
    used_composer = False
    if enable_catalog and compose_callback and dieta_calc_info and dieta_calc_info.get("target_kcal"):
        try:
            target_kcal = int(dieta_calc_info.get("target_kcal") or 2000)
            n_meals = len(filtered_meals) or 3
            weight_val = None
            if profile_data and profile_data.get("weight_kg") is not None:
                weight_val = float(profile_data.get("weight_kg"))
            elif peso_slot is not None:
                weight_val = float(peso_slot)
            composed = compose_callback(
                target_kcal,
                n_meals=n_meals,
                catalog_path=catalog_path,
                exclude_allergens=allergy_list or None,
                exclude_keywords=(allergy_list or []) + (dislike_list or []),
                objetivo=objetivo_norm,
                weight_kg=weight_val,
            )
            if composed and isinstance(composed, dict):
                composed_meals: List[Dict[str, Any]] = []
                for meal in composed.get("meals", []):
                    items_out: List[Dict[str, Any]] = []
                    for item in meal.get("items", []):
                        name = item.get("name") or item.get("id")
                        qty = item.get("qty_g") or item.get("qty") or 100
                        kcal = item.get("kcal")
                        items_out.append({"name": name, "qty": f"{int(qty)} g", "kcal": kcal})
                    composed_meals.append({"name": meal.get("name"), "items": items_out, "notes": None})
                diet_payload["meals"] = composed_meals
                final_meals = composed_meals
                used_composer = True
        except Exception:
            used_composer = False

    items_source = catalog_items
    if enable_catalog and not used_composer and items_source is None and catalog_loader:
        try:
            items_source = catalog_loader()
        except Exception:
            items_source = None

    if enable_catalog and not used_composer and items_source:
        composed_meals = []
        idx = 0
        for meal in filtered_meals:
            items_for_meal: List[Dict[str, Any]] = []
            for _ in range(3):
                if not items_source:
                    break
                item = items_source[idx % len(items_source)]
                idx += 1
                name = item.get("name") or item.get("name_es") or item.get("id")
                kcal100 = item.get("energy_kcal_100g") or 0
                qty_g = item.get("serving_size_g") or 100
                kcal = round((kcal100 * qty_g) / 100.0) if kcal100 else None
                items_for_meal.append(
                    {
                        "name": name,
                        "qty": f"{int(qty_g)} g",
                        "kcal": kcal,
                        "source": item.get("source"),
                    }
                )
            composed_meals.append({"name": meal.get("name"), "items": items_for_meal, "notes": meal.get("notes")})
        diet_payload["meals"] = composed_meals
        final_meals = composed_meals

    lines.append("Menu diario ejemplo:")
    for meal in final_meals:
        items = meal.get("items", [])
        if items and isinstance(items[0], dict):
            items_str = ", ".join(
                [f"{it.get('name')} ({it.get('qty', '100g')}, {it.get('kcal', '?')} kcal)" for it in items]
            )
        else:
            items_str = ", ".join(items)
        lines.append(f"- {meal.get('name', 'Comida')}: {items_str}")
        note = meal.get("notes")
        if note:
            lines.append(f"  Nota: {note}")
    if hydration:
        lines.append(f"Hidratacion recomendada: {hydration}")

    explanation = {
        "datos_usados": {
            "objetivo": plan_label,
            "nivel": nivel_norm,
            "alergias": alergias,
            "dislikes": dislikes,
            "condiciones": condiciones,
            "profile": profile_data or {},
        },
        "criterios": [
            "Macros base definidas por objetivo.",
            "Aplicacion de ajustes por salud declarada.",
            "Opcional: composicion de comidas desde catalogo propio.",
        ],
        "reglas": [
            "Alergias excluidas del menu." if allergy_list else "Sin alergias declaradas.",
            "Preferencias alimentarias respetadas." if dislike_list else "Sin preferencias excluyentes.",
        ],
        "fuentes": ["Guías internas Fitter, OMS 2020, Guías Alimentarias Chile."],
    }

    diet_payload["explanation"] = explanation

    context_payload: Dict[str, Any] = {}
    for key, value in (
        ("medical_conditions", condiciones),
        ("allergies", alergias),
        ("dislikes", dislikes),
    ):
        if value and str(value).strip().lower() not in {"", "ninguna", "ninguno", "no"}:
            context_payload[key] = value

    text_response = "\n".join(lines)
    return {
        "text": text_response,
        "diet_payload": diet_payload,
        "context_payload": context_payload,
    }
