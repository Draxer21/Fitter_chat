# actions/actions.py
from __future__ import annotations
from typing import Any, Text, Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
import os
import random
import re
import logging
from urllib.parse import quote

import requests

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction  # <- Validador de formularios
from rasa_sdk.events import SlotSet

logger = logging.getLogger(__name__)

# =========================================================
# Helpers
# =========================================================
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:5000").strip().rstrip("/")
CONTEXT_TIMEOUT = float(os.getenv("CHAT_CONTEXT_TIMEOUT", "4"))
CONTEXT_API_KEY = os.getenv("CHAT_CONTEXT_API_KEY", "").strip() or os.getenv("BACKEND_CONTEXT_KEY", "").strip()
REQUIRE_AUTH_FOR_ROUTINE = os.getenv("CHAT_REQUIRE_AUTH", "1").lower() not in {"0", "false", "no"}
NOTIFICATIONS_TIMEOUT = float(os.getenv("CHAT_NOTIFY_TIMEOUT", "6"))
EMAIL_ROUTINE_ENABLED = os.getenv("CHAT_EMAIL_ROUTINE", "1").lower() not in {"0", "false", "no"}
ROUTINE_EMAIL_SUBJECT = (os.getenv("CHAT_ROUTINE_EMAIL_SUBJECT", "Tu rutina diaria Fitter") or "Tu rutina diaria Fitter").strip()


def send_context_update(sender_id: str, payload: Dict[str, Any]) -> None:
    """Propaga información del usuario al backend para persistir contexto."""
    if not sender_id or not payload:
        return
    base = BACKEND_BASE_URL
    if not base:
        return
    url = f"{base.rstrip('/')}/chat/context/{sender_id}"
    try:
        requests.post(url, json=payload, timeout=CONTEXT_TIMEOUT)
    except Exception as exc:
        logger.warning("No se pudo actualizar contexto para %s: %s", sender_id, exc)


def fetch_chat_context(sender_id: str) -> Optional[Dict[str, Any]]:
    if not sender_id or not BACKEND_BASE_URL:
        return None
    safe_sender = quote(sender_id[:80])
    url = f"{BACKEND_BASE_URL.rstrip('/')}/chat/context/{safe_sender}"
    headers: Dict[str, str] = {}
    if CONTEXT_API_KEY:
        headers["X-Context-Key"] = CONTEXT_API_KEY
    try:
        resp = requests.get(url, headers=headers, timeout=CONTEXT_TIMEOUT)
    except requests.RequestException as exc:
        logger.warning("No se pudo obtener contexto para %s: %s", sender_id, exc)
        return None
    if resp.status_code != 200:
        return None
    try:
        payload = resp.json()
    except Exception:
        logger.warning("Respuesta invalida del backend al obtener contexto para %s", sender_id)
        return None
    return payload.get("context")


def ensure_authenticated_context(tracker: Tracker) -> Optional[Dict[str, Any]]:
    sender = (tracker.sender_id or "").strip()
    if not sender:
        return None
    ctx = fetch_chat_context(sender)
    if not ctx or not ctx.get("user_id"):
        return None
    return ctx


