# actions/actions.py
from __future__ import annotations
from typing import Any, Text, Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
import time
import os
import random
import re
import logging
from urllib.parse import quote

import requests
from dotenv import load_dotenv
import threading

from backend.planner.common import build_health_notes, parse_allergy_list, parse_health_flags
from backend.planner.workouts import generate_workout_plan, pick_exercises
from backend.planner.diets import generate_diet_plan, calc_target_kcal_and_macros, DIET_BASES

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction  # <- Validador de formularios
from rasa_sdk.events import SlotSet, FollowupAction

logger = logging.getLogger(__name__)

# Optional local composer import (used when action server has access to backend package)
try:
    from backend.food.composer import compose_diet  # type: ignore
except Exception:
    compose_diet = None

# =========================================================
# Helpers
# =========================================================
# Carga el .env del proyecto para que el action server tenga las mismas variables
_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(_BASE_DIR, ".env"))
load_dotenv()  # fallback a variables del entorno del shell

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:5000").strip().rstrip("/")
CONTEXT_TIMEOUT = float(os.getenv("CHAT_CONTEXT_TIMEOUT", "4"))
CONTEXT_API_KEY = os.getenv("CHAT_CONTEXT_API_KEY", "").strip() or os.getenv("BACKEND_CONTEXT_KEY", "").strip()
REQUIRE_AUTH_FOR_ROUTINE = os.getenv("CHAT_REQUIRE_AUTH", "1").lower() not in {"0", "false", "no"}
NOTIFICATIONS_TIMEOUT = float(os.getenv("CHAT_NOTIFY_TIMEOUT", "6"))
EMAIL_ROUTINE_ENABLED = os.getenv("CHAT_EMAIL_ROUTINE", "1").lower() not in {"0", "false", "no"}
ROUTINE_EMAIL_SUBJECT = (os.getenv("CHAT_ROUTINE_EMAIL_SUBJECT", "Tu rutina diaria Fitter") or "Tu rutina diaria Fitter").strip()
PROFILE_UPDATE_PATH = "/profile/me"
CHAT_ENABLE_DIETA_CALC = os.getenv("CHAT_ENABLE_DIETA_CALC", "0").strip().lower() in {"1", "true", "yes"}
_RAW_DIETA_CALC_MODE = os.getenv("CHAT_DIETA_CALC_MODE", "").strip().lower()
if _RAW_DIETA_CALC_MODE in {"off", "auto", "on"}:
    CHAT_DIETA_CALC_MODE = _RAW_DIETA_CALC_MODE
else:
    # Backward compatible: if old flag enabled -> on, otherwise default to auto.
    CHAT_DIETA_CALC_MODE = "on" if CHAT_ENABLE_DIETA_CALC else "auto"
CHAT_DIET_CATALOG = os.getenv("CHAT_DIET_CATALOG", "0").strip() in {"1", "true", "yes"}
BACKEND_HEALTH_PATH = (os.getenv("BACKEND_HEALTH_PATH", "/health") or "/health").strip()
BACKEND_HEALTH_TIMEOUT = float(os.getenv("BACKEND_HEALTH_TIMEOUT", "0.8"))


def backend_health_status(
    *,
    sender_id: Optional[str] = None,
    intent: Optional[str] = None,
    demo_offline: Optional[bool] = None,
) -> Tuple[bool, float]:
    if not BACKEND_BASE_URL:
        return False, 0.0
    path = BACKEND_HEALTH_PATH if BACKEND_HEALTH_PATH.startswith("/") else f"/{BACKEND_HEALTH_PATH}"
    url = f"{BACKEND_BASE_URL.rstrip('/')}{path}"
    start = time.perf_counter()
    try:
        resp = requests.get(url, timeout=BACKEND_HEALTH_TIMEOUT)
    except Exception:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "healthcheck",
            extra={
                "sender": sender_id,
                "intent": intent,
                "demo_offline": demo_offline,
                "ok": False,
                "elapsed_ms": round(elapsed_ms, 1),
            },
        )
        return False, elapsed_ms
    elapsed_ms = (time.perf_counter() - start) * 1000
    ok = resp.status_code == 200
    logger.info(
        "healthcheck",
        extra={
            "sender": sender_id,
            "intent": intent,
            "demo_offline": demo_offline,
            "ok": ok,
            "elapsed_ms": round(elapsed_ms, 1),
        },
    )
    return ok, elapsed_ms


def backend_health_ok(
    *,
    sender_id: Optional[str] = None,
    intent: Optional[str] = None,
    demo_offline: Optional[bool] = None,
) -> bool:
    ok, _ = backend_health_status(sender_id=sender_id, intent=intent, demo_offline=demo_offline)
    return ok


def mark_offline(dispatcher: CollectingDispatcher, tracker: Tracker) -> List[Dict[Text, Any]]:
    logger.info(
        "served_offline_response",
        extra={
            "sender": tracker.sender_id,
            "intent": tracker.latest_message.get("intent", {}).get("name"),
            "demo_offline": tracker.get_slot("demo_offline"),
        },
    )
    events: List[Dict[Text, Any]] = [SlotSet("offline_mode", True), SlotSet("backend_down", True)]
    if not tracker.get_slot("offline_notified"):
        dispatcher.utter_message(response="utter_offline_intro")
        events.append(SlotSet("offline_notified", True))
    return events


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


