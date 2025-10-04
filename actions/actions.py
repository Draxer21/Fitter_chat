# actions/actions.py
from __future__ import annotations
from typing import Any, Text, Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
import os
import random
import re
import logging

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction  # <- Validador de formularios

logger = logging.getLogger(__name__)

# =========================================================
# Helpers
# =========================================================
def _slot(tracker: Tracker, name: str) -> Optional[str]:
    v = tracker.get_slot(name)
    return str(v).strip() if v is not None else None

def _safe_int(value: Optional[str], default: int, min_v: Optional[int] = None, max_v: Optional[int] = None) -> int:
    try:
        n = int(str(value).strip())
    except Exception:
        n = default
    if min_v is not None:
        n = max(min_v, n)
    if max_v is not None:
        n = min(max_v, n)
    return n

def _normaliza_fecha(value: Optional[str]) -> Optional[str]:
    """Devuelve fecha ISO (YYYY-MM-DD) o None si no puede normalizar."""
    if not value:
        return None
    v = value.strip().lower()
    v = v.replace("mañana", "manana")

    today = date.today()
    if v in ("hoy",):
        return today.isoformat()
    if v in ("manana",):
        return (today + timedelta(days=1)).isoformat()
    if v in ("ayer",):
        return (today - timedelta(days=1)).isoformat()

    try:
        return datetime.fromisoformat(v).date().isoformat()
    except Exception:
        pass

    m = re.match(r"^\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})\s*$", v)
    if m:
        d, mth, y = map(int, m.groups())
        try:
            return date(y, mth, d).isoformat()
        except Exception:
            return None

    m = re.match(r"^\s*(\d{4})[/-](\d{1,2})[/-](\d{1,2})\s*$", v)
    if m:
        y, mth, d = map(int, m.groups())
        try:
            return date(y, mth, d).isoformat()
        except Exception:
            return None

    return value

def _normaliza_hora(value: Optional[str]) -> Optional[str]:
    """Devuelve HH:MM (24h) o el valor original si no puede normalizar."""
    if not value:
        return None
    v = value.strip().lower().replace(".", ":")

    m = re.match(r"^\s*(\d{1,2})(?::?(\d{1,2}))?\s*(am|pm)?\s*$", v)
    if not m:
        return value
    h_str, m_str, ampm = m.groups()
    try:
        h = int(h_str)
        mi = int(m_str) if m_str is not None else 0
    except Exception:
        return value

    if ampm:
        if ampm == "am" and h == 12:
            h = 0
        elif ampm == "pm" and h != 12:
            h = (h % 12) + 12

    if not (0 <= h <= 23 and 0 <= mi <= 59):
        return value

    return f"{h:02d}:{mi:02d}"

def _equip_key_norm(equip: str) -> str:
    """Normaliza claves de equipamiento al diccionario (usa 'peso_corporal' con guion bajo)."""
    e = (equip or "").strip().lower()
    mapping = {
        "peso corporal": "peso_corporal",
        "peso_corporal": "peso_corporal",
        "sin equipo": "peso_corporal",
        "sin equipamiento": "peso_corporal",
        "cuerpo libre": "peso_corporal",
        "nada": "peso_corporal",
        "maquinas": "máquinas",  # normaliza a acentuado
    }
    return mapping.get(e, e)

# =========================================================
# Catálogos / Esquemas (demo)
# =========================================================

OBJECTIVE_TIPS: Dict[str, str] = {
    "hipertrofia": "Rango 8–12 repeticiones, RPE 7–8, descansos 60–90s.",
    "fuerza": "Rango 3–6 repeticiones, RPE 8–9, descansos 2–3 min.",
    "bajar_grasa": "Déficit calórico 10–20%, circuitos, y 2–3 sesiones de cardio/semana.",
    "resistencia": "Volumen moderado, pausas cortas, 20–30 min de trabajo aeróbico."
}

NUTRICION_TIPS: Dict[str, str] = {
    "hipertrofia":  "Proteínas 1.6–2.2 g/kg; superávit calórico leve (5–10%).",
    "bajar_grasa":  "Déficit 10–20%; proteínas 1.8–2.4 g/kg; fibra alta; hidratación.",
    "fuerza":       "Calorías de mantenimiento ±5%; hidratos pre/post entreno; sueño 7–9h.",
    "resistencia":  "Hidratos 5–7 g/kg; hidratación y electrolitos; proteína 1.4–1.8 g/kg."
}

