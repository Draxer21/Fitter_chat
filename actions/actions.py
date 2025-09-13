# actions/actions.py
from __future__ import annotations
from typing import Any, Text, Dict, List, Optional
from datetime import datetime

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

# -------------------------------
# Catálogos base (demo)
# -------------------------------
OBJECTIVE_TIPS = {
    "hipertrofia": "Rango 8–12 repeticiones, RPE 7–8, descansos 60–90s.",
    "fuerza": "Rango 3–6 repeticiones, RPE 8–9, descansos 2–3 min.",
    "bajar_grasa": "Circuitos 12–15 repeticiones, pausas cortas + 2–3 sesiones de cardio.",
    "resistencia": "Volumen moderado, pausas cortas, 20–30 min de trabajo aeróbico."
}

MUSCLE_PLANS = {
    "pecho":   ["Press banca 4x8–10", "Press inclinado mancuernas 3x10–12", "Aperturas 3x12–15"],
    "espalda": ["Dominadas asistidas 4x6–8", "Remo con barra 4x8–10", "Jalón al pecho 3x10–12"],
    "piernas": ["Sentadilla 4x6–8", "Prensa 3x10–12", "Peso muerto rumano 3x8–10"],
    "hombros": ["Press militar 4x6–8", "Elevaciones laterales 3x12–15", "Pájaros 3x12–15"],
    "brazos":  ["Curl barra 4x8–10", "Fondos 3x8–10", "Curl martillo 3x10–12"],
    "core":    ["Plancha 3x40–60s", "Crunch 3x15–20", "Elevación de piernas 3x12–15"],
    "fullbody":["Sentadilla 3x8", "Press banca 3x8", "Remo 3x8", "Peso muerto 3x5"]
}

NUTRICION_TIPS = {
    "hipertrofia":  "Proteínas 1.6–2.2 g/kg; superávit calórico leve (5–10%).",
    "bajar_grasa":  "Déficit calórico 10–20%; proteínas 1.8–2.4 g/kg; fibra alta.",
    "fuerza":       "Calorías de mantenimiento ±5%; hidratos pre/post entreno.",
    "resistencia":  "Hidratos 5–7 g/kg; hidratación y electrolitos; proteínas 1.4–1.8 g/kg."
}

# “Base de datos” en memoria (demo). En producción: PostgreSQL/CRM.
RESERVAS: List[Dict[str, Any]] = []


def _slot(tracker: Tracker, name: str) -> Optional[str]:
    v = tracker.get_slot(name)
    return str(v).strip() if v else None


def _normaliza_fecha(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    v = value.lower()
    today = datetime.now().date()
    if v == "hoy":
        return today.isoformat()
    if v == "mañana":
        return (today).fromordinal(today.toordinal() + 1).isoformat()
    try:
        # AAAA-MM-DD
        return datetime.fromisoformat(v).date().isoformat()
    except Exception:
        return value  # dejar tal cual si no cumple ISO; el front podrá validar


def _normaliza_hora(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%H:%M").strftime("%H:%M")
    except Exception:
        return value  # dejar tal cual si no cumple HH:MM


# -------------------------------
# ACCIÓN: Sugerir rutina
# -------------------------------
class ActionSugerirRutina(Action):
    def name(self) -> Text:
        return "action_sugerir_rutina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        objetivo = (_slot(tracker, "objetivo") or "general").lower()
        musculo  = (_slot(tracker, "musculo")  or "fullbody").lower()
        nivel    = (_slot(tracker, "nivel")    or "principiante").lower()

        ejercicios = MUSCLE_PLANS.get(musculo, MUSCLE_PLANS["fullbody"])
        tip = OBJECTIVE_TIPS.get(objetivo, "Ajusta volumen e intensidad según tolerancia.")

        texto = (
            f"Rutina sugerida ▶ {musculo.title()} · objetivo: {objetivo} · nivel: {nivel}\n"
            + "\n".join([f"- {e}" for e in ejercicios])
            + f"\n\nNotas: {tip}"
        )
        dispatcher.utter_message(text=texto)
        return []


# -------------------------------
# ACCIÓN: Resumen rutina (cierre de formulario)
# -------------------------------
class ActionResumenRutina(Action):
    def name(self) -> Text:
        return "action_resumen_rutina"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        objetivo = _slot(tracker, "objetivo")
        musculo  = _slot(tracker, "musculo")
        nivel    = _slot(tracker, "nivel")
        dispatcher.utter_message(
            text=f"Resumen ▶ objetivo: {objetivo}, grupo: {musculo}, nivel: {nivel}. ¿Deseas otra sugerencia?"
        )
        return []


# -------------------------------
# ACCIÓN: Consejo de nutrición (ligado a objetivo)
# -------------------------------
class ActionConsejoNutricion(Action):
    def name(self) -> Text:
        return "action_consejo_nutricion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        objetivo = (_slot(tracker, "objetivo") or "general").lower()
        consejo = NUTRICION_TIPS.get(objetivo,
                                     "Prioriza proteína adecuada, vegetales, fibra y buena hidratación.")
        dispatcher.utter_message(text=f"Nutrición ▶ objetivo {objetivo}: {consejo}")
        return []


# -------------------------------
# ACCIÓN: Crear reserva
# -------------------------------
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

        reserva = {
            "user": tracker.sender_id,
            "clase": clase,
            "fecha": fecha,
            "hora": hora,
            "created_at": datetime.now().isoformat(timespec="seconds")
        }
        RESERVAS.append(reserva)
        dispatcher.utter_message(
            text=f"Reserva creada ✅: {clase} el {fecha} a las {hora} (demo)."
        )
        return []


# -------------------------------
# ACCIÓN: Cancelar reserva
# -------------------------------
class ActionCancelarReserva(Action):
    def name(self) -> Text:
        return "action_cancelar_reserva"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        clase = _slot(tracker, "clase")
        fecha = _normaliza_fecha(_slot(tracker, "fecha"))
        hora  = _normaliza_hora(_slot(tracker, "hora"))

        # Criterio de cancelación: si vienen los tres campos, cancelar exacto; si no, cancelar la más próxima del usuario
        global RESERVAS
        before = len(RESERVAS)

        if clase and fecha and hora:
            RESERVAS = [r for r in RESERVAS if not (
                r["user"] == tracker.sender_id and r["clase"] == clase and r["fecha"] == fecha and r["hora"] == hora
            )]
        else:
            # eliminar la primera reserva del usuario (demo)
            for i, r in enumerate(RESERVAS):
                if r["user"] == tracker.sender_id:
                    RESERVAS.pop(i)
                    break

        after = len(RESERVAS)
        if after < before:
            dispatcher.utter_message(text="Reserva cancelada ✅ (demo).")
        else:
            dispatcher.utter_message(text="No encontré una reserva que coincida para cancelar (demo).")
        return []


# -------------------------------
# ACCIÓN: Consultar reserva
# -------------------------------
class ActionConsultarReserva(Action):
    def name(self) -> Text:
        return "action_consultar_reserva"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user = tracker.sender_id
        # Mostrar la próxima reserva del usuario (demo)
        user_reservas = [r for r in RESERVAS if r["user"] == user]
        if not user_reservas:
            dispatcher.utter_message(text="No tienes reservas registradas (demo).")
            return []

        # En demo, mostramos la última creada
        r = user_reservas[-1]
        dispatcher.utter_message(text=f"Tu reserva ▶ {r['clase']} el {r['fecha']} a las {r['hora']} (demo).")
        return []