def fetch_user_profile(ctx: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not ctx or not ctx.get("user_id") or not BACKEND_BASE_URL:
        return None
    user_id = ctx.get("user_id")
    headers: Dict[str, str] = {"Accept": "application/json"}
    if CONTEXT_API_KEY:
        headers["X-Context-Key"] = CONTEXT_API_KEY
    try:
        resp = requests.get(
            f"{BACKEND_BASE_URL.rstrip('/')}" + "/profile/me",
            params={"user_id": user_id},
            headers=headers,
            timeout=CONTEXT_TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.warning("No se pudo obtener perfil para user_id=%s: %s", user_id, exc)
        return None
    if resp.status_code != 200:
        logger.debug("Perfil no disponible para user_id=%s (status=%s)", user_id, resp.status_code)
        return None
    try:
        payload = resp.json()
    except Exception:
        logger.warning("Respuesta invalida del backend al obtener perfil (user_id=%s)", user_id)
        return None
    profile = payload.get("profile") if isinstance(payload, dict) else None
    if profile and profile.get("weight_kg") is not None:
        try:
            profile["weight_kg"] = float(profile["weight_kg"])
        except (TypeError, ValueError):
            pass
    if profile and profile.get("height_cm") is not None:
        try:
            profile["height_cm"] = float(profile["height_cm"])
        except (TypeError, ValueError):
            pass
    return profile


def save_hero_plan(ctx: Optional[Dict[str, Any]], payload: Dict[str, Any]) -> bool:
    if not ctx or not ctx.get("user_id") or not BACKEND_BASE_URL:
        return False
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if CONTEXT_API_KEY:
        headers["X-Context-Key"] = CONTEXT_API_KEY
    body = {
        "user_id": ctx.get("user_id"),
        "plan_key": payload.get("plan_key"),
        "title": payload.get("title"),
        "payload": payload,
        "source": "chat",
    }
    try:
        resp = requests.post(
            f"{BACKEND_BASE_URL.rstrip('/')}/profile/hero-plans",
            json=body,
            headers=headers,
            timeout=CONTEXT_TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.warning("No se pudo guardar el entreno unico: %s", exc)
        return False
    return resp.status_code in {200, 201}


def persist_plan(
    ctx: Optional[Dict[str, Any]],
    *,
    path: str,
    payload: Dict[str, Any],
) -> Optional[str]:
    if not ctx or not ctx.get("user_id") or not BACKEND_BASE_URL:
        return None
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if CONTEXT_API_KEY:
        headers["X-Context-Key"] = CONTEXT_API_KEY
    body = {"user_id": ctx.get("user_id"), **payload}
    try:
        resp = requests.post(
            f"{BACKEND_BASE_URL.rstrip('/')}{path}",
            json=body,
            headers=headers,
            timeout=CONTEXT_TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.warning("No se pudo guardar plan en %s: %s", path, exc)
        return None
    if resp.status_code not in {200, 201}:
        logger.warning("Persistencia plan fallida %s (status=%s)", path, resp.status_code)
        return None
    try:
        data = resp.json()
    except Exception:
        return None
    plan_id = data.get("id") if isinstance(data, dict) else None
    return str(plan_id) if plan_id else None


def infer_training_level(profile: Optional[Dict[str, Any]]) -> Optional[str]:
    """Determina el nivel de entrenamiento usando experiencia declarada o actividad."""
    if not profile:
        return None

    principiante = {"principiante", "beginner", "novato", "novata", "suave", "ligero", "ligera", "sedentario", "sedentaria", "descarga"}
    intermedio = {"intermedio", "intermedia", "moderado", "moderada", "progresivo"}
    avanzado = {"avanzado", "avanzada", "advanced", "explosivo", "desafiante", "atleta", "intenso", "intensa"}

    def _map_level(value: str) -> Optional[str]:
        if not value:
            return None
        if value in principiante:
            return "principiante"
        if value in intermedio:
            return "intermedio"
        if value in avanzado:
            return "avanzado"
        return None

    experience = str(profile.get("experience_level") or "").strip().lower()
    mapped = _map_level(experience)
    if mapped:
        return mapped

    activity = str(profile.get("activity_level") or "").strip().lower()
    return _map_level(activity)


def profile_is_complete(profile: Optional[Dict[str, Any]]) -> bool:
    if not profile:
        return False
    weight = profile.get("weight_kg")
    height = profile.get("height_cm")
    goal = profile.get("primary_goal")
    return weight not in {None, "", 0} and height not in {None, "", 0} and bool(goal)


def _to_float(value: Any) -> Optional[float]:
    if value in (None, "", 0):
        return None
    text = str(value).strip().replace(",", ".")
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _normalize_list_or_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, list):
        cleaned = [str(item).strip() for item in value if str(item).strip()]
        return ", ".join(cleaned) if cleaned else None
    text = str(value).strip()
    return text or None


def build_profile_summary(profile: Optional[Dict[str, Any]]) -> str:
    if not profile:
        return "No encontre datos registrados en tu perfil."
    bits: List[str] = []
    weight = _to_float(profile.get("weight_kg"))
    height = _to_float(profile.get("height_cm"))
    goal = profile.get("primary_goal")
    diet_pref = profile.get("diet_preference")
    medical = _normalize_list_or_text(profile.get("medical_conditions"))
    somatotipo = _normalize_list_or_text(profile.get("somatotipo"))
    if weight:
        if weight.is_integer():
            bits.append(f"Peso: {int(weight)} kg")
        else:
            bits.append(f"Peso: {weight:.1f} kg")
    if height:
        if height.is_integer():
            bits.append(f"Altura: {int(height)} cm")
        else:
            bits.append(f"Altura: {height:.1f} cm")
    if goal:
        bits.append(f"Objetivo: {str(goal).replace('_', ' ')}")
    if diet_pref:
        bits.append(f"Dieta: {diet_pref}")
    if somatotipo:
        label = "no se" if somatotipo == "no_se" else somatotipo
        bits.append(f"Somatotipo: {label}")
    if medical:
        bits.append(f"Padecimientos: {medical}")
    if not bits:
        return "No hay datos cargados en tu perfil todavía."
    return "Datos actuales de tu perfil: " + " | ".join(bits)


class ValidateProfileForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_profile_form"

    def _validate_range(
        self,
        dispatcher: CollectingDispatcher,
        slot_name: Text,
        value: Any,
        min_v: float,
        max_v: float,
        units: Text,
    ) -> Dict[Text, Any]:
        number = _to_float(value)
        if number is None:
            dispatcher.utter_message(text=f"Necesito un valor numerico para {slot_name}.")
            return {slot_name: None}
        if not (min_v <= number <= max_v):
            dispatcher.utter_message(
                text=f"El valor de {slot_name} debe estar entre {min_v:g} y {max_v:g} {units}."
            )
            return {slot_name: None}
        rounded = round(number, 1)
        return {slot_name: rounded}

    def validate_peso(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        return self._validate_range(dispatcher, "peso", value, 35, 260, "kg")

    def validate_altura(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        return self._validate_range(dispatcher, "altura", value, 120, 230, "cm")

    def _normalize_optional(self, value: Any, default: Text = "") -> Text:
        text = (str(value or "")).strip()
        return text or default

    def validate_objetivo_fitness(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        raw = (str(value or "")).strip().lower()
        if not raw:
            dispatcher.utter_message(text="Necesito saber tu objetivo principal para ajustar las recomendaciones.")
            return {"objetivo_fitness": None}
        aliases = {
            "bajar grasa": {"bajar grasa", "definicion", "perder peso", "definir"},
            "ganar masa": {"ganar masa", "hipertrofia", "aumentar masa", "volumen"},
            "rendimiento": {"rendimiento", "resistencia", "deporte"},
            "salud general": {"salud general", "mantenerme", "bienestar", "salud"},
        }
        for canonical, synonym_set in aliases.items():
            if raw in synonym_set:
                return {"objetivo_fitness": canonical}
        return {"objetivo_fitness": raw}

    def validate_somatotipo(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        raw = (str(value or "")).strip().lower()
        if not raw:
            return {"somatotipo": "no_se"}
        cleaned = raw.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        cleaned = re.sub(r"\s+", " ", cleaned)
        if cleaned in {"no se", "no_se", "no estoy seguro", "no lo se", "ns", "nose"}:
            return {"somatotipo": "no_se"}
        if any(token in cleaned for token in {"ecto", "ectomorfo"}):
            return {"somatotipo": "ectomorfo"}
        if any(token in cleaned for token in {"meso", "mesomorfo"}):
            return {"somatotipo": "mesomorfo"}
        if any(token in cleaned for token in {"endo", "endomorfo"}):
            return {"somatotipo": "endomorfo"}
        if ("grasa" in cleaned or "retengo" in cleaned) and ("subo" in cleaned or "acumulo" in cleaned):
            return {"somatotipo": "endomorfo"}
        if ("peso" in cleaned or "masa" in cleaned) and ("cuesta" in cleaned or "dif" in cleaned):
            return {"somatotipo": "ectomorfo"}
        return {"somatotipo": cleaned}

    def validate_padecimientos(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        text = (str(value or "")).strip()
        if not text:
            dispatcher.utter_message(text="Indica si tienes algun padecimiento. Si no, escribe 'ninguno'.")
            return {"padecimientos": None}
        lowered = text.lower()
        if lowered in {"ninguno", "ninguna", "sin problemas", "no"}:
            return {"padecimientos": "ninguno"}
        return {"padecimientos": text}

    def validate_preferencia_dieta(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        text = (str(value or "")).strip()
        if not text:
            return {"preferencia_dieta": "ninguna"}
        lowered = text.lower()
        aliases = {
            "vegetariana": {"vegetariana", "vegetarian"},
            "vegana": {"vegana", "vegan"},
            "sin lactosa": {"sin lactosa", "lactosa", "intolerancia a la lactosa"},
            "sin gluten": {"sin gluten", "celiaco", "celiaca"},
            "ninguna": {"ninguna", "ninguno", "sin restriccion", "normal"},
        }
        for canonical, synonym_set in aliases.items():
            if lowered in synonym_set:
                return {"preferencia_dieta": canonical}
        return {"preferencia_dieta": text}

    def validate_musculo_preferido(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        opciones = {"pecho", "espalda", "piernas", "hombros", "brazos", "core", "fullbody", "cardio"}
        raw = (str(value or "")).strip().lower()
        if not raw:
            dispatcher.utter_message(text="Indica un grupo muscular de la lista o di 'ninguno'.")
            return {"musculo_preferido": None}
        if raw in {"ninguno", "ninguna", "no"}:
            return {"musculo_preferido": None}
        if raw not in opciones:
            dispatcher.utter_message(text="Solo puedo guardar pecho, espalda, piernas, hombros, brazos, core, fullbody o cardio.")
            return {"musculo_preferido": None}
        return {"musculo_preferido": raw}


class ActionFetchProfile(Action):
    def name(self) -> Text:
        return "action_fetch_profile"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        events: List[Dict[Text, Any]] = []
        active_loop = tracker.active_loop_name
        intent_name = tracker.latest_message.get("intent", {}).get("name")
        if not backend_health_ok(sender_id=tracker.sender_id, intent=intent_name, demo_offline=tracker.get_slot("demo_offline")):
            events.extend(mark_offline(dispatcher, tracker))
            events.append(SlotSet("resumen_perfil", "Modo offline: no pude acceder al perfil web."))
            events.append(SlotSet("perfil_completo", False))
            return events

        ctx = ensure_authenticated_context(tracker)
        if not ctx:
            dispatcher.utter_message(
                text="No pude validar tu sesion. Inicia sesion en la web y vuelve a intentarlo."
            )
            events.append(SlotSet("perfil_completo", False))
            return events

        try:
            profile = fetch_user_profile(ctx)
        except Exception as exc:
            logger.warning("No se pudo obtener el perfil: %s", exc)
            profile = None
        complete = profile_is_complete(profile)

        if profile:
            weight = _to_float(profile.get("weight_kg"))
            height = _to_float(profile.get("height_cm"))
            medical = _normalize_list_or_text(profile.get("medical_conditions"))
            diet_pref = _normalize_list_or_text(profile.get("diet_preference"))
            somatotipo = _normalize_list_or_text(profile.get("somatotipo"))
            goal = str(profile.get("primary_goal") or "").replace("_", " ").strip()
            if weight is not None:
                events.append(SlotSet("peso", weight))
            if height is not None:
                events.append(SlotSet("altura", height))
            if goal:
                events.append(SlotSet("objetivo_fitness", goal))
            if medical:
                events.append(SlotSet("padecimientos", medical))
            if diet_pref:
                events.append(SlotSet("preferencia_dieta", diet_pref))
            if somatotipo:
                events.append(SlotSet("somatotipo", somatotipo))
        else:
            profile = {}

        summary = build_profile_summary(profile if profile else None)
        events.append(SlotSet("resumen_perfil", summary))
        events.append(SlotSet("perfil_completo", complete))
        pending_service = tracker.get_slot("servicio_pendiente")
        if not pending_service:
            latest_intent = tracker.latest_message.get("intent", {}).get("name")
            if latest_intent == "solicitar_rutina":
                pending_service = "rutina"
                events.append(SlotSet("servicio_pendiente", "rutina"))
            elif latest_intent == "solicitar_dieta":
                pending_service = "dieta"
                events.append(SlotSet("servicio_pendiente", "dieta"))

        if not complete:
            if active_loop == "profile_form":
                return events
            return events

        return events


class ActionSubmitProfileForm(Action):
    def name(self) -> Text:
        return "action_submit_profile_form"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        intent_name = tracker.latest_message.get("intent", {}).get("name")
        if not backend_health_ok(sender_id=tracker.sender_id, intent=intent_name, demo_offline=tracker.get_slot("demo_offline")):
            events = mark_offline(dispatcher, tracker)
            dispatcher.utter_message(
                text="No pude guardar tu perfil porque el backend no está disponible. Puedo seguir con datos locales si quieres."
            )
            events.append(SlotSet("perfil_completo", False))
            return events
        ctx = ensure_authenticated_context(tracker)
        if not ctx:
            dispatcher.utter_message(
                text="Tu sesion web no esta activa. Inicia sesion y vuelve a actualizar el perfil."
            )
            return [SlotSet("perfil_completo", False)]

        weight = tracker.get_slot("peso")
        height = tracker.get_slot("altura")
        goal = tracker.get_slot("objetivo_fitness")
        medical = tracker.get_slot("padecimientos")
        diet_pref = tracker.get_slot("preferencia_dieta")
        preferred_muscle = tracker.get_slot("musculo_preferido")
        somatotipo = tracker.get_slot("somatotipo")

        payload = {
            "user_id": ctx.get("user_id"),
            "weight_kg": float(weight) if weight is not None else None,
            "height_cm": float(height) if height is not None else None,
            "primary_goal": (goal or "").strip() or None,
            "medical_conditions": None if (medical or "").lower() in {"", "ninguno"} else medical,
            "diet_preference": (diet_pref or "").strip() or None,
            "somatotipo": (somatotipo or "").strip() or None,
        }

        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if CONTEXT_API_KEY:
            headers["X-Context-Key"] = CONTEXT_API_KEY

        if not BACKEND_BASE_URL:
            dispatcher.utter_message(text="No encontre la configuracion del backend para guardar el perfil.")
            return []

        try:
            resp = requests.put(
                f"{BACKEND_BASE_URL.rstrip('/')}{PROFILE_UPDATE_PATH}",
                json=payload,
                headers=headers,
                timeout=CONTEXT_TIMEOUT,
            )
        except requests.RequestException as exc:
            logger.warning("No se pudo actualizar el perfil: %s", exc)
            dispatcher.utter_message(
                text="No pude actualizar tu perfil por un problema de red. Intentalo de nuevo en unos minutos."
            )
            return []

        if resp.status_code in {401, 403}:
            dispatcher.utter_message(text="Parece que tu sesion expiro. Inicia sesion otra vez para continuar.")
            return [SlotSet("perfil_completo", False)]

        if not resp.ok:
            logger.warning("Fallo al actualizar perfil (status=%s, body=%s)", resp.status_code, resp.text[:200])
            dispatcher.utter_message(
                text="El backend rechazo la actualizacion de perfil. Revisa los datos o intentalo mas tarde."
            )
            return []

        refreshed_profile: Optional[Dict[str, Any]] = None
        if resp.content:
            try:
                refreshed_profile = resp.json().get("profile")
            except Exception:
                logger.debug("No se pudo parsear la respuesta de perfil actualizada.")
        events: List[Dict[Text, Any]] = []
        if refreshed_profile:
            summary = build_profile_summary(refreshed_profile)
            events.append(SlotSet("resumen_perfil", summary))
            events.append(SlotSet("perfil_completo", profile_is_complete(refreshed_profile)))
            refreshed_weight = _to_float(refreshed_profile.get("weight_kg"))
            refreshed_height = _to_float(refreshed_profile.get("height_cm"))
            refreshed_goal = refreshed_profile.get("primary_goal")
            refreshed_medical = _normalize_list_or_text(refreshed_profile.get("medical_conditions"))
            refreshed_diet = _normalize_list_or_text(refreshed_profile.get("diet_preference"))
            refreshed_somatotipo = _normalize_list_or_text(refreshed_profile.get("somatotipo"))
            if refreshed_weight is not None:
                events.append(SlotSet("peso", refreshed_weight))
            if refreshed_height is not None:
                events.append(SlotSet("altura", refreshed_height))
            if refreshed_goal:
                events.append(SlotSet("objetivo_fitness", str(refreshed_goal).replace("_", " ").strip()))
            if refreshed_medical:
                events.append(SlotSet("padecimientos", refreshed_medical))
            if refreshed_diet:
                events.append(SlotSet("preferencia_dieta", refreshed_diet))
            if refreshed_somatotipo:
                events.append(SlotSet("somatotipo", refreshed_somatotipo))
        if preferred_muscle is not None:
            events.append(SlotSet("musculo_preferido", preferred_muscle))
        else:
            summary = build_profile_summary(payload)
            events.append(SlotSet("resumen_perfil", summary))
            events.append(SlotSet("perfil_completo", True))
            if payload["weight_kg"] is not None:
                events.append(SlotSet("peso", payload["weight_kg"]))
            if payload["height_cm"] is not None:
                events.append(SlotSet("altura", payload["height_cm"]))
            if payload["primary_goal"]:
                events.append(SlotSet("objetivo_fitness", payload["primary_goal"]))
            if payload["medical_conditions"]:
                events.append(SlotSet("padecimientos", payload["medical_conditions"]))
            if payload["diet_preference"]:
                events.append(SlotSet("preferencia_dieta", payload["diet_preference"]))
            if payload["somatotipo"]:
                events.append(SlotSet("somatotipo", payload["somatotipo"]))
        if preferred_muscle is not None:
            events.append(SlotSet("musculo_preferido", preferred_muscle))

        events.append(SlotSet("servicio_pendiente", None))

        return events


def maybe_send_routine_email(
    ctx: Optional[Dict[str, Any]],
    header_lines: Optional[List[str]] = None,
    exercises: Optional[List[Dict[str, Any]]] = None,
    routine_data: Optional[Dict[str, Any]] = None,
    attach: bool = False,
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
    if routine_data and isinstance(routine_data, dict):
        # build body from routine_data
        if routine_data.get("header"):
            body_lines.append(routine_data.get("header"))
        summary = routine_data.get("summary", {})
        body_lines.append("")
        body_lines.append("Detalle de ejercicios:")
        for entry in routine_data.get("exercises", []):
            body_lines.append(f"- {_format_exercise(entry)}")
        body_lines.append("")
        body_lines.append("Recuerda calentar antes de iniciar y ajustar la intensidad según tu sensación.")
    else:
        if header_lines:
            for line in header_lines:
                body_lines.append(line)
        body_lines.append("")
        body_lines.append("Detalle de ejercicios:")
        if exercises:
            for entry in exercises:
                body_lines.append(f"- {_format_exercise(entry)}")
        body_lines.append("")
        body_lines.append("Recuerda calentar antes de iniciar y ajustar la intensidad según tu sensación.")

    payload = {
        "user_id": int(user_id),
        "body": "\n".join(body_lines).strip(),
        "subject": ROUTINE_EMAIL_SUBJECT,
        "attach": bool(attach),
        "routine_data": routine_data if routine_data else None,
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


# =====================
# Dieta: cálculos opt-in
# =====================
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

SOMATOTIPO_TIPS_RUTINA: Dict[str, str] = {
    "ectomorfo": "Prioriza progresión de cargas y descanso suficiente; evita volumen excesivo.",
    "mesomorfo": "Responde bien a volumen moderado y variedad; mantén consistencia.",
    "endomorfo": "Combina fuerza con cardio moderado; controla descansos y volumen total.",
}

SOMATOTIPO_TIPS_DIETA: Dict[str, str] = {
    "ectomorfo": "Enfoca en energía y carbohidratos complejos; comidas frecuentes ayudan.",
    "mesomorfo": "Mantén balance estable de macros; prioriza calidad y timing.",
    "endomorfo": "Prioriza proteína/fibra y controla carbohidratos de alta carga.",
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

HERO_PROGRAMS: Dict[str, Dict[str, Any]] = {
    "shonen": {
        "title": "Shonen Power",
        "duration": "8 semanas",
        "focus": "Fuerza + hipertrofia con circuitos metabólicos",
        "body_type": "Atlético y veloz",
        "training": "4-5 sesiones por semana con bloques de potencia, sprints ligeros y trabajo de core avanzado.",
        "aliases": ["shonen power", "shonen"],
    },
    "ninja": {
        "title": "Ninja Agility",
        "duration": "6 semanas",
        "focus": "Movilidad, pliometría y acondicionamiento funcional",
        "body_type": "Ágil y definido",
        "training": "Sesiones cortas de alta frecuencia con énfasis en balance, saltos y control corporal.",
        "aliases": ["ninja agility", "ninja"],
    },
    "mecha": {
        "title": "Mecha Endurance",
        "duration": "10 semanas",
        "focus": "Resistencia progresiva y trabajo aeróbico estructurado",
        "body_type": "Robusto y resistente",
        "training": "Ciclos largos con cardio guiado, fuerza básica y sesiones de recuperación activa.",
        "aliases": ["mecha endurance", "mecha"],
    },
    "batman_bale": {
        "title": "Batman (Christian Bale)",
        "duration": "12 semanas",
        "focus": "Fuerza + volumen con base en compuestos y acondicionamiento",
        "body_type": "Atlético, hombros y espalda marcados",
        "training": "Compuestos tipo press banca, sentadilla, peso muerto y trabajo funcional, con artes marciales.",
        "diet": "Fase de aumento agresivo y luego dieta limpia hipercalorica con proteina magra y carbos complejos.",
        "calories": "No especificadas; aumento agresivo al inicio y luego hipercalorica limpia.",
        "macros": "No especificadas; prioridad a proteina magra y carbohidratos complejos.",
        "meals": [
            "Avena con batido de proteina",
            "Salmon con arroz y batata",
            "Pasta o pan integral con proteina magra",
            "Batido de proteina post-entreno",
        ],
        "sources": [
            "https://www.gq.com.mx/entretenimiento/articulo/christian-bale-rutinas-de-ejercicio-en-su-carrera",
            "https://steelsupplements.com/blogs/steel-blog/christian-bales-batman-workout-routine-and-diet-plan",
            "https://forums.superherohype.com/threads/bales-diet-and-training-for-bb.311673/",
        ],
        "aliases": ["batman bale", "batman christian bale", "christian bale", "batman"],
    },
    "batman_affleck": {
        "title": "Batman (Ben Affleck)",
        "duration": "12 semanas",
        "focus": "Hipertrofia con enfasis en fuerza maxima",
        "body_type": "Masivo y denso",
        "training": "5 sesiones/semana con cargas altas, bajo volumen de cardio y enfoque en espalda, pecho y hombro.",
        "diet": "Dieta six-pack, sin lacteos, 6 comidas diarias y control de sodio.",
        "calories": "3500-4000 kcal/dia",
        "macros": "Proteina alta, carbohidratos complejos moderados, grasas saludables; sodio 1500-2000 mg.",
        "meals": [
            "Claras con avena y banana",
            "Pechuga de pollo con camote",
            "Salmon con brocoli",
            "Batido de proteina con frutos secos",
        ],
        "sources": [
            "https://manofmany.com/culture/fitness/ben-affleck-batman-workout-diet-plan",
        ],
        "aliases": ["batman affleck", "batman ben affleck", "ben affleck"],
    },
    "batman_pattinson": {
        "title": "Batman (Robert Pattinson)",
        "duration": "8 semanas",
        "focus": "Fuerza relativa, movilidad y acondicionamiento funcional",
        "body_type": "Fibroso y agil",
        "training": "4 sesiones/semana con calistenia, circuitos y trabajo tipo box/HIIT.",
        "diet": "Mantenimiento o ligero deficit, proteina alta, carbos fibrosos y alcohol casi nulo.",
        "calories": "~2800 kcal/dia",
        "macros": "Proteina ~200-220 g/dia; carbos fibrosos; grasas moderadas.",
        "meals": [
            "Avena con huevo cocido, jugo de naranja y te verde",
            "Atun con tortitas de arroz y mantequilla de mani",
            "Pollo a la plancha con papa al horno pre-entreno",
            "Requeson con fruta",
            "Filete magro con arroz y vegetales",
            "Batido de proteina con banana y moras",
        ],
        "sources": [
            "https://manofmany.com/culture/fitness/robert-pattinson-batman-workout-diet-plan",
            "https://www.menshealth.com/fitness/a39367846/robert-pattinson-batman-diet-plan-aseel-soueid/",
        ],
        "aliases": ["batman pattinson", "batman robert pattinson", "robert pattinson", "pattinson"],
    },
    "capitan_america_evans": {
        "title": "Capitan America (Chris Evans)",
        "duration": "12 semanas",
        "focus": "Hipertrofia total y fuerza con alto volumen",
        "body_type": "Musculoso y equilibrado",
        "training": "5-6 sesiones/semana con division torso-pierna, trabajo accesorio y core frecuente.",
        "diet": "Superavit moderado-alto con muchas comidas, carbos complejos y proteina alta.",
        "calories": "~4000 kcal/dia",
        "macros": "Proteina ~2 g/kg (200-240 g/dia), carbos complejos altos, grasas saludables.",
        "meals": [
            "Avena con frutas y nueces",
            "Batido de suero + BCAA",
            "Manzana con almendras pre-entreno",
            "Ensalada de pollo con arroz integral",
            "Pescado o carne magra con verduras",
            "Caseina antes de dormir",
        ],
        "sources": [
            "https://manofmany.com/culture/fitness/chris-evans-captain-america-workout-diet-plan",
            "https://www.gq.com.mx/cuidados/fitness/articulos/rutina-de-ejercicio-de-chris-evans/3021",
        ],
        "aliases": ["capitan america", "capitan america chris evans", "chris evans"],
    },
    "superman_cavill": {
        "title": "Superman (Henry Cavill)",
        "duration": "12 semanas",
        "focus": "Hipertrofia + fuerza con alto volumen",
        "body_type": "Masivo y definido",
        "training": "Fases de fuerza maxima y luego circuitos intensos tipo acondicionamiento.",
        "diet": "Fase de volumen hipercalorica y luego ajuste a alimentos mas magros.",
        "calories": "~5000 kcal/dia (fase volumen)",
        "macros": "Proteina ~300 g/dia; carbos altos; grasas saludables.",
        "meals": [
            "5 claras + 2 yemas + filete + batido de avena",
            "Requeson con uvas",
            "Curry de pollo con arroz jazmin",
            "Carne magra con vegetales",
            "Batido de caseina nocturno",
        ],
        "sources": [
            "http://abcnews.go.com/blogs/entertainment/2013/06/henry-cavill-made-enormous-changes-using-man-of-steel-workout",
            "https://manofmany.com/culture/fitness/henry-cavills-superman-diet-workout-plan",
        ],
        "aliases": ["superman cavill", "henry cavill", "superman"],
    },
    "superman_corenswet": {
        "title": "Superman (David Corenswet)",
        "duration": "20 semanas",
        "focus": "Volumen con sobrecarga progresiva",
        "body_type": "Muy masivo",
        "training": "Split empuje-traccion-piernas con progresion semanal y tecnica estricta.",
        "diet": "Volumen limpio con 5 comidas solidas y 2 batidos hipercaloricos.",
        "calories": "4500-6000 kcal/dia",
        "macros": "Proteina ~250 g/dia; carbos abundantes; grasas moderadas.",
        "meals": [
            "4 huevos + avena con mantequilla de mani + leche entera",
            "Pollo con arroz",
            "Carne roja con pasta y verduras",
            "Batido hipercalorico (~1200 kcal)",
            "Yogur griego entero antes de dormir",
        ],
        "sources": [
            "https://www.gq.com/story/david-corenswet-superman-legacy-workout-1",
            "https://www.eonline.com/news/1419758/supermans-david-corenswet-details-diet-and-workout-transformation",
            "https://menshealth.com.au/david-corenswet-workout-routine-diet-plan/",
            "https://www.eatingwell.com/david-corenswet-weight-gain-for-superman-11769355",
        ],
        "aliases": ["superman corenswet", "david corenswet", "corenswet"],
    },
    "wolverine_jackman": {
        "title": "Wolverine (Hugh Jackman)",
        "duration": "12 semanas",
        "focus": "Fuerza + hipertrofia con periodizacion",
        "body_type": "Muy musculoso y definido",
        "training": "Basicos pesados con progresion y bloques 4x10-12 a 4x5.",
        "diet": "Ayuno 16/8 con ventana de comidas densas en calorias.",
        "calories": "~4000 kcal/dia (fase volumen)",
        "macros": "230 g proteina / 230 g carbohidratos / 230 g grasas aprox.",
        "meals": [
            "Avena con arandanos y 2 huevos",
            "Filete magro + batata + brocoli",
            "Pechuga de pollo con arroz integral",
            "Batido de suero + nueces",
            "Pescado blanco con aguacate y brocoli",
        ],
        "sources": [
            "https://www.businessinsider.com/how-hugh-jackman-got-in-shape-for-logan-2017-3",
            "https://www.businessinsider.com/4000-calorie-diet-hugh-jackman-get-shredded-to-play-wolverine-2020-7",
        ],
        "aliases": ["wolverine", "hugh jackman", "jackman"],
    },
}

# =========================================================
# Banco de ejercicios y selección
# =========================================================
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

def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    v = value.strip()
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(v)
    except Exception:
        return None

def _fetch_public_classes(search: Optional[str] = None) -> List[Dict[str, Any]]:
    if not BACKEND_BASE_URL:
        return []
    params: Dict[str, str] = {}
    if search:
        params["search"] = str(search).strip()
    try:
        resp = requests.get(
            f"{BACKEND_BASE_URL.rstrip('/')}/classes/public",
            params=params if params else None,
            timeout=CONTEXT_TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.warning("No se pudo obtener clases publicas: %s", exc)
        return []
    if resp.status_code != 200:
        logger.warning("Clases publicas no disponibles (status=%s)", resp.status_code)
        return []
    try:
        payload = resp.json()
    except Exception:
        return []
    classes = payload.get("classes") if isinstance(payload, dict) else None
    return classes if isinstance(classes, list) else []

def _fetch_public_sessions(class_id: Optional[int], start_iso: Optional[str], end_iso: Optional[str]) -> List[Dict[str, Any]]:
    if not BACKEND_BASE_URL:
        return []
    params: Dict[str, str] = {}
    if class_id is not None:
        params["class_id"] = str(class_id)
    if start_iso:
        params["start"] = start_iso
    if end_iso:
        params["end"] = end_iso
    try:
        resp = requests.get(
            f"{BACKEND_BASE_URL.rstrip('/')}/classes/public/sessions",
            params=params if params else None,
            timeout=CONTEXT_TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.warning("No se pudo obtener sesiones publicas: %s", exc)
        return []
    if resp.status_code != 200:
        logger.warning("Sesiones publicas no disponibles (status=%s)", resp.status_code)
        return []
    try:
        payload = resp.json()
    except Exception:
        return []
    sessions = payload.get("sessions") if isinstance(payload, dict) else None
    return sessions if isinstance(sessions, list) else []

def _norm_class_name(value: Any) -> str:
    return str(value or "").strip().lower()

def _resolve_class_match(name: str, classes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not name or not classes:
        return None
    norm = _norm_class_name(name)
    exact = [c for c in classes if _norm_class_name(c.get("name")) == norm]
    if exact:
        return exact[0]
    partial = [c for c in classes if norm in _norm_class_name(c.get("name"))]
    if len(partial) == 1:
        return partial[0]
    return None

def _format_session_label(session: Dict[str, Any]) -> Optional[str]:
    start = _parse_iso_datetime(session.get("start_time"))
    if not start:
        return None
    return f"{start.date().isoformat()} {start.strftime('%H:%M')}"

class ValidateReservaForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_reserva_form"

    def validate_clase(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        clase = str(value or "").strip()
        if not clase:
            dispatcher.utter_message(text="Necesito el nombre de la clase para reservar.")
            return {"clase": None}

        classes = _fetch_public_classes()
        if not classes:
            return {"clase": clase}

        match = _resolve_class_match(clase, classes)
        if match:
            return {"clase": match.get("name")}

        opciones = [c.get("name") for c in classes if c.get("name")]
        opciones = opciones[:6]
        if opciones:
            dispatcher.utter_message(text="No encontre esa clase. Opciones: " + ", ".join(opciones))
        else:
            dispatcher.utter_message(text="No encontre esa clase. Prueba con otro nombre.")
        return {"clase": None}

    def validate_fecha(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        fecha_raw = str(value or "").strip()
        fecha = _normaliza_fecha(fecha_raw)
        if not fecha:
            dispatcher.utter_message(text="Necesito una fecha valida (ej. 2025-01-10).")
            return {"fecha": None}
        if isinstance(fecha, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", fecha) and _fecha_es_pasada(fecha):
            dispatcher.utter_message(text="Esa fecha ya paso. Elige otra, por favor.")
            return {"fecha": None}
        return {"fecha": fecha}

    def validate_hora(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        hora_raw = str(value or "").strip()
        hora = _normaliza_hora(hora_raw)
        if not hora or not re.match(r"^\d{2}:\d{2}$", hora):
            dispatcher.utter_message(text="Necesito una hora valida (ej. 18:30).")
            return {"hora": None}
        return {"hora": hora}

# =========================================================
# VALIDATOR del FORM rutina_form (evita loops y normaliza)
# =========================================================
class ValidateRutinaForm(FormValidationAction):
    """Normaliza respuestas y coordina el cierre del formulario de rutinas."""

    REQUIRED_ORDER: Tuple[str, ...] = (
        "objetivo",
        "nivel",
        "musculo",
        "equipamiento",
        "ejercicios_num",
        "tiempo_disponible",
        "condiciones_salud",
        "alergias",
    )

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

    async def required_slots(
        self,
        domain_slots: List[Text],
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Text]:
        """Mantiene un orden consistente sin importar como esté definido el dominio."""
        if not domain_slots:
            return list(self.REQUIRED_ORDER)
        ordered = [slot for slot in self.REQUIRED_ORDER if slot in domain_slots]
        if ordered:
            extras = [slot for slot in domain_slots if slot not in ordered]
            return ordered + extras
        return domain_slots

    def _values_after_validation(
        self,
        tracker: Tracker,
        events: List[Any],
    ) -> Dict[str, Any]:
        after = dict(tracker.slots or {})
        for event in events:
            if isinstance(event, SlotSet):
                after[event.key] = event.value
        return after

    def _missing_slots(self, values: Dict[str, Any]) -> List[str]:
        missing: List[str] = []
        for slot in self.REQUIRED_ORDER:
            if values.get(slot) in {None, ""}:
                missing.append(slot)
        return missing

    async def get_validation_events(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Any]:
        events = await super().get_validation_events(dispatcher, tracker, domain)
        missing = self._missing_slots(self._values_after_validation(tracker, events))
        if not missing:
            already_closed = any(
                isinstance(ev, SlotSet) and ev.key == "requested_slot" and ev.value is None
                for ev in events
            )
            if not already_closed:
                events.append(SlotSet("requested_slot", None))
            events.append(FollowupAction("action_generar_rutina"))
        return events

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

    def validate_nivel(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        v = self._norm_text(value)
        aliases = {
            "principiante": "principiante",
            "novato": "principiante",
            "básico": "principiante",
            "basico": "principiante",
            "suave": "principiante",
            "ligero": "principiante",
            "regenerativo": "principiante",
            "descarga": "principiante",
            "de descarga": "principiante",
            "intermedio": "intermedio",
            "intermedia": "intermedio",
            "moderado": "intermedio",
            "moderada": "intermedio",
            "progresivo": "intermedio",
            "intermedio bajo": "intermedio",
            "intermedio alto": "intermedio",
            "avanzado": "avanzado",
            "avanzada": "avanzado",
            "avanzado plus": "avanzado",
            "desafiante": "avanzado",
            "explosivo": "avanzado",
        }
        if v:
            v = aliases.get(v, v)
            if v in {"principiante", "intermedio", "avanzado"}:
                return {"nivel": v}
            dispatcher.utter_message(
                text="No reconocí ese nivel. Usa principiante, intermedio o avanzado."
            )
            return {"nivel": None}

        # Si no hay valor, intenta usar el perfil del usuario
        ctx = ensure_authenticated_context(tracker)
        profile = fetch_user_profile(ctx)
        inferred = infer_training_level(profile)
        if inferred:
            dispatcher.utter_message(text=f"Asumiré nivel {inferred} según tu actividad registrada.")
            return {"nivel": inferred}
        dispatcher.utter_message(text="No tengo tu nivel, usaré intermedio por defecto. Si quieres otro, dímelo.")
        return {"nivel": "intermedio"}

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


class ValidateHeroForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_hero_form"

    def _norm(self, value: Any) -> str:
        return (str(value or "")).strip().lower()

    def _match_program(self, value: Any) -> Optional[str]:
        norm = self._norm(value)
        if not norm:
            return None
        for key, data in HERO_PROGRAMS.items():
            title = self._norm(data.get("title"))
            if key in norm or (title and title in norm):
                return key
            for alias in data.get("aliases", []):
                if self._norm(alias) in norm:
                    return key
        return None

    def validate_hero_programa(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        matched = self._match_program(value)
        if matched:
            return {"hero_programa": matched}
        dispatcher.utter_message(
            text=(
                "No reconocí ese plan. Elige entre Shonen Power, Ninja Agility, Mecha Endurance, "
                "Batman (Christian Bale), Batman (Ben Affleck), Batman (Robert Pattinson), "
                "Capitan America (Chris Evans), Superman (Henry Cavill), Superman (David Corenswet) "
                "o Wolverine (Hugh Jackman)."
            )
        )
        return {"hero_programa": None}

    def validate_hero_inicio(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        raw = (str(value or "")).strip()
        if not raw:
            dispatcher.utter_message(text="Necesito saber cuándo deseas comenzar para programar las fases.")
            return {"hero_inicio": None}
        try:
            chosen = datetime.fromisoformat(raw).date()
        except Exception:
            return {"hero_inicio": raw}
        if chosen < date.today():
            dispatcher.utter_message(text="Esa fecha ya pasó. Indícame otra, por favor.")
            return {"hero_inicio": None}
        return {"hero_inicio": chosen.isoformat()}

    def validate_hero_equipo(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        raw = (str(value or "")).strip()
        if not raw:
            dispatcher.utter_message(text="Describe con qué equipamiento cuentas (casa, gimnasio, TRX, etc.).")
            return {"hero_equipo": None}
        return {"hero_equipo": raw}


# =========================================================
# ACCIÓN: Generar rutina completa
# =========================================================
class ActionGenerarRutina(Action):
    def name(self) -> Text:
        return "action_generar_rutina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        intent_name = tracker.latest_message.get("intent", {}).get("name")
        offline_backend = not backend_health_ok(sender_id=tracker.sender_id, intent=intent_name, demo_offline=tracker.get_slot("demo_offline"))
        offline_events: List[Dict[Text, Any]] = []
        if offline_backend:
            offline_events.extend(mark_offline(dispatcher, tracker))
        ctx: Optional[Dict[str, Any]] = None
        if REQUIRE_AUTH_FOR_ROUTINE:
            ctx = ensure_authenticated_context(tracker)
            if ctx is None and not offline_backend:
                dispatcher.utter_message(text="Necesitas iniciar sesión en Fitter antes de generar tu rutina. Inicia sesión y vuelve a intentarlo.")
                return []
        if ctx is None:
            ctx = ensure_authenticated_context(tracker)

        profile_data = None if offline_backend else fetch_user_profile(ctx)

        profile_goal = None
        if profile_data and profile_data.get("primary_goal"):
            profile_goal = str(profile_data["primary_goal"]).replace("_", " ").strip().lower()
        somatotipo = (_slot(tracker, "somatotipo") or (profile_data.get("somatotipo") if profile_data else None) or "").strip().lower()

        raw_musculo = _slot(tracker, "musculo") or tracker.get_slot("musculo_preferido")
        # If the user hasn't provided a muscle group, ask explicitly and show profile summary
        if not raw_musculo:
            # show profile summary if available
            if profile_data:
                profile_bits: List[str] = []
                weight = profile_data.get("weight_kg")
                height = profile_data.get("height_cm")
                goal = profile_data.get("primary_goal")
                activity = profile_data.get("activity_level")
                if weight:
                    profile_bits.append(f"Peso: {weight} kg")
                if height:
                    profile_bits.append(f"Altura: {height} cm")
                if goal:
                    profile_bits.append(f"Objetivo declarado: {str(goal).replace('_', ' ')}")
                if activity:
                    profile_bits.append(f"Actividad: {activity}")
                if profile_bits:
                    resumen = "Datos perfil: " + " | ".join(profile_bits)
                    dispatcher.utter_message(text=resumen)
            # ask which muscle to train
            dispatcher.utter_message(response="utter_ask_musculo")
            return []
        musculo = (raw_musculo or "brazos").lower()
        inferred_level = infer_training_level(profile_data)
        nivel = (_slot(tracker, "nivel") or inferred_level or "intermedio").lower()
        objetivo = (_slot(tracker, "objetivo") or profile_goal or "fuerza").lower()
        equip = (_slot(tracker, "equipamiento") or "mancuernas").lower()

        condiciones = _slot(tracker, "condiciones_salud") or (profile_data.get("medical_conditions") if profile_data else None) or "ninguna"
        alergias = _slot(tracker, "alergias") or (profile_data.get("allergies") if profile_data else None) or "ninguna"
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
        if offline_backend:
            header_lines.append("Modo offline: rutina generada localmente sin perfil web.")
        if somatotipo and somatotipo not in {"no_se", "no se", "no sé", "ninguno", "ninguna"}:
            tip = SOMATOTIPO_TIPS_RUTINA.get(somatotipo)
            if tip:
                header_lines.append(f"Somatotipo (heurístico): {somatotipo}. {tip}")
        if profile_data:
            profile_bits: List[str] = []
            weight = profile_data.get("weight_kg")
            height = profile_data.get("height_cm")
            goal = profile_data.get("primary_goal")
            activity = profile_data.get("activity_level")
            if weight:
                profile_bits.append(f"Peso: {weight} kg")
            if height:
                profile_bits.append(f"Altura: {height} cm")
            if goal:
                profile_bits.append(f"Objetivo declarado: {str(goal).replace('_', ' ')}")
            if activity:
                profile_bits.append(f"Actividad: {activity}")
            if profile_bits:
                header_lines.append("Datos perfil: " + " | ".join(profile_bits))
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
                "somatotipo": somatotipo if somatotipo else None,
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

        plan_id = None
        if not offline_backend:
            plan_id = persist_plan(
                ctx,
                path="/api/routine-plans",
                payload={
                    "title": routine_summary.get("header") or "Rutina generada",
                    "objective": objetivo,
                    "content": routine_summary,
                },
            )
        if plan_id:
            dispatcher.utter_message(text=f"Rutina guardada. ID: {plan_id}\nVer detalle: /cuenta/rutinas/{plan_id}")

        # Send the routine as an attached PDF to the user's email in background
        # (do not block the action thread to avoid connector timeouts)
        try:
            if EMAIL_ROUTINE_ENABLED and ctx:
                threading.Thread(
                    target=maybe_send_routine_email,
                    args=(ctx,),
                    kwargs={"routine_data": routine_summary, "attach": True},
                    daemon=True,
                ).start()
        except Exception as exc:
            logger.warning("No se pudo iniciar thread para enviar rutina por correo: %s", exc)

        context_payload: Dict[str, Any] = {}
        if condiciones and condiciones.lower() not in {"", "ninguna", "ninguno", "no"}:
            context_payload["medical_conditions"] = condiciones
        if alergias and alergias.lower() not in {"", "ninguna", "ninguno", "no"}:
            context_payload["allergies"] = alergias
        if dislikes and str(dislikes).strip():
            context_payload["dislikes"] = dislikes
        if context_payload:
            send_context_update(tracker.sender_id, context_payload)

        return offline_events + [
            SlotSet("ultima_rutina", routine_summary),
            SlotSet("servicio_pendiente", None),
        ]

# =========================================================
# ACCION: Generar dieta complementaria
# =========================================================
class ActionGenerarDieta(Action):
    def name(self) -> Text:
        return "action_generar_dieta"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        logger.info(f"=== DIETA CONFIG === CHAT_DIETA_CALC_MODE={CHAT_DIETA_CALC_MODE}, CHAT_DIET_CATALOG={CHAT_DIET_CATALOG}")
        
        intent_name = tracker.latest_message.get("intent", {}).get("name")
        offline_backend = not backend_health_ok(sender_id=tracker.sender_id, intent=intent_name, demo_offline=tracker.get_slot("demo_offline"))
        offline_events: List[Dict[Text, Any]] = []
        if offline_backend:
            offline_events.extend(mark_offline(dispatcher, tracker))

        ctx = ensure_authenticated_context(tracker)
        profile_data = None if offline_backend else fetch_user_profile(ctx)
        ctx_dislikes = ctx.get("dislikes") if ctx else None

        profile_goal = None
        if profile_data and profile_data.get("primary_goal"):
            profile_goal = str(profile_data["primary_goal"]).replace("_", " ").strip().lower()
        somatotipo = (_slot(tracker, "somatotipo") or (profile_data.get("somatotipo") if profile_data else None) or "").strip().lower()

        # prefer explicit slot, then profile, then sensible default
        objetivo_slot = _slot(tracker, "objetivo")
        objetivo = (objetivo_slot or profile_goal or "equilibrada").lower()
        inferred_level = infer_training_level(profile_data)
        nivel = (_slot(tracker, "nivel") or inferred_level or "intermedio").lower()
        alergias = _slot(tracker, "alergias") or (profile_data.get("allergies") if profile_data else None) or "ninguna"
        dislikes = _slot(tracker, "no_gusta") or ctx_dislikes
        condiciones = _slot(tracker, "condiciones_salud") or (profile_data.get("medical_conditions") if profile_data else None) or "ninguna"

        # If essential info is missing (objetivo explicit or peso), ask like routines do
        peso_slot = tracker.get_slot("peso")
        missing_objetivo = not objetivo_slot and not profile_goal
        missing_peso = (peso_slot is None) and not (profile_data and profile_data.get("weight_kg"))
        if missing_objetivo or missing_peso:
            # show profile summary if available
            if profile_data:
                profile_bits: List[str] = []
                weight = profile_data.get("weight_kg")
                height = profile_data.get("height_cm")
                goal = profile_data.get("primary_goal")
                activity = profile_data.get("activity_level")
                if weight:
                    profile_bits.append(f"Peso: {weight} kg")
                if height:
                    profile_bits.append(f"Altura: {height} cm")
                if goal:
                    profile_bits.append(f"Objetivo declarado: {str(goal).replace('_', ' ')}")
                if activity:
                    profile_bits.append(f"Actividad: {activity}")
                if profile_bits:
                    resumen = "Datos perfil: " + " | ".join(profile_bits)
                    dispatcher.utter_message(text=resumen)

            # ask for missing slots (objetivo first)
            if missing_objetivo:
                dispatcher.utter_message(response="utter_ask_objetivo")
                return []
            if missing_peso:
                dispatcher.utter_message(response="utter_ask_peso")
                return []

        plan = DIET_BASES.get(objetivo) or DIET_BASES.get("equilibrada")
        plan_label = objetivo if objetivo in DIET_BASES else "equilibrada"
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
        if somatotipo and somatotipo not in {"no_se", "no se", "no sé", "ninguno", "ninguna"}:
            tip = SOMATOTIPO_TIPS_DIETA.get(somatotipo)
            if tip:
                adjustments.append(f"Somatotipo (heurístico): {somatotipo}. {tip}")

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

        # Opt-in: calcular kcal objetivo y macros en gramos si la feature está activada
        dieta_calc_info: Optional[Dict[str, Any]] = None
        if CHAT_DIETA_CALC_MODE != "off":
            try:
                weight = None
                if profile_data and profile_data.get("weight_kg") is not None:
                    weight = _to_float(profile_data.get("weight_kg"))
                # intentar obtener altura/edad/sexo del perfil
                height = None
                if profile_data and profile_data.get("height_cm") is not None:
                    height = _to_float(profile_data.get("height_cm"))
                age = None
                if profile_data and profile_data.get("age") is not None:
                    try:
                        age = int(profile_data.get("age"))
                    except Exception:
                        age = None
                sex = profile_data.get("sex") if profile_data else None
                activity = profile_data.get("activity_level") if profile_data else None
                should_calc = CHAT_DIETA_CALC_MODE == "on" or (CHAT_DIETA_CALC_MODE == "auto" and weight and height)
                if should_calc:
                    dieta_calc_info = calc_target_kcal_and_macros(
                        weight_kg=weight,
                        height_cm=height,
                        age=age,
                        sex=sex,
                        activity_level=activity,
                        objetivo=objetivo,
                        somatotipo=somatotipo if somatotipo else None,
                    )
            except Exception:
                dieta_calc_info = None

        lines: List[str] = [
            f"Plan alimenticio sugerido para objetivo {plan_label} (nivel {nivel}).",
            f"Calorias estimadas: {plan.get('calorias', 'mantenimiento')}",
            "Macros orientativas:",
            f"- Proteinas: {macros.get('proteinas', '-')}",
            f"- Carbohidratos: {macros.get('carbohidratos', '-')}",
            f"- Grasas: {macros.get('grasas', '-')}",
        ]
        if offline_backend:
            lines.insert(1, "Modo offline: plan generado localmente sin perfil web.")
        if adjustments:
            lines.append("Ajustes y personalización:")
            for note in adjustments:
                lines.append(f"- {note}")
        if dieta_calc_info and dieta_calc_info.get("target_kcal"):
            lines.append("Detalle calórico estimado:")
            if dieta_calc_info.get("bmr"):
                lines.append(f"- BMR: {dieta_calc_info.get('bmr')} kcal")
            if dieta_calc_info.get("maintenance_kcal"):
                lines.append(f"- Mantenimiento: {dieta_calc_info.get('maintenance_kcal')} kcal")
            if dieta_calc_info.get("target_kcal"):
                lines.append(f"- Objetivo: {dieta_calc_info.get('target_kcal')} kcal")
            if dieta_calc_info.get("proteinas_g") and dieta_calc_info.get("carbs_g") and dieta_calc_info.get("fats_g"):
                lines.append(f"- Macros: {dieta_calc_info.get('proteinas_g')}g P / {dieta_calc_info.get('carbs_g')}g C / {dieta_calc_info.get('fats_g')}g G")
            if dieta_calc_info.get("note"):
                lines.append(f"Nota: {dieta_calc_info.get('note')}")
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
                "somatotipo": somatotipo if somatotipo else None,
                # si se calculó la versión opt-in, añadimos valores absolutos
                **({
                    "target_kcal": dieta_calc_info.get("target_kcal"),
                    "bmr": dieta_calc_info.get("bmr"),
                    "maintenance_kcal": dieta_calc_info.get("maintenance_kcal"),
                    "proteinas_g": dieta_calc_info.get("proteinas_g"),
                    "carbs_g": dieta_calc_info.get("carbs_g"),
                    "fats_g": dieta_calc_info.get("fats_g"),
                    "dieta_note": dieta_calc_info.get("note"),
                } if dieta_calc_info else {}),
                "hydration": hydration,
                "health_adjustments": adjustments or None,
                "allergies": allergy_list or None,
                "dislikes": dislike_list or None,
                "medical_conditions": condiciones if condiciones.lower() not in {"", "ninguna", "ninguno", "no"} else None,
                "allergen_hits": allergen_hits or None,
            },
            "meals": filtered_meals,
        }

        # If catalog integration is enabled, prefer local composer when available
        final_meals = filtered_meals  # Default to generic meals
        if CHAT_DIET_CATALOG:
            used_composer = False
            # try local composer first (faster, offline)
            try:
                if compose_diet:
                    # choose target kcal from calculated info if available
                    target_kcal = None
                    if dieta_calc_info and isinstance(dieta_calc_info, dict):
                        target_kcal = dieta_calc_info.get('target_kcal')
                    if target_kcal is None:
                        # fallback sensible default
                        target_kcal = 2000
                    n_meals = len(filtered_meals) or 3
                    # allow composer to use the project's catalog file
                    catalog_path = os.path.join(_BASE_DIR, 'backend', 'data', 'food_catalog_curated.json')
                    logger.info(f"=== COMPOSER ATTEMPT === target_kcal={target_kcal}, n_meals={n_meals}, catalog_path={catalog_path}")
                    # determine weight to pass to composer
                    weight_val = None
                    try:
                        if profile_data and profile_data.get('weight_kg') is not None:
                            weight_val = _to_float(profile_data.get('weight_kg'))
                        else:
                            weight_val = _to_float(tracker.get_slot('peso'))
                    except Exception:
                        weight_val = None

                    composed = compose_diet(
                        int(target_kcal),
                        n_meals=n_meals,
                        catalog_path=catalog_path,
                        exclude_allergens=allergy_list or None,
                        objetivo=objetivo,
                        weight_kg=weight_val,
                    )
                    logger.info(f"=== COMPOSE_DIET RESULT === composed type: {type(composed)}, has meals: {bool(composed and composed.get('meals'))}")
                    if composed and isinstance(composed, dict):
                        composed_meals: List[Dict[str, Any]] = []
                        for meal in composed.get('meals', []):
                            items_out: List[Dict[str, Any]] = []
                            for it in meal.get('items', []):
                                name = it.get('name') or it.get('id')
                                qty = it.get('qty_g') or it.get('qty') or 100
                                kcal = it.get('kcal')
                                items_out.append({'name': name, 'qty': f"{int(qty)} g", 'kcal': kcal})
                            composed_meals.append({'name': meal.get('name'), 'items': items_out, 'notes': None})
                        diet_payload['meals'] = composed_meals
                        final_meals = composed_meals  # Update final_meals with catalog data
                        logger.info(f"=== COMPOSER SUCCESS === Replaced meals with {len(composed_meals)} composed meals")
                        used_composer = True
            except Exception as e:
                logger.error(f"=== COMPOSER FAILED === {type(e).__name__}: {e}", exc_info=True)
                used_composer = False

            # fallback to remote HTTP catalog composition if local composer not used
            if not used_composer and BACKEND_BASE_URL:
                try:
                    exclude_allergens_param = ",".join([a for a in (allergy_list or [])])
                    catalog_url = f"{BACKEND_BASE_URL.rstrip('/')}/notifications/catalog?limit=200"
                    if exclude_allergens_param:
                        catalog_url += f"&exclude_allergens={quote(exclude_allergens_param)}"
                    resp = requests.get(catalog_url, timeout=CONTEXT_TIMEOUT)
                    if resp.ok:
                        catalog_items = resp.json().get('items', [])
                    else:
                        catalog_items = []
                except Exception:
                    catalog_items = []

                # simple composition: for each meal, pick up to 3 items from catalog (rotating)
                if catalog_items:
                    composed_meals: List[Dict[str, Any]] = []
                    idx = 0
                    for meal in filtered_meals:
                        items_for_meal: List[Dict[str, Any]] = []
                        for _i in range(3):
                            if not catalog_items:
                                break
                            item = catalog_items[idx % len(catalog_items)]
                            idx += 1
                            name = item.get('name') or item.get('name_es') or item.get('id')
                            kcal100 = item.get('energy_kcal_100g') or 0
                            qty_g = item.get('serving_size_g') or 100
                            kcal = round((kcal100 * qty_g) / 100.0) if kcal100 else None
                            items_for_meal.append({
                                'name': name,
                                'qty': f"{int(qty_g)} g",
                                'kcal': kcal,
                                'source': item.get('source'),
                            })
                        composed_meals.append({
                            'name': meal.get('name'),
                            'items': items_for_meal,
                            'notes': meal.get('notes')
                        })
                    diet_payload['meals'] = composed_meals
                    final_meals = composed_meals  # Update final_meals with HTTP catalog data
        
        # Build text response AFTER catalog processing, using final_meals
        lines.append("Menu diario ejemplo:")
        for meal in final_meals:
            items = meal.get("items", [])
            # Handle both string arrays and object arrays
            if items and isinstance(items[0], dict):
                # Catalog format: array of {name, qty, kcal}
                items_str = ", ".join([f"{it.get('name')} ({it.get('qty', '100g')}, {it.get('kcal', '?')} kcal)" for it in items])
            else:
                # Old format: array of strings
                items_str = ", ".join(items)
            lines.append(f"- {meal.get('name', 'Comida')}: {items_str}")
            note = meal.get("notes")
            if note:
                lines.append(f"  Nota: {note}")
        if hydration:
            lines.append(f"Hidratacion recomendada: {hydration}")

        text_response = "\n".join(lines)
        dispatcher.utter_message(text=text_response)
        dispatcher.utter_message(json_message=diet_payload)

        diet_id = None
        if not offline_backend:
            diet_id = persist_plan(
                ctx,
                path="/api/diet-plans",
                payload={
                    "title": f"Dieta {plan_label}".strip(),
                    "goal": plan_label,
                    "content": diet_payload,
                },
            )
        if diet_id:
            dispatcher.utter_message(text=f"Dieta guardada. ID: {diet_id}\nVer detalle: /cuenta/dietas/{diet_id}")

        context_payload: Dict[str, Any] = {}
        if condiciones and condiciones.lower() not in {"", "ninguna", "ninguno", "no"}:
            context_payload["medical_conditions"] = condiciones
        if alergias and alergias.lower() not in {"", "ninguna", "ninguno", "no"}:
            context_payload["allergies"] = alergias
        if dislikes and str(dislikes).strip():
            context_payload["dislikes"] = dislikes
        if context_payload:
            send_context_update(tracker.sender_id, context_payload)

        return offline_events + [
            SlotSet("ultima_dieta", diet_payload),
            SlotSet("servicio_pendiente", None),
        ]



class ActionInscribirEntrenoUnico(Action):
    def name(self) -> Text:
        return "action_inscribir_entreno_unico"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        ctx = ensure_authenticated_context(tracker)
        raw_key = _slot(tracker, "hero_programa") or "shonen"
        key = raw_key.lower()
        plan = HERO_PROGRAMS.get(key, HERO_PROGRAMS["shonen"])
        inicio = tracker.get_slot("hero_inicio") or "cuando estés listo"
        equip = tracker.get_slot("hero_equipo") or "solo peso corporal"
        diet = plan.get("diet")
        calories = plan.get("calories")
        macros = plan.get("macros")
        meals = plan.get("meals") or []
        sources = plan.get("sources") or []

        header = f"Plan {plan['title']} — {plan['duration']}"
        lines = [
            header,
            f"Enfoque: {plan['focus']}",
            f"Tipo de cuerpo objetivo: {plan['body_type']}",
            f"Inicio estimado: {inicio}",
            f"Equipamiento declarado: {equip}",
            plan["training"],
            "Te enviaré recordatorios y recomendaciones adicionales si completas tu perfil.",
        ]
        if diet:
            lines.insert(5, f"Enfoque dietario: {diet}")
        if calories:
            lines.append(f"Calorias diarias: {calories}")
        if macros:
            lines.append(f"Macros: {macros}")
        if meals:
            lines.append("Ejemplos de comidas: " + "; ".join(meals))
        if sources:
            lines.append("Fuentes: " + " | ".join(sources))
        if ctx and plan.get("title"):
            saved = save_hero_plan(
                ctx,
                {
                    "type": "hero_training_plan",
                    "plan_key": key,
                    "title": plan["title"],
                    "duration": plan["duration"],
                    "focus": plan["focus"],
                    "body_type": plan["body_type"],
                    "training": plan["training"],
                    "diet": diet,
                    "calories": calories,
                    "macros": macros,
                    "meals": meals,
                    "sources": sources,
                    "start": inicio,
                    "equipment": equip,
                },
            )
            if saved:
                lines.append("Guarde este entreno unico en tu perfil para consultarlo cuando quieras.")

        dispatcher.utter_message(text="\n".join(lines))
        dispatcher.utter_message(json_message={
            "type": "hero_training_plan",
            "plan_key": key,
            "title": plan["title"],
            "duration": plan["duration"],
            "focus": plan["focus"],
            "body_type": plan["body_type"],
            "start": inicio,
            "equipment": equip,
            "diet": diet,
            "calories": calories,
            "macros": macros,
            "meals": meals,
            "sources": sources,
        })

        return [
            SlotSet("hero_programa", None),
            SlotSet("hero_inicio", None),
            SlotSet("hero_equipo", None),
        ]

class ActionSugerirRutina(Action):
    def name(self) -> Text:
        return "action_sugerir_rutina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        ctx = ensure_authenticated_context(tracker)
        profile_data = fetch_user_profile(ctx) if ctx else None
        inferred_level = infer_training_level(profile_data)

        objetivo = (_slot(tracker, "objetivo") or "hipertrofia").lower()
        musculo  = (_slot(tracker, "musculo")  or "fullbody").lower()
        nivel    = (_slot(tracker, "nivel")    or inferred_level or "principiante").lower()
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

        ctx = ensure_authenticated_context(tracker)
        profile_data = fetch_user_profile(ctx) if ctx else None
        inferred_level = infer_training_level(profile_data)

        objetivo = _slot(tracker, "objetivo") or "general"
        musculo  = _slot(tracker, "musculo")  or "fullbody"
        nivel    = _slot(tracker, "nivel")    or inferred_level or "principiante"

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

        classes = _fetch_public_classes()
        if classes:
            match = _resolve_class_match(clase, classes)
            if not match:
                opciones = [c.get("name") for c in classes if c.get("name")][:6]
                if opciones:
                    dispatcher.utter_message(text="No encontre esa clase. Opciones: " + ", ".join(opciones))
                else:
                    dispatcher.utter_message(text="No encontre esa clase. Prueba con otro nombre.")
                return [SlotSet("clase", None), FollowupAction("reserva_form")]

            class_id = match.get("id")
            class_name = match.get("name") or clase
            if isinstance(fecha, str):
                day_start = f"{fecha}T00:00:00"
                day_end = f"{fecha}T23:59:59"
            else:
                day_start = None
                day_end = None
            sessions = _fetch_public_sessions(class_id, day_start, day_end)
            if sessions:
                match_session = None
                for session in sessions:
                    start = _parse_iso_datetime(session.get("start_time"))
                    if not start:
                        continue
                    if start.date().isoformat() == fecha and start.strftime("%H:%M") == hora:
                        match_session = session
                        break
                if not match_session:
                    opciones = []
                    for session in sessions:
                        label = _format_session_label(session)
                        if label:
                            opciones.append(label)
                    if opciones:
                        dispatcher.utter_message(
                            text="No hay clase en ese horario. Opciones: " + ", ".join(opciones[:6])
                        )
                    else:
                        dispatcher.utter_message(text="No hay horarios para esa fecha.")
                    return [SlotSet("hora", None), FollowupAction("reserva_form")]
            else:
                dispatcher.utter_message(text="No hay clases disponibles para esa fecha.")
                return [SlotSet("fecha", None), SlotSet("hora", None), FollowupAction("reserva_form")]

            clase = class_name

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