# (nombre, url, fuente)
CATALOGO: Dict[str, Dict[str, List[Tuple[str, str, str]]]] = {
    "pecho": {
        "barra": [
            ("Press banca con barra", "https://exrx.net/WeightExercises/PectoralSternal/BBBenchPress", "ExRx"),
            ("Press inclinado con barra", "https://exrx.net/WeightExercises/PectoralClavicular/BBInclineBenchPress", "ExRx"),
            ("Press cerrado (tríceps)", "https://exrx.net/WeightExercises/Triceps/BBCloseGripBenchPress", "ExRx"),
            ("Press banca con pausa", "https://exrx.net/ExInfo/TempoTraining", "ExRx"),
            ("Fondos en paralelas lastrados", "https://exrx.net/WeightExercises/PectoralSternal/ASChestDip", "ExRx"),
            ("Press en máquina Smith", "https://exrx.net/WeightExercises/PectoralSternal/SMBenchPress", "ExRx"),
            ("Press declinado con barra", "https://exrx.net/WeightExercises/PectoralSternal/BBDeclineBenchPress", "ExRx"),
            ("Remo invertido agarre ancho", "https://exrx.net/WeightExercises/TrapeziusMiddle/BBInvertedRowWide", "ExRx")
        ],
        "mancuernas": [
            ("Press banca con mancuernas", "https://exrx.net/WeightExercises/PectoralSternal/DBBenchPress", "ExRx"),
            ("Press inclinado con mancuernas", "https://exrx.net/WeightExercises/PectoralClavicular/DBInclineBenchPress", "ExRx"),
            ("Aperturas planas", "https://exrx.net/WeightExercises/PectoralSternal/DBFly", "ExRx"),
            ("Press neutro con mancuernas", "https://exrx.net/WeightExercises/PectoralSternal/DBNeutralGripBenchPress", "ExRx"),
            ("Flexiones con lastre", "https://exrx.net/WeightExercises/PectoralSternal/BWPushupWeighted", "ExRx"),
            ("Aperturas inclinadas", "https://exrx.net/WeightExercises/PectoralClavicular/DBInclineFly", "ExRx"),
            ("Cruces en polea alta", "https://exrx.net/WeightExercises/PectoralSternal/CBStandingFly", "ExRx"),
            ("Flexiones pausa 2s abajo", "https://exrx.net/ExInfo/TempoTraining", "ExRx")
        ],
        "peso_corporal": [
            ("Flexiones estándar", "https://exrx.net/WeightExercises/PectoralSternal/BWPushup", "ExRx"),
            ("Flexiones diamante", "https://exrx.net/WeightExercises/Triceps/BWCloseTricepsPushup", "ExRx"),
            ("Flexiones inclinadas", "https://exrx.net/WeightExercises/PectoralSternal/BWInclinePushup", "ExRx"),
            ("Flexiones declinadas", "https://exrx.net/WeightExercises/PectoralSternal/BWDeclinePushup", "ExRx"),
            ("Flexiones arqueadas", "https://exrx.net/WeightExercises/PectoralSternal/BWArcherPushup", "ExRx"),
            ("Fondos en paralelas", "https://exrx.net/WeightExercises/PectoralSternal/ASChestDip", "ExRx"),
            ("Plancha con toques", "https://exrx.net/WeightExercises/RectusAbdominis/BWPlank", "ExRx"),
            ("Flexiones tempo 3-1-1", "https://exrx.net/ExInfo/TempoTraining", "ExRx")
        ]
    },
    "espalda": {
        "barra": [
            ("Peso muerto convencional", "https://exrx.net/WeightExercises/ErectorSpinae/BBDeadlift", "ExRx"),
            ("Remo con barra", "https://exrx.net/WeightExercises/BackGeneral/BBBentOverRow", "ExRx"),
            ("Peso muerto rumano", "https://exrx.net/WeightExercises/Hamstrings/BBRomanianDeadlift", "ExRx"),
            ("Remo Pendlay", "https://exrx.net/WeightExercises/BackGeneral/BBPendlayRow", "ExRx"),
            ("Jalón al pecho guiado", "https://exrx.net/WeightExercises/LatissimusDorsi/LVFrontPulldown", "ExRx"),
            ("Remo T", "https://exrx.net/WeightExercises/BackGeneral/BPTBarRow", "ExRx"),
            ("Remo invertido", "https://exrx.net/WeightExercises/TrapeziusMiddle/BBInvertedRow", "ExRx"),
            ("Buenos días", "https://exrx.net/WeightExercises/ErectorSpinae/BBGoodMorning", "ExRx")
        ],
        "mancuernas": [
            ("Remo con mancuernas", "https://exrx.net/WeightExercises/BackGeneral/DBBentOverRow", "ExRx"),
            ("Remo unilateral", "https://exrx.net/WeightExercises/BackGeneral/DBOneArmRow", "ExRx"),
            ("Pull-over con mancuerna", "https://exrx.net/WeightExercises/LatissimusDorsi/DBPullover", "ExRx"),
            ("Dominadas asistidas", "https://exrx.net/WeightExercises/LatissimusDorsi/ASPullup", "ExRx"),
            ("Jalón polea agarre neutro", "https://exrx.net/WeightExercises/LatissimusDorsi/CBNeutralGripPulldown", "ExRx"),
            ("Remo pecho apoyado", "https://exrx.net/WeightExercises/BackGeneral/DBChestSupportedRow", "ExRx"),
            ("Face pull", "https://exrx.net/WeightExercises/DeltoidPosterior/CBFacePull", "ExRx"),
            ("Remo en máquina", "https://exrx.net/WeightExercises/BackGeneral/LVSeatedRow", "ExRx")
        ]
    },
    "piernas": {
        "barra": [
            ("Sentadilla trasera", "https://exrx.net/WeightExercises/Quadriceps/BBSquat", "ExRx"),
            ("Sentadilla frontal", "https://exrx.net/WeightExercises/Quadriceps/BBFrontSquat", "ExRx"),
            ("Peso muerto rumano", "https://exrx.net/WeightExercises/Hamstrings/BBRomanianDeadlift", "ExRx"),
            ("Zancadas con barra", "https://exrx.net/WeightExercises/Quadriceps/BBLunge", "ExRx"),
            ("Buenos días", "https://exrx.net/WeightExercises/ErectorSpinae/BBGoodMorning", "ExRx"),
            ("Hip thrust con barra", "https://exrx.net/WeightExercises/GluteusMaximus/BBHipThrust", "ExRx"),
            ("Sentadilla con pausa", "https://exrx.net/ExInfo/TempoTraining", "ExRx"),
            ("Sentadilla a caja", "https://exrx.net/WeightExercises/Quadriceps/BBBoxSquat", "ExRx")
        ],
        "mancuernas": [
            ("Sentadilla goblet", "https://exrx.net/WeightExercises/Quadriceps/DBGobletSquat", "ExRx"),
            ("Zancadas caminando", "https://exrx.net/WeightExercises/Quadriceps/DBLunge", "ExRx"),
            ("Peso muerto a una pierna", "https://exrx.net/WeightExercises/Hamstrings/DBSingleLegDeadlift", "ExRx"),
            ("Step-up", "https://exrx.net/WeightExercises/Quadriceps/DBStepUp", "ExRx"),
            ("Elevación de talones", "https://exrx.net/WeightExercises/Gastrocnemius/BBCalfRaise", "ExRx"),
            ("Sentadilla búlgara", "https://exrx.net/WeightExercises/Quadriceps/DBBulgarianSplitSquat", "ExRx"),
            ("Hip thrust mancuerna", "https://exrx.net/WeightExercises/GluteusMaximus/DBHipThrust", "ExRx"),
            ("Sissy squat asistida", "https://exrx.net/WeightExercises/Quadriceps/BWSissySquat", "ExRx")
        ]
    },
    "hombros": {
        "mancuernas": [
            ("Press militar mancuernas", "https://exrx.net/WeightExercises/DeltoidAnterior/DBShoulderPress", "ExRx"),
            ("Elevaciones laterales", "https://exrx.net/WeightExercises/DeltoidLateral/DBLateralRaise", "ExRx"),
            ("Pájaros (deltoide posterior)", "https://exrx.net/WeightExercises/DeltoidPosterior/DBRearDeltRaise", "ExRx"),
            ("Press Arnold", "https://exrx.net/WeightExercises/DeltoidAnterior/DBArnoldPress", "ExRx"),
            ("Elevación frontal", "https://exrx.net/WeightExercises/DeltoidAnterior/DBFrontRaise", "ExRx"),
            ("Remo al mentón moderado", "https://exrx.net/WeightExercises/TrapeziusUpper/BBUprightRow", "ExRx"),
            ("Face pull", "https://exrx.net/WeightExercises/DeltoidPosterior/CBFacePull", "ExRx"),
            ("Press en máquina", "https://exrx.net/WeightExercises/DeltoidAnterior/LVShoulderPress", "ExRx")
        ]
    },
    "brazos": {
        "mancuernas": [
            ("Curl alterno", "https://exrx.net/WeightExercises/Biceps/DBCurl", "ExRx"),
            ("Curl martillo", "https://exrx.net/WeightExercises/Brachioradialis/DBHammerCurl", "ExRx"),
            ("Curl inclinado", "https://exrx.net/WeightExercises/Biceps/DBInclineCurl", "ExRx"),
            ("Press francés mancuernas", "https://exrx.net/WeightExercises/Triceps/DBFrenchPress", "ExRx"),
            ("Extensión tríceps polea", "https://exrx.net/WeightExercises/Triceps/CBPushdown", "ExRx"),
            ("Copa tríceps", "https://exrx.net/WeightExercises/Triceps/DBOneArmOverheadExtension", "ExRx"),
            ("Curl barra Z", "https://exrx.net/WeightExercises/Biceps/BBCurl", "ExRx"),
            ("Fondos entre bancos", "https://exrx.net/WeightExercises/Triceps/BWBenchDip", "ExRx")
        ],
        "peso_corporal": [
            ("Flexiones diamante", "https://exrx.net/WeightExercises/Triceps/BWCloseTricepsPushup", "ExRx"),
            ("Fondos en paralelas", "https://exrx.net/WeightExercises/Triceps/ASDip", "ExRx"),
            ("Flexiones cerradas", "https://exrx.net/WeightExercises/Triceps/BWCloseTricepsPushup", "ExRx"),
            ("Isométrico bíceps con toalla", "https://exrx.net/ExInfo/Isometric", "ExRx"),
            ("Extensión tríceps banco", "https://exrx.net/WeightExercises/Triceps/BWBenchDip", "ExRx"),
            ("Curl con banda elástica", "https://exrx.net/WeightExercises/Biceps/CBBandCurl", "ExRx"),
            ("Press cerrado", "https://exrx.net/WeightExercises/Triceps/BBCloseGripBenchPress", "ExRx"),
            ("Flexiones tempo 3-1-1", "https://exrx.net/ExInfo/TempoTraining", "ExRx")
        ]
    },
    "core": {
        "peso_corporal": [
            ("Plancha", "https://exrx.net/WeightExercises/RectusAbdominis/BWPlank", "ExRx"),
            ("Crunch", "https://exrx.net/WeightExercises/RectusAbdominis/BWCrunch", "ExRx"),
            ("Elevación de piernas", "https://exrx.net/WeightExercises/RectusAbdominis/BWLegRaiseBentKnee", "ExRx"),
            ("Dead bug", "https://exrx.net/WeightExercises/TransverseAbdominis/BWDeadBug", "ExRx"),
            ("Pallof press (banda)", "https://exrx.net/WeightExercises/Obliques/CBBandPallofPress", "ExRx"),
            ("Plancha lateral", "https://exrx.net/WeightExercises/Obliques/BWSidePlank", "ExRx"),
            ("Mountain climbers", "https://exrx.net/WeightExercises/RectusAbdominis/BWMountainClimber", "ExRx"),
            ("Hollow hold", "https://exrx.net/WeightExercises/RectusAbdominis/BWHollowBodyHold", "ExRx")
        ]
    },
    "fullbody": {
        "mancuernas": [
            ("Sentadilla goblet", "https://exrx.net/WeightExercises/Quadriceps/DBGobletSquat", "ExRx"),
            ("Press banca mancuernas", "https://exrx.net/WeightExercises/PectoralSternal/DBBenchPress", "ExRx"),
            ("Remo con mancuernas", "https://exrx.net/WeightExercises/BackGeneral/DBBentOverRow", "ExRx"),
            ("Peso muerto rumano", "https://exrx.net/WeightExercises/Hamstrings/DBRomanianDeadlift", "ExRx"),
            ("Press militar DB", "https://exrx.net/WeightExercises/DeltoidAnterior/DBShoulderPress", "ExRx"),
            ("Zancadas", "https://exrx.net/WeightExercises/Quadriceps/DBLunge", "ExRx"),
            ("Face pull", "https://exrx.net/WeightExercises/DeltoidPosterior/CBFacePull", "ExRx"),
            ("Elevación de talones", "https://exrx.net/WeightExercises/Gastrocnemius/BBCalfRaise", "ExRx")
        ]
    },
    "cardio": {
    "peso_corporal": [
        ("Saltar la cuerda (básico)", "https://exrx.net/Aerobic/Exercises/JumpRopeSingleHop", "ExRx"),
        ("Saltar la cuerda (dobles)", "https://exrx.net/Aerobic/Exercises/JumpRopeDoubleRotation", "ExRx"),
        ("Burpees", "https://exrx.net/Aerobic/Exercises/Burpee", "ExRx"),
        ("Jumping jacks", "https://exrx.net/Aerobic/Exercises/JumpingJack", "ExRx"),
        ("Mountain climbers", "https://exrx.net/Aerobic/Exercises/MountainClimber", "ExRx"),
        ("Rodillas altas (high knees)", "https://exrx.net/Aerobic/Exercises/HighKneeRun", "ExRx"),
        ("Saltos laterales (skater)", "https://exrx.net/Plyometrics/MBLateralBound", "ExRx"),
        ("Shadow boxing (rounds)", "https://www.youtube.com/watch?v=J4j3AOVWuHE", "Tony Jeffries (YouTube)")
    ],
    "máquinas": [
        ("Cinta de correr: entrenos clave (intervalos/cuestas)", "https://www.youtube.com/watch?v=kvITDpAfJxg", "The Running Channel (YouTube)"),
        ("Cinta de correr: 20 min principiantes (intervalos guiados)", "https://www.youtube.com/watch?v=ufhM_9eLU-s", "Sam Candler (YouTube)"),
        ("Bicicleta estática: 20 min intervalos principiantes", "https://www.youtube.com/watch?v=KTQGbk8_2DM", "Sunny Health & Fitness (YouTube)"),
        ("Bicicleta estática: HIIT 15 min principiantes", "https://www.youtube.com/watch?v=GzEpFWfFWiQ", "Kaleigh Cohen Fitness (YouTube)"),
        ("Elíptica: cómo usarla (técnica)", "https://www.youtube.com/watch?v=yISC2qwdh9I", "Nuffield Health (YouTube)"),
        ("Elíptica: intervalos 10 min principiantes", "https://www.youtube.com/watch?v=t9KVWTROVb0", "Sunny Health & Fitness (YouTube)"),
        ("Remo indoor: técnica correcta", "https://www.concept2.com/training/rowing-technique", "Concept2"),
        ("Stair climber: guía para principiantes", "https://www.youtube.com/watch?v=SZU9Rm0sNOo", "Calvin The Alchemist (YouTube)")
    ]
},

}

