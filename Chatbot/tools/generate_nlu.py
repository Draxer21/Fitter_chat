#!/usr/bin/env python
"""
Genera ejemplos de intents en formato Rasa NLU a partir de plantillas y listas de valores.

Uso rápido:

    python tools/generate_nlu.py \
        --spec-dir data/specs \
        --output data/generated/nlu_generated.yml \
        --per-intent 2000

Cada archivo dentro de --spec-dir debe ser un YAML con la siguiente estructura mínima:

intent: nombre_del_intent
templates:
  - "Frase con {slot}"
slots:
  slot:
    - valor1
    - valor2
static_examples:
  - "Frase fija opcional"

El script:
    * Expande cada plantilla combinando los valores de los slots.
    * Deduplica resultados y toma hasta --per-intent ejemplos (si hay menos, usa todos).
    * Mezcla los estáticos antes de muestrear para asegurar presencia.
    * Escribe un archivo NLU con formato Rasa (version 3.x).
"""

from __future__ import annotations

import argparse
import random
import sys
from itertools import product
from pathlib import Path
from string import Formatter
from typing import Dict, Iterable, List, Sequence, Set

import yaml


class SpecError(Exception):
    """Errores específicos de lectura o validación de specs."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generador de datos NLU a partir de plantillas.")
    parser.add_argument(
        "--spec-dir",
        type=Path,
        default=Path("data/specs"),
        help="Directorio con archivos YAML que describen cada intent.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/generated/nlu_generated.yml"),
        help="Ruta del archivo NLU resultante.",
    )
    parser.add_argument(
        "--per-intent",
        type=int,
        default=500,
        help="Cantidad objetivo de ejemplos por intent.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1337,
        help="Semilla para barajado aleatorio (permite reproducir resultados).",
    )
    parser.add_argument(
        "--min-ratio",
        type=float,
        default=0.5,
        help=(
            "Relación mínima entre ejemplos generados y objetivo. "
            "Si una combinación produce menos de (per_intent * min_ratio) ejemplos, se emitirá una advertencia."
        ),
    )
    return parser.parse_args()


def load_spec(file_path: Path) -> Dict:
    try:
        data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise SpecError(f"El archivo {file_path} no es un YAML válido: {exc}") from exc

    if not isinstance(data, dict):
        raise SpecError(f"El archivo {file_path} debe definir un mapeo con la clave 'intent'.")

    intent = data.get("intent")
    if not intent or not isinstance(intent, str):
        raise SpecError(f"{file_path}: falta la clave 'intent' o su valor no es una cadena.")

    templates = data.get("templates") or []
    if not templates or not isinstance(templates, list):
        raise SpecError(f"{file_path}: se requiere la lista 'templates' con al menos una frase.")

    slots = data.get("slots") or {}
    if slots and not isinstance(slots, dict):
        raise SpecError(f"{file_path}: 'slots' debe ser un diccionario de listas de valores.")

    # Validar que los valores de cada slot sean listas no vacías.
    for slot_name, values in slots.items():
        if not isinstance(values, list) or not values:
            raise SpecError(f"{file_path}: el slot '{slot_name}' debe tener una lista de valores no vacía.")

    static_examples = data.get("static_examples") or []
    if static_examples and not isinstance(static_examples, list):
        raise SpecError(f"{file_path}: 'static_examples' debe ser una lista de cadenas.")

    return {
        "intent": intent,
        "templates": templates,
        "slots": slots,
        "static_examples": static_examples,
        "path": file_path,
    }


def extract_placeholders(template: str) -> List[str]:
    formatter = Formatter()
    placeholders: List[str] = []
    for _, field_name, _, _ in formatter.parse(template):
        if field_name:
            placeholders.append(field_name)
    return placeholders


def expand_template(template: str, slots: Dict[str, Sequence[str]]) -> Iterable[str]:
    placeholders = extract_placeholders(template)
    if not placeholders:
        yield template
        return

    missing: Set[str] = {name for name in placeholders if name not in slots}
    if missing:
        raise SpecError(f"La plantilla '{template}' requiere slots no definidos: {', '.join(sorted(missing))}")

    value_lists: List[Sequence[str]] = [slots[name] for name in placeholders]
    for combination in product(*value_lists):
        values_map = dict(zip(placeholders, combination))
        yield template.format(**values_map)


def generate_examples(spec: Dict, target: int, rng: random.Random) -> List[str]:
    generated: List[str] = []
    for template in spec["templates"]:
        generated.extend(expand_template(template, spec["slots"]))

    # Deduplicar manteniendo orden determinista.
    deduped: List[str] = list(dict.fromkeys(generated))

    if len(deduped) < target:
        rng.shuffle(deduped)
        combined = list(dict.fromkeys(spec["static_examples"] + deduped))
        if len(combined) < target:
            return combined
        return combined[:target]

    rng.shuffle(deduped)

    static_examples = spec["static_examples"]
    selection = static_examples.copy()
    remaining_needed = target - len(selection)
    if remaining_needed < 0:
        selection = static_examples[:target]
        remaining_needed = 0
    selection.extend(deduped[:remaining_needed])
    return selection


def format_examples_rasa(examples: Sequence[str]) -> str:
    lines = [f"    - {text}" for text in examples]
    return "\n".join(lines)


def ensure_parent_directory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def main() -> int:
    args = parse_args()
    rng = random.Random(args.seed)

    if not args.spec_dir.exists():
        print(f"[ERROR] El directorio de specs no existe: {args.spec_dir}", file=sys.stderr)
        return 1

    specs_paths = sorted(args.spec_dir.glob("*.yml"))
    if not specs_paths:
        print(f"[ERROR] No se encontraron archivos .yml en {args.spec_dir}", file=sys.stderr)
        return 1

    output_blocks: List[str] = []
    warns: List[str] = []

    for path in specs_paths:
        spec = load_spec(path)
        examples = generate_examples(spec, args.per_intent, rng)
        if len(examples) < args.per_intent * args.min_ratio:
            warns.append(
                f"[ADVERTENCIA] {spec['intent']}: solo se generaron {len(examples)} ejemplos. "
                "Revisa si las combinaciones son suficientes o amplía las listas."
            )

        block = f"- intent: {spec['intent']}\n  examples: |\n{format_examples_rasa(examples)}"
        output_blocks.append(block)

    ensure_parent_directory(args.output)
    output_content = "version: \"3.1\"\n\nnlu:\n" + "\n".join(output_blocks) + "\n"
    args.output.write_text(output_content, encoding="utf-8")

    print(f"[OK] Archivo generado en {args.output} con {len(output_blocks)} intents.")
    for warn in warns:
        print(warn, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