def maybe_send_routine_email(
    ctx: Optional[Dict[str, Any]],
    header_lines: List[str],
    exercises: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if not EMAIL_ROUTINE_ENABLED:
        return None
    if not ctx:
        return None
    user_id = ctx.get("user_id")
    if not user_id:
        return None
    if not BACKEND_BASE_URL:
        return None

    def _format_exercise(entry: Dict[str, Any]) -> str:
        nombre = entry.get("nombre") or entry.get("name") or "Ejercicio"
        series = entry.get("series") or "-"
        reps = entry.get("repeticiones") or entry.get("reps") or "-"
        rpe = entry.get("rpe") or "-"
        video = entry.get("video") or entry.get("link")
        base = f"{nombre} | {series} series x {reps} reps | RPE {rpe}"
        if video:
            return f"{base} | Video: {video}"
        return base

    body_lines: List[str] = []
    for line in header_lines:
        body_lines.append(line)
    body_lines.append("")
    body_lines.append("Detalle de ejercicios:")
    for entry in exercises:
        body_lines.append(f"- {_format_exercise(entry)}")
    body_lines.append("")
    body_lines.append("Recuerda calentar antes de iniciar y ajustar la intensidad según tu sensación.")

    payload = {
        "user_id": int(user_id),
        "body": "\n".join(body_lines).strip(),
        "subject": ROUTINE_EMAIL_SUBJECT,
    }
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if CONTEXT_API_KEY:
        headers["X-Context-Key"] = CONTEXT_API_KEY
    try:
        resp = requests.post(
            f"{BACKEND_BASE_URL.rstrip('/')}/notifications/daily-routine",
            json=payload,
            headers=headers,
            timeout=NOTIFICATIONS_TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.warning("No se pudo enviar rutina por correo para %s: %s", user_id, exc)
        return {"status": "network", "error": str(exc)}

    if resp.status_code in {401, 403}:
        logger.info("Envio de rutina por correo rechazado por auth (user_id=%s)", user_id)
        return {"status": "unauthorized"}
    if not resp.ok:
        logger.warning("Fallo al enviar rutina por correo (status=%s, body=%s)", resp.status_code, resp.text[:200])
        return {"status": "error", "error": resp.text}

    logger.info("Rutina enviada por correo a user_id=%s", user_id)
    return {"status": "ok"}


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
    return [
        item.strip()
        for item in re.split(r"[;,]", normalized)
        if item.strip()
    ]


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
        "intermedio":   {"series": (4, 5), "reps": (3, 5), "rires": "RIR 1-2", "rpe": "RPE 8-9"},
        "avanzado":     {"series": (5, 6), "reps": (2, 4), "rires": "RIR 0-1", "rpe": "RPE 9-9.5"}
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
        "intermedio":   {"series": (3, 4), "reps": (12, 20), "rires": "RIR 2-3", "rpe": "RPE 6-7"}
    }
}

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

    def _canonical_optional(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        original = str(value).strip()
        norm = self._norm_text(value)
        if not original:
            return "ninguna"
        if norm in {"ninguna", "ninguno", "ningunas", "ningunos", "no", "ningun problema"}:
            return "ninguna"
        return original

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

    def validate_condiciones_salud(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        limpio = self._canonical_optional(value)
        if limpio == "ninguna":
            return {"condiciones_salud": "ninguna"}
        if limpio is None:
            dispatcher.utter_message(text="Indicame si padeces alguna condicion (ej. hipertension, asma) o responde 'ninguna'.")
            return {"condiciones_salud": None}
        return {"condiciones_salud": limpio}

    def validate_alergias(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        limpio = self._canonical_optional(value)
        if limpio == "ninguna":
            return {"alergias": "ninguna"}
        if limpio is None:
            dispatcher.utter_message(text="Senalame alergias o intolerancias (ej. lactosa, gluten) o responde 'ninguna'.")
            return {"alergias": None}
        return {"alergias": limpio}

# =========================================================
# ACCIÓN: Generar rutina completa
# =========================================================
class ActionGenerarRutina(Action):
    def name(self) -> Text:
        return "action_generar_rutina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        ctx: Optional[Dict[str, Any]] = None
        if REQUIRE_AUTH_FOR_ROUTINE:
            ctx = ensure_authenticated_context(tracker)
            if ctx is None:
                dispatcher.utter_message(text="Necesitas iniciar sesión en Fitter antes de generar tu rutina. Inicia sesión y vuelve a intentarlo.")
                return []

        musculo = (_slot(tracker, "musculo") or "brazos").lower()
        nivel = (_slot(tracker, "nivel") or "intermedio").lower()
        objetivo = (_slot(tracker, "objetivo") or "fuerza").lower()
        equip = (_slot(tracker, "equipamiento") or "mancuernas").lower()

        condiciones = _slot(tracker, "condiciones_salud") or "ninguna"
        alergias = _slot(tracker, "alergias") or "ninguna"
        health_flags = parse_health_flags(condiciones)
        health_notes = build_health_notes(health_flags)
        allergy_list = parse_allergy_list(alergias)

        ejercicios_num = _safe_int(_slot(tracker, "ejercicios_num"), default=7, min_v=4, max_v=12)
        tiempo = _safe_int(_slot(tracker, "tiempo_disponible"), default=45, min_v=15, max_v=120)

        plan = SCHEMES.get(objetivo, {}).get(nivel) or SCHEMES.get("fuerza", {}).get("intermedio")
        s_min, s_max = plan["series"]
        r_min, r_max = plan["reps"]
        rpe_text = plan["rpe"]
        rir_text = plan["rires"]

        if health_flags.get("hipertension") or health_flags.get("cardiaco"):
            rpe_text = "RPE <= 7"
            rir_text = "RIR 2 (evita el fallo)"
            if "Manten intensidad moderada" not in health_notes:
                health_notes.append("Manten intensidad moderada (RPE <= 7).")
        if health_flags.get("diabetes") and "Revisa glucosa" not in health_notes:
            health_notes.append("Revisa glucosa antes y despues de entrenar.")

        ejercicios = pick_exercises(musculo, equip, ejercicios_num)

        fallback_notice = ""
        if not ejercicios:
            ejercicios = pick_exercises("fullbody", "mancuernas", ejercicios_num)
            fallback_notice = " (fallback a fullbody por catologo no disponible)"

        structured_ejercicios: List[Dict[str, Any]] = []
        bloques: List[str] = []
        for i, (nombre, url) in enumerate(ejercicios, start=1):
            bloques.append(
                f"{i}. {nombre} | {s_min}-{s_max} series x {r_min}-{r_max} reps | {rpe_text} | {rir_text} | Video: {url}"
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

        header_lines: List[str] = [
            f"Rutina - {musculo.title()} - nivel {nivel} - objetivo {objetivo}{fallback_notice}",
            f"Sesion aproximada {tiempo} min | {ejercicios_num} ejercicios | Equipo: {equip}",
            f"Progresion sugerida: +2.5-5% carga o +1 rep/serie manteniendo {rir_text}."
        ]
        if health_notes or allergy_list:
            extra_bits: List[str] = []
            if health_notes:
                extra_bits.append("; ".join(health_notes))
            if allergy_list:
                extra_bits.append("Alergias registradas: " + ", ".join(allergy_list))
            header_lines.append("Precaucion salud: " + " | ".join(extra_bits))
        header = "\n".join(header_lines)
        texto = header + ("\n\n" + "\n".join(bloques) if bloques else "\n\n(No se encontraron ejercicios en el catalogo.)")

        dispatcher.utter_message(text=texto)

        routine_summary = {
            "type": "routine_detail",
            "routine_id": routine_id,
            "header": header_lines[0],
            "summary": {
                "tiempo_min": tiempo,
                "ejercicios": ejercicios_num,
                "equipamiento": equip,
                "objetivo": objetivo,
                "nivel": nivel,
                "musculo": musculo,
                "fallback": bool(fallback_notice.strip()),
                "progresion": f"+2.5-5% carga o +1 rep/serie manteniendo {rir_text}.",
                "health_notes": health_notes or None,
                "allergies": allergy_list or None,
                "medical_conditions": condiciones if condiciones.lower() not in {"", "ninguna", "ninguno", "no"} else None,
            },
            "fallback_notice": fallback_notice.strip() or None,
            "exercises": structured_ejercicios
        }

        dispatcher.utter_message(json_message=routine_summary)

        email_status = maybe_send_routine_email(ctx, header_lines, structured_ejercicios)
        if email_status:
            status = email_status.get("status")
            if status == "ok":
                dispatcher.utter_message(text="También te envié esta rutina a tu correo registrado.")
            elif status == "unauthorized":
                dispatcher.utter_message(text="Tu sesión web expiró, por lo que no pude enviarte la rutina por correo. Inicia sesión nuevamente si deseas recibirla por email.")
            else:
                dispatcher.utter_message(text="No pude enviar la rutina por correo esta vez, pero aquí tienes todo el detalle para que lo sigas desde el chat.")

        context_payload: Dict[str, Any] = {}
        if condiciones and condiciones.lower() not in {"", "ninguna", "ninguno", "no"}:
            context_payload["medical_conditions"] = condiciones
        if alergias and alergias.lower() not in {"", "ninguna", "ninguno", "no"}:
            context_payload["allergies"] = alergias
        if context_payload:
            send_context_update(tracker.sender_id, context_payload)

        return [SlotSet("ultima_rutina", routine_summary)]

# =========================================================
# ACCION: Generar dieta complementaria
# =========================================================
class ActionGenerarDieta(Action):
    def name(self) -> Text:
        return "action_generar_dieta"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        objetivo = (_slot(tracker, "objetivo") or "equilibrada").lower()
        nivel = (_slot(tracker, "nivel") or "intermedio").lower()
        alergias = _slot(tracker, "alergias") or "ninguna"
        condiciones = _slot(tracker, "condiciones_salud") or "ninguna"

        plan = DIET_BASES.get(objetivo) or DIET_BASES.get("equilibrada")
        plan_label = objetivo if objetivo in DIET_BASES else "equilibrada"
        health_flags = parse_health_flags(condiciones)
        allergy_list = parse_allergy_list(alergias)

        adjustments: List[str] = []
        if health_flags.get("hipertension") or health_flags.get("cardiaco"):
            adjustments.append("Reduce sodio: condimenta con hierbas, evita embutidos y frituras.")
        if health_flags.get("diabetes"):
            adjustments.append("Distribuye carbohidratos complejos en porciones moderadas cada 3-4 horas.")
        if health_flags.get("asma"):
            adjustments.append("Incluye alimentos antiinflamatorios (omega 3, frutas variadas).")

        meals = plan.get("meals", [])
        filtered_meals: List[Dict[str, Any]] = []
        allergen_hits: List[Dict[str, Any]] = []
        for meal in meals:
            joined = " ".join(meal.get("items", [])).lower()
            if allergy_list and any(token in joined for token in allergy_list):
                allergen_hits.append({"meal": meal.get("name"), "items": meal.get("items", [])})
                continue
            filtered_meals.append(meal)

        if not filtered_meals:
            filtered_meals = meals

        if allergy_list and allergen_hits:
            adjustments.append("Reemplaza ingredientes en las comidas marcadas por alternativas seguras.")

        macros = plan.get("macros", {})
        hydration = plan.get("hydration")

        lines: List[str] = [
            f"Plan alimenticio sugerido para objetivo {plan_label} (nivel {nivel}).",
            f"Calorias estimadas: {plan.get('calorias', 'mantenimiento')}",
            "Macros orientativas:",
            f"- Proteinas: {macros.get('proteinas', '-')}",
            f"- Carbohidratos: {macros.get('carbohidratos', '-')}",
            f"- Grasas: {macros.get('grasas', '-')}",
        ]
        if adjustments:
            lines.append("Ajustes de salud:")
            for note in adjustments:
                lines.append(f"- {note}")
        if allergy_list and not allergen_hits:
            lines.append("Se han considerado tus alergias registradas.")
        if not allergy_list:
            lines.append("Si tienes alergias alimentarias, avisa para personalizar mas el plan.")

        lines.append("Menu diario ejemplo:")
        for meal in filtered_meals:
            items = ", ".join(meal.get("items", []))
            lines.append(f"- {meal.get('name', 'Comida')}: {items}")
            note = meal.get("notes")
            if note:
                lines.append(f"  Nota: {note}")
        if hydration:
            lines.append(f"Hidratacion recomendada: {hydration}")

        text_response = "\n".join(lines)
        dispatcher.utter_message(text=text_response)

        diet_payload = {
            "type": "diet_plan",
            "objective": plan_label,
            "summary": {
                "calorias": plan.get("calorias"),
                "macros": macros,
                "hydration": hydration,
                "health_adjustments": adjustments or None,
                "allergies": allergy_list or None,
                "medical_conditions": condiciones if condiciones.lower() not in {"", "ninguna", "ninguno", "no"} else None,
                "allergen_hits": allergen_hits or None,
            },
            "meals": filtered_meals,
        }

        dispatcher.utter_message(json_message=diet_payload)

        context_payload: Dict[str, Any] = {}
        if condiciones and condiciones.lower() not in {"", "ninguna", "ninguno", "no"}:
            context_payload["medical_conditions"] = condiciones
        if alergias and alergias.lower() not in {"", "ninguna", "ninguno", "no"}:
            context_payload["allergies"] = alergias
        if context_payload:
            send_context_update(tracker.sender_id, context_payload)

        return [SlotSet("ultima_dieta", diet_payload)]


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
        consejo = NUTRICION_TIPS.get(objetivo, "Prioriza proteina adecuada, vegetales, fibra y buena hidratacion.")
        alergias = _slot(tracker, "alergias") or ""
        condiciones = _slot(tracker, "condiciones_salud") or ""

        extras: List[str] = []
        if alergias and alergias.lower() not in {"", "ninguna", "ninguno", "no"}:
            extras.append(f"Evita ingredientes con: {alergias}.")
        flags = parse_health_flags(condiciones)
        if flags.get("hipertension") or flags.get("cardiaco"):
            extras.append("Usa poco sodio y elige grasas monoinsaturadas.")
        if flags.get("diabetes"):
            extras.append("Controla porciones de carbohidratos y prioriza fibra.")
        if flags.get("asma"):
            extras.append("Mantente hidratado y suma alimentos antiinflamatorios.")

        mensaje = f"Nutricion segun objetivo {objetivo}: {consejo}"
        if extras:
            mensaje += " Ajustes: " + " ".join(extras)
        dispatcher.utter_message(text=mensaje)

        context_payload: Dict[str, Any] = {}
        if alergias and alergias.lower() not in {"", "ninguna", "ninguno", "no"}:
            context_payload["allergies"] = alergias
        if condiciones and condiciones.lower() not in {"", "ninguna", "ninguno", "no"}:
            context_payload["medical_conditions"] = condiciones
        if context_payload:
            send_context_update(tracker.sender_id, context_payload)

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