# Esquemas de series/reps/RPE por objetivo-nivel
SCHEMES: Dict[str, Dict[str, Dict[str, Any]]] = {
    "fuerza": {
        "principiante": {"series": (3, 4), "reps": (4, 6), "rires": "RIR 2", "rpe": "RPE 8"},
        "intermedio":   {"series": (4, 5), "reps": (3, 5), "rires": "RIR 1–2", "rpe": "RPE 8–9"},
        "avanzado":     {"series": (5, 6), "reps": (2, 4), "rires": "RIR 0–1", "rpe": "RPE 9–9.5"}
    },
    "hipertrofia": {
        "principiante": {"series": (3, 4), "reps": (8, 12), "rires": "RIR 2", "rpe": "RPE 7–8"},
        "intermedio":   {"series": (3, 5), "reps": (6, 12), "rires": "RIR 1–2", "rpe": "RPE 7–9"},
        "avanzado":     {"series": (4, 6), "reps": (6, 10), "rires": "RIR 0–1", "rpe": "RPE 8–9"}
    },
    "bajar_grasa": {
        "principiante": {"series": (3, 4), "reps": (10, 15), "rires": "RIR 2–3", "rpe": "RPE 6–7"},
        "intermedio":   {"series": (3, 4), "reps": (12, 15), "rires": "RIR 2–3", "rpe": "RPE 6–7"}
    },
    "resistencia": {
        "principiante": {"series": (3, 4), "reps": (12, 20), "rires": "RIR 2–3", "rpe": "RPE 6–7"},
        "intermedio":   {"series": (3, 4), "reps": (12, 20), "rires": "RIR 2–3", "rpe": "RPE 6–7"}
    }
}

