"""Compartir utilidades entre planners de rutina y dieta."""

from __future__ import annotations

from typing import Dict, List, Optional
import re


def parse_health_flags(text: Optional[str]) -> Dict[str, bool]:
    raw = (text or "").strip().lower()
    if not raw or raw in {"ninguna", "ninguno", "ningunas", "ningunos", "sin", "no"}:
        return {}
    flags = {
        "hipertension": any(k in raw for k in ("hipertension", "hipertensión", "presion alta", "tension alta")),
        "cardiaco": any(k in raw for k in ("cardi", "corazon", "cardiopatia", "arritmia", "infarto")),
        "diabetes": "diabet" in raw,
        "asma": "asma" in raw or "respir" in raw,
    }
    return {k: v for k, v in flags.items() if v}


def build_health_notes(flags: Dict[str, bool]) -> List[str]:
    notes: List[str] = []
    if flags.get("hipertension") or flags.get("cardiaco"):
        notes.append("Manten intensidad moderada (RPE ≤ 7) y evita bloqueos de respiración.")
    if flags.get("diabetes"):
        notes.append("Controla glucosa antes/después y prioriza carbohidratos complejos.")
    if flags.get("asma"):
        notes.append("Incluye calentamientos largos y ten el inhalador disponible.")
    return notes


def parse_allergy_list(text: Optional[str]) -> List[str]:
    raw = (text or "").strip().lower()
    if not raw or raw in {"ninguna", "ninguno", "ningunas", "ningunos", "no"}:
        return []
    normalized = raw.replace(" y ", ",").replace("/", ",")
    return [item.strip() for item in re.split(r"[;,]", normalized) if item.strip()]


def equip_key_norm(equip: str) -> str:
    """Normaliza claves de equipamiento."""
    e = (equip or "").strip().lower()
    mapping = {
        "peso corporal": "peso_corporal",
        "peso_corporal": "peso_corporal",
        "sin equipo": "peso_corporal",
        "sin equipamiento": "peso_corporal",
        "cuerpo libre": "peso_corporal",
        "nada": "peso_corporal",
        "maquinas": "máquinas",
    }
    return mapping.get(e, e)
