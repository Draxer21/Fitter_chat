"""Servicio de demo pública — sin autenticación, sin persistencia en BD.

Permite a visitantes sin cuenta probar FITTER con respuestas reales del planificador.
- Contexto en memoria (no se guarda en BD).
- Máx. MAX_TURNS mensajes por sesión.
- Después de CONTENT_TURNS respuestas con rutina/dieta inyecta CTA de registro.
- Detecta intención por palabras clave (no usa Rasa) para velocidad.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Dict, List, Optional

from ..planner import workouts as workout_planner
from ..planner import diets as diet_planner
from ..planner.common import parse_health_flags


# ── Límites ──────────────────────────────────────────────────────────────────
MAX_TURNS = 10          # máx. mensajes totales por sesión
CONTENT_TURNS = 2       # tras cuántas rutinas/dietas se inyecta el CTA
SESSION_TTL = 3600      # segundos que vive una sesión en memoria (1h)

CTA_MESSAGE = (
    "¿Te convenció FITTER? 🎯 Crea tu cuenta gratis en Rey Gym y:\n"
    "• Guarda esta rutina en tu perfil\n"
    "• Recibe planes personalizados con tu historial real\n"
    "• Accede a seguimiento de progreso y explicaciones XAI completas\n\n"
    "👉 **Crea tu cuenta gratis** — sin tarjeta de crédito, configurable en 2 minutos."
)

FAREWELL_MESSAGE = (
    "Has llegado al límite de la demo gratuita. "
    "Crea tu cuenta en Rey Gym para seguir usando FITTER sin restricciones 🚀"
)

# Palabras clave para detectar intent sin Rasa
_RUTINA_KW = re.compile(
    r"\b(rutina|ejercicio|entren|workout|gym|pesas|musculo|fuerza|"
    r"hipertrofia|cardio|bajar grasa|perder peso|ganar masa|serie|rep)\b",
    re.I,
)
_DIETA_KW = re.compile(
    r"\b(dieta|comer|alimenta|nutrici|menu|comida|proteina|carbohidrato|"
    r"cal[oó]ria|macros|peso|adelgazar|grasa|vegano|vegetariano)\b",
    re.I,
)
_SALUDO_KW = re.compile(
    r"^\s*(hola|buenas|hey|saludos|buen[oa]s?\s+(d[ií]as?|tardes?|noches?))\b",
    re.I,
)


# ── Contexto de sesión en memoria ─────────────────────────────────────────────
@dataclass
class DemoSession:
    session_id: str
    turns: int = 0                      # mensajes totales enviados
    content_turns: int = 0              # rutinas/dietas generadas
    cta_sent: bool = False
    created_at: float = field(default_factory=time.time)
    # Preferencias que el usuario va mencionando
    objetivo: str = "hipertrofia"
    nivel: str = "intermedio"
    musculo: str = "fullbody"
    condiciones: Optional[str] = None
    alergias: Optional[str] = None

    @property
    def expired(self) -> bool:
        return (time.time() - self.created_at) > SESSION_TTL

    @property
    def exhausted(self) -> bool:
        return self.turns >= MAX_TURNS


# ── Store de sesiones ──────────────────────────────────────────────────────────
class DemoSessionStore:
    def __init__(self) -> None:
        self._sessions: Dict[str, DemoSession] = {}
        self._lock = Lock()

    def get_or_create(self, session_id: str) -> DemoSession:
        with self._lock:
            sess = self._sessions.get(session_id)
            if sess is None or sess.expired:
                sess = DemoSession(session_id=session_id)
                self._sessions[session_id] = sess
            return sess

    def _prune(self) -> None:
        """Elimina sesiones expiradas para no acumular memoria."""
        with self._lock:
            expired = [k for k, v in self._sessions.items() if v.expired]
            for k in expired:
                del self._sessions[k]


# Instancia global (singleton por proceso)
_store = DemoSessionStore()


# ── Detección de intención ─────────────────────────────────────────────────────
def _detect_intent(message: str) -> str:
    if _SALUDO_KW.match(message):
        return "saludo"
    if _RUTINA_KW.search(message):
        return "rutina"
    if _DIETA_KW.search(message):
        return "dieta"
    return "otro"


def _extract_preferences(message: str, session: DemoSession) -> None:
    """Actualiza preferencias del usuario a partir del texto libre."""
    msg = message.lower()
    # Objetivo
    if any(k in msg for k in ("fuerza", "powerlifting", "levantar")):
        session.objetivo = "fuerza"
    elif any(k in msg for k in ("hipertrofia", "masa muscular", "musculo", "volumen")):
        session.objetivo = "hipertrofia"
    elif any(k in msg for k in ("bajar grasa", "perder grasa", "adelgazar", "definir", "quemar")):
        session.objetivo = "bajar_grasa"
    elif any(k in msg for k in ("resistencia", "cardio", "correr", "fondo")):
        session.objetivo = "resistencia"
    # Nivel
    if any(k in msg for k in ("principiante", "nunca he", "recien empiezo", "nuevo")):
        session.nivel = "principiante"
    elif any(k in msg for k in ("avanzado", "años entrenando", "experiencia")):
        session.nivel = "avanzado"
    elif any(k in msg for k in ("intermedio", "algo de experiencia")):
        session.nivel = "intermedio"
    # Músculo
    for grupo in ("pecho", "espalda", "piernas", "hombros", "brazos", "core", "fullbody", "cardio"):
        if grupo in msg:
            session.musculo = grupo
            break
    # Condiciones
    health_flags = parse_health_flags(msg)
    if health_flags:
        existing = session.condiciones or ""
        session.condiciones = (existing + " " + msg).strip()


# ── Respuestas del servicio ────────────────────────────────────────────────────
def _build_saludo_response() -> List[Dict[str, Any]]:
    return [{
        "text": (
            "¡Hola! Soy FITTER, tu entrenador virtual de Rey Gym 👋\n\n"
            "Estás en modo demo — puedes pedirme una **rutina** o un **plan de dieta** "
            "y te mostraré exactamente cómo funciona la IA con explicación detallada de cada decisión.\n\n"
            "¿Con qué empezamos? Puedes decirme por ejemplo:\n"
            "• *\"Quiero una rutina para ganar músculo\"*\n"
            "• *\"Dame una dieta para bajar grasa\"*"
        ),
        "custom": {"type": "demo_intro"},
    }]


def _build_otro_response(turns_left: int) -> List[Dict[str, Any]]:
    return [{
        "text": (
            f"En la demo puedo generarte una **rutina de entrenamiento** o un **plan de dieta** "
            f"con explicación XAI completa. Te quedan {turns_left} mensajes en esta sesión.\n\n"
            "Prueba decirme: *\"Quiero una rutina de pecho\"* o *\"Dame una dieta para bajar grasa\"*"
        ),
        "custom": {"type": "demo_hint"},
    }]


def _build_cta_message() -> Dict[str, Any]:
    return {
        "text": CTA_MESSAGE,
        "custom": {"type": "demo_cta"},
    }


# ── Función principal ──────────────────────────────────────────────────────────
def process_demo_message(
    session_id: str,
    message: str,
) -> Dict[str, Any]:
    """
    Procesa un mensaje de demo y devuelve una lista de respuestas.
    Retorna: {"responses": [...], "turns_left": int, "exhausted": bool}
    """
    session = _store.get_or_create(session_id)

    # Sesión agotada
    if session.exhausted:
        return {
            "responses": [{"text": FAREWELL_MESSAGE, "custom": {"type": "demo_farewell"}}],
            "turns_left": 0,
            "exhausted": True,
        }

    session.turns += 1
    _extract_preferences(message, session)
    intent = _detect_intent(message)
    responses: List[Dict[str, Any]] = []

    if intent == "saludo":
        responses = _build_saludo_response()

    elif intent == "rutina":
        try:
            payload = workout_planner.generate_workout_plan(
                objetivo=session.objetivo,
                nivel=session.nivel,
                musculo=session.musculo,
                equipamiento="mixto",
                ejercicios_num=5,
                tiempo_min=45,
                condiciones=session.condiciones,
                alergias=session.alergias,
            )
            routine_summary = payload.get("routine_summary") or {}
            explanation_dict = routine_summary.get("explanation") or {}

            from .orchestrator import format_explanation_block
            explanation_text = format_explanation_block(explanation_dict) if explanation_dict else None

            responses.append({
                "text": payload.get("text", "Aquí está tu rutina:"),
                "custom": {
                    **routine_summary,
                    "explanation_text": explanation_text,
                    "demo": True,
                },
            })
            session.content_turns += 1
        except Exception as exc:
            responses.append({"text": f"No pude generar la rutina: {exc}"})

    elif intent == "dieta":
        try:
            payload = diet_planner.generate_diet_plan(
                objetivo=session.objetivo,
                nivel=session.nivel,
                alergias=session.alergias or "",
                dislikes="",
                condiciones=session.condiciones or "",
            )
            diet_payload = payload.get("diet_payload") or payload
            explanation_dict = diet_payload.get("explanation") or {}

            from .orchestrator import format_explanation_block
            explanation_text = format_explanation_block(explanation_dict) if explanation_dict else None

            responses.append({
                "text": payload.get("text", "Aquí está tu plan de dieta:"),
                "custom": {
                    **diet_payload,
                    "explanation_text": explanation_text,
                    "demo": True,
                },
            })
            session.content_turns += 1
        except Exception as exc:
            responses.append({"text": f"No pude generar el plan de dieta: {exc}"})

    else:
        turns_left = MAX_TURNS - session.turns
        responses = _build_otro_response(turns_left)

    # Inyectar CTA tras CONTENT_TURNS respuestas de contenido
    if session.content_turns >= CONTENT_TURNS and not session.cta_sent:
        responses.append(_build_cta_message())
        session.cta_sent = True

    # Limpiar sesiones expiradas de vez en cuando
    if session.turns % 5 == 0:
        _store._prune()

    turns_left = max(0, MAX_TURNS - session.turns)
    return {
        "responses": responses,
        "turns_left": turns_left,
        "exhausted": session.exhausted,
    }