# =========================================================
# Banco de ejercicios y selección
# =========================================================
def _build_bank_por_prioridad(grupo: str, equip: str) -> List[Tuple[str, str]]:
    """
    Construye un pool de ejercicios (nombre, url) según prioridad:
    1) grupo + equip
    2) grupo + cualquier equip disponible
    3) fallback: fullbody + mancuernas
    """
    g = (grupo or "").strip().lower()
    e = _equip_key_norm(equip)

    pool: List[Tuple[str, str]] = []

    # 1) grupo + equip
    if g in CATALOGO and e in CATALOGO[g]:
        pool += [(n, u) for (n, u, _src) in CATALOGO[g][e]]

    # 2) grupo + otros equip si 1) quedó corto
    if g in CATALOGO:
        for e2, lista in CATALOGO[g].items():
            if e2 == e:
                continue
            pool += [(n, u) for (n, u, _src) in lista]

    # 3) fallback adicional (se suma al final)
    if "fullbody" in CATALOGO and "mancuernas" in CATALOGO["fullbody"]:
        pool += [(n, u) for (n, u, _src) in CATALOGO["fullbody"]["mancuernas"]]

    # deduplicar por nombre
    seen = set()
    unique_pool: List[Tuple[str, str]] = []
    for n, u in pool:
        if n not in seen:
            seen.add(n)
            unique_pool.append((n, u))
    return unique_pool

def pick_exercises(grupo: str, equip: str, n: int) -> List[Tuple[str, str]]:
    """Devuelve n ejercicios (nombre, url) priorizando el banco más relevante, sin duplicados."""
    pool = _build_bank_por_prioridad(grupo, equip)
    if not pool:
        return []
    random.shuffle(pool)
    return pool[:max(0, n)]

# =========================================================
# “BD” en memoria (demo) para reservas
# =========================================================
RESERVAS: List[Dict[str, Any]] = []

def _fecha_es_pasada(iso_yyyy_mm_dd: str) -> bool:
    try:
        d = datetime.fromisoformat(iso_yyyy_mm_dd).date()
        return d < date.today()
    except Exception:
        return False

# =========================================================
# VALIDATOR del FORM rutina_form (evita loops y normaliza)
# =========================================================
class ValidateRutinaForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_rutina_form"

    def _norm_text(self, x: Any) -> Text:
        return (str(x or "")).strip().lower()

    def validate_equipamiento(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        v = self._norm_text(value)
        normalizaciones = {
            "nada": "peso corporal",
            "sin equipo": "peso corporal",
            "sin equipamiento": "peso corporal",
            "cuerpo libre": "peso corporal",
            "peso_corporal": "peso corporal",
            "maquinas": "máquinas",
        }
        v = normalizaciones.get(v, v)
        permitidos = {"barra", "mancuernas", "polea", "máquinas", "maquinas", "peso corporal"}
        if v in permitidos:
            if v == "maquinas":
                v = "máquinas"
            return {"equipamiento": v}
        # heurística débil
        for k in permitidos:
            if k in v:
                return {"equipamiento": "máquinas" if k in {"maquinas", "máquinas"} else k}
        dispatcher.utter_message(text="No reconocí el equipamiento. Opciones: barra, mancuernas, polea, máquinas, peso corporal.")
        return {"equipamiento": None}

    def validate_ejercicios_num(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        v = self._norm_text(value)
        palabra_a_int = {"seis": 6, "siete": 7, "ocho": 8, "6": 6, "7": 7, "8": 8}
        if v in palabra_a_int:
            n = palabra_a_int[v]
        else:
            try:
                n = int(v)
            except Exception:
                dispatcher.utter_message(text="Indícame un número entre 6 y 8 (por ejemplo: 6, 7 u 8).")
                return {"ejercicios_num": None}
        if n < 6 or n > 8:
            dispatcher.utter_message(text="El número de ejercicios debe ser entre 6 y 8. ¿Probamos con 6, 7 u 8?")
            return {"ejercicios_num": None}
        return {"ejercicios_num": float(n)}

    def validate_musculo(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        v = self._norm_text(value)
        if not v:
            return {"musculo": None}
        v = v.replace(" y ", ", ").replace("/", ", ").replace("  ", " ")
        catalogo = {"pecho", "espalda", "piernas", "hombros", "brazos", "core", "fullbody", "cardio"}
        elegidos = [t.strip() for t in v.split(",") if t.strip()]
        if all(t in catalogo for t in elegidos):
            return {"musculo": ", ".join(elegidos)}
        for t in elegidos:
            if t not in catalogo:
                dispatcher.utter_message(text=f"No reconocí el grupo '{t}'. Usa: pecho, espalda, piernas, hombros, brazos, core, fullbody, cardio.")
                return {"musculo": None}
        return {"musculo": v}

# =========================================================
# ACCIÓN: Generar rutina completa
# =========================================================
class ActionGenerarRutina(Action):
    def name(self) -> Text:
        return "action_generar_rutina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        musculo  = (_slot(tracker, "musculo") or "brazos").lower()
        nivel    = (_slot(tracker, "nivel") or "intermedio").lower()
        objetivo = (_slot(tracker, "objetivo") or "fuerza").lower()
        equip    = (_slot(tracker, "equipamiento") or "mancuernas").lower()

        ejercicios_num = _safe_int(_slot(tracker, "ejercicios_num"), default=7, min_v=4, max_v=12)
        tiempo         = _safe_int(_slot(tracker, "tiempo_disponible"), default=45, min_v=15, max_v=120)

        plan = SCHEMES.get(objetivo, {}).get(nivel) or SCHEMES.get("fuerza", {}).get("intermedio")
        s_min, s_max = plan["series"]
        r_min, r_max = plan["reps"]
        rpe_text = plan["rpe"]
        rir_text = plan["rires"]

        ejercicios = pick_exercises(musculo, equip, ejercicios_num)

        fallback_notice = ""
        if not ejercicios:
            ejercicios = pick_exercises("fullbody", "mancuernas", ejercicios_num)
            fallback_notice = " (fallback a Fullbody por catálogo no disponible)"

        structured_ejercicios: List[Dict[str, Any]] = []
        bloques: List[str] = []
        for i, (nombre, url) in enumerate(ejercicios, start=1):
            bloques.append(
                f"{i}. {nombre} · {s_min}-{s_max} x {r_min}-{r_max} · {rpe_text} · {rir_text} · Video: {url}"
            )
            structured_ejercicios.append({
                "orden": i,
                "nombre": nombre,
                "video": url,
                "series": f"{s_min}-{s_max}",
                "repeticiones": f"{r_min}-{r_max}",
                "rpe": rpe_text,
                "rir": rir_text
            })

        routine_id = f"rutina-{int(datetime.now().timestamp())}"

        header = (
            f"Rutina · {musculo.capitalize()} · {nivel} · objetivo {objetivo}{fallback_notice}\n"
            f"Sesión ~{tiempo} min · {ejercicios_num} ejercicios · Equipo: {equip}\n"
            f"Progresión: +2.5-5% carga o +1 rep/serie manteniendo {rir_text}."
        )
        texto = header + ("\n\n" + "\n".join(bloques) if bloques else "\n\n(No se encontraron ejercicios en el catálogo).")

        dispatcher.utter_message(text=texto)

        dispatcher.utter_message(json_message={
            "type": "routine_detail",
            "routine_id": routine_id,
            "header": header.split("\n", 1)[0],
            "summary": {
                "tiempo_min": tiempo,
                "ejercicios": ejercicios_num,
                "equipamiento": equip,
                "objetivo": objetivo,
                "nivel": nivel,
                "musculo": musculo,
                "fallback": bool(fallback_notice.strip()),
                "progresion": f"+2.5-5% carga o +1 rep/serie manteniendo {rir_text}."
            },
            "fallback_notice": fallback_notice.strip() or None,
            "exercises": structured_ejercicios
        })
        return []

# =========================================================
# ACCIÓN: Sugerir rutina (breve)
# =========================================================
class ActionSugerirRutina(Action):
    def name(self) -> Text:
        return "action_sugerir_rutina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        objetivo = (_slot(tracker, "objetivo") or "hipertrofia").lower()
        musculo  = (_slot(tracker, "musculo")  or "fullbody").lower()
        nivel    = (_slot(tracker, "nivel")    or "principiante").lower()
        equip    = (_slot(tracker, "equipamiento") or "mancuernas").lower()

        ejercicios = pick_exercises(musculo, equip, 6)
        if not ejercicios:
            ejercicios = pick_exercises("fullbody", "mancuernas", 6)
            header = f"Rutina sugerida ▶ {musculo.title()} · objetivo: {objetivo} · nivel: {nivel} (fallback)"
        else:
            header = f"Rutina sugerida ▶ {musculo.title()} · objetivo: {objetivo} · nivel: {nivel}"

        tip = OBJECTIVE_TIPS.get(objetivo, "Ajusta volumen e intensidad según tolerancia.")

        texto = header + "\n" + "\n".join([f"- {nombre} (video: {url})" for (nombre, url) in ejercicios]) + f"\n\nNotas: {tip}"
        dispatcher.utter_message(text=texto)
        return []

# =========================================================
# ACCIÓN: Resumen rutina (cierre del form con enlace a front)
# =========================================================
class ActionResumenRutina(Action):
    def name(self) -> Text:
        return "action_resumen_rutina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        objetivo = _slot(tracker, "objetivo") or "general"
        musculo  = _slot(tracker, "musculo")  or "fullbody"
        nivel    = _slot(tracker, "nivel")    or "principiante"

        routine_id = f"{musculo}-{nivel}-{int(datetime.now().timestamp())}"

        FRONTEND_BASE = os.getenv("FRONTEND_BASE", "http://localhost:3000").rstrip("/")
        url = f"{FRONTEND_BASE}/rutina/{routine_id}"

        dispatcher.utter_message(
            text=f"Rutina generada ▶ {musculo.title()} · nivel {nivel}. Objetivo: {objetivo}. ¿Cómo deseas verla?"
        )
        dispatcher.utter_message(json_message={
            "type": "routine_link",
            "title": "Abrir rutina en una nueva pestaña",
            "url": url,
            "routine": {
                "id": routine_id,
                "objetivo": objetivo,
                "musculo": musculo,
                "nivel": nivel
            }
        })
        return []

# =========================================================
# ACCIÓN: Consejo de nutrición (ligado a objetivo)
# =========================================================
class ActionConsejoNutricion(Action):
    def name(self) -> Text:
        return "action_consejo_nutricion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        objetivo = (_slot(tracker, "objetivo") or "general").lower()
        consejo = NUTRICION_TIPS.get(objetivo, "Prioriza proteína adecuada, vegetales, fibra y buena hidratación.")
        dispatcher.utter_message(text=f"Nutrición ▶ objetivo {objetivo}: {consejo}")
        return []

# =========================================================
# ACCIONES: Reservas (demo en memoria)
# =========================================================
RESERVAS: List[Dict[str, Any]] = []

class ActionCrearReserva(Action):
    def name(self) -> Text:
        return "action_crear_reserva"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        clase = _slot(tracker, "clase")
        fecha = _normaliza_fecha(_slot(tracker, "fecha"))
        hora  = _normaliza_hora(_slot(tracker, "hora"))

        if not (clase and fecha and hora):
            dispatcher.utter_message(text="Faltan datos para la reserva (clase/fecha/hora).")
            return []

        if isinstance(fecha, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", fecha) and _fecha_es_pasada(fecha):
            dispatcher.utter_message(text=f"La fecha {fecha} ya pasó. Elige otra, por favor.")
            return []

        reserva = {
            "user": tracker.sender_id,
            "clase": clase,
            "fecha": fecha,
            "hora": hora,
            "created_at": datetime.now().isoformat(timespec="seconds")
        }
        RESERVAS.append(reserva)
        dispatcher.utter_message(text=f"Reserva creada ✅: {clase} el {fecha} a las {hora} (demo).")
        return []

class ActionCancelarReserva(Action):
    def name(self) -> Text:
        return "action_cancelar_reserva"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        clase = _slot(tracker, "clase")
        fecha = _normaliza_fecha(_slot(tracker, "fecha"))
        hora  = _normaliza_hora(_slot(tracker, "hora"))

        global RESERVAS
        before = len(RESERVAS)

        if clase and fecha and hora:
            RESERVAS = [r for r in RESERVAS if not (
                r.get("user") == tracker.sender_id and r.get("clase") == clase and r.get("fecha") == fecha and r.get("hora") == hora
            )]
        else:
            for i, r in enumerate(list(RESERVAS)):
                if r.get("user") == tracker.sender_id:
                    RESERVAS.pop(i)
                    break

        after = len(RESERVAS)
        if after < before:
            dispatcher.utter_message(text="Reserva cancelada ✅ (demo).")
        else:
            dispatcher.utter_message(text="No encontré una reserva que coincida para cancelar (demo).")
        return []

class ActionConsultarReserva(Action):
    def name(self) -> Text:
        return "action_consultar_reserva"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user = tracker.sender_id
        user_reservas = [r for r in RESERVAS if r.get("user") == user]
        if not user_reservas:
            dispatcher.utter_message(text="No tienes reservas registradas (demo).")
            return []

        r = user_reservas[-1]
        dispatcher.utter_message(text=f"Tu reserva ▶ {r['clase']} el {r['fecha']} a las {r['hora']} (demo).")
        return []

# =========================================================
# ACCIÓN: Cambio de plan (flujo separado)
# =========================================================
class ActionSuscripcionCambioPlan(Action):
    def name(self) -> Text:
        return "action_suscripcion_cambio_plan"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text="¿A qué plan te gustaría cambiarte? (Mensual, Trimestral, Anual)")
        return []




