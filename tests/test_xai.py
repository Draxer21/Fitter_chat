"""
Tests de Explainability (XAI).
Verifica que las rutinas y dietas generadas incluyen bloques de explicacion
conversacionales con datos_usados, razonamiento, criterios, reglas y fuentes.
"""
import pytest
from backend.chat.orchestrator import format_explanation_block
from backend.planner.workouts import generate_workout_plan


class TestFormatExplanationBlock:
    """Verificar el formateo conversacional del bloque XAI."""

    def test_complete_payload(self):
        payload = {
            "datos_usados": {"objetivo": "fuerza", "nivel": "intermedio", "musculo": "pecho"},
            "razonamiento": [
                "Elegí 4-5 series de 3-5 repeticiones porque para fuerza en nivel intermedio "
                "este rango maximiza las adaptaciones neuromusculares."
            ],
            "criterios": ["Series basadas en objetivo-nivel", "Reps ajustadas a fuerza"],
            "reglas": ["Sin restricciones de salud"],
            "fuentes": ["ExRx catalog", "WHO 2020"],
        }
        result = format_explanation_block(payload)
        # Debe ser conversacional, no lista rigida
        assert "tome en cuenta" in result or "informacion" in result
        assert "parametros" in result or "definieron" in result
        assert "restricciones" in result or "precauciones" in result
        assert "basada en" in result
        assert "fuerza" in result
        assert "ExRx" in result

    def test_empty_payload(self):
        result = format_explanation_block({})
        assert "valores por defecto" in result

    def test_datos_usados_shows_values(self):
        payload = {
            "datos_usados": {"peso": 75, "altura": 175},
            "criterios": [],
            "reglas": [],
            "fuentes": [],
        }
        result = format_explanation_block(payload)
        assert "75" in result
        assert "175" in result

    def test_none_values_excluded(self):
        payload = {
            "datos_usados": {"campo_real": "valor", "campo_nulo": None},
            "criterios": [None, "criterio real"],
            "reglas": [],
            "fuentes": [],
        }
        result = format_explanation_block(payload)
        assert "valor" in result
        assert "criterio real" in result

    def test_alternative_key_datos(self):
        payload = {
            "datos": {"objetivo": "hipertrofia"},
            "criterios": ["test"],
            "reglas": [],
            "fuentes": [],
        }
        result = format_explanation_block(payload)
        assert "hipertrofia" in result

    def test_razonamiento_included(self):
        """El nuevo campo razonamiento debe aparecer en la salida."""
        payload = {
            "datos_usados": {"objetivo": "fuerza"},
            "razonamiento": [
                "Elegí este esquema porque maximiza la fuerza neuromuscular.",
                "Se priorizaron movimientos compuestos."
            ],
            "criterios": [],
            "reglas": [],
            "fuentes": [],
        }
        result = format_explanation_block(payload)
        assert "maximiza la fuerza" in result
        assert "compuestos" in result


def _get_explanation(plan):
    """Extrae el bloque explanation del plan (esta dentro de routine_summary)."""
    return plan.get("routine_summary", {}).get("explanation") or plan.get("explanation") or {}


class TestWorkoutPlanExplanation:
    """Verificar que generate_workout_plan incluye explicacion XAI conversacional."""

    def test_plan_includes_explanation_block(self):
        plan = generate_workout_plan(
            objetivo="fuerza",
            nivel="intermedio",
            musculo="pecho",
            equipamiento="mancuernas",
            ejercicios_num=5,
            tiempo_min=45,
        )
        explanation = _get_explanation(plan)
        assert explanation, "El plan no incluye bloque 'explanation'"

    def test_explanation_has_datos_usados(self):
        plan = generate_workout_plan(
            objetivo="hipertrofia",
            nivel="principiante",
            musculo="espalda",
            equipamiento="barra",
            ejercicios_num=4,
            tiempo_min=40,
        )
        datos = _get_explanation(plan).get("datos_usados", {})
        assert datos, "datos_usados esta vacio"

    def test_explanation_has_razonamiento(self):
        """El plan debe incluir razonamiento conversacional."""
        plan = generate_workout_plan(
            objetivo="hipertrofia",
            nivel="intermedio",
            musculo="pecho",
            equipamiento="mancuernas",
            ejercicios_num=4,
            tiempo_min=45,
        )
        razonamiento = _get_explanation(plan).get("razonamiento", [])
        assert len(razonamiento) > 0, "razonamiento esta vacio"
        # Debe explicar POR QUE se eligieron esos parametros
        texto_completo = " ".join(razonamiento)
        assert "serie" in texto_completo.lower(), "Debe mencionar series"
        assert "repeticion" in texto_completo.lower(), "Debe mencionar repeticiones"

    def test_explanation_has_criterios(self):
        plan = generate_workout_plan(
            objetivo="fuerza",
            nivel="avanzado",
            musculo="piernas",
            equipamiento="barra",
            ejercicios_num=6,
            tiempo_min=60,
        )
        criterios = _get_explanation(plan).get("criterios", [])
        assert len(criterios) > 0, "criterios esta vacio"

    def test_explanation_has_fuentes(self):
        plan = generate_workout_plan(
            objetivo="fuerza",
            nivel="intermedio",
            musculo="brazos",
            equipamiento="mancuernas",
            ejercicios_num=5,
            tiempo_min=45,
        )
        fuentes = _get_explanation(plan).get("fuentes", [])
        assert len(fuentes) > 0, "fuentes esta vacio"
        # Deben ser fuentes citables, no genericas
        texto_fuentes = " ".join(fuentes)
        assert "ExRx" in texto_fuentes or "OMS" in texto_fuentes or "NSCA" in texto_fuentes

    def test_health_condition_reflected_in_reglas(self):
        plan = generate_workout_plan(
            objetivo="fuerza",
            nivel="intermedio",
            musculo="pecho",
            equipamiento="mancuernas",
            ejercicios_num=5,
            tiempo_min=45,
            condiciones="hipertension",
        )
        reglas = _get_explanation(plan).get("reglas", [])
        assert len(reglas) > 0, "Las reglas deben reflejar que hubo evaluacion de condiciones"
        texto_reglas = " ".join(reglas)
        assert "hipertension" in texto_reglas.lower() or "presion" in texto_reglas.lower(), \
            "Las reglas deben explicar POR QUE se ajusto la intensidad"

    def test_health_condition_reflected_in_razonamiento(self):
        """El razonamiento debe explicar conversacionalmente el ajuste por salud."""
        plan = generate_workout_plan(
            objetivo="fuerza",
            nivel="intermedio",
            musculo="pecho",
            equipamiento="mancuernas",
            ejercicios_num=5,
            tiempo_min=45,
            condiciones="hipertension",
        )
        razonamiento = _get_explanation(plan).get("razonamiento", [])
        texto = " ".join(razonamiento).lower()
        assert "hipertension" in texto or "presion arterial" in texto, \
            "El razonamiento debe explicar el impacto de la hipertension"
        assert "rpe" in texto or "intensidad" in texto, \
            "Debe explicar que se redujo la intensidad"

    def test_no_conditions_explains_no_restrictions(self):
        """Sin condiciones de salud, debe indicar que no se aplicaron restricciones."""
        plan = generate_workout_plan(
            objetivo="fuerza",
            nivel="principiante",
            musculo="espalda",
            equipamiento="barra",
            ejercicios_num=3,
            tiempo_min=30,
        )
        reglas = _get_explanation(plan).get("reglas", [])
        texto = " ".join(reglas).lower()
        assert "no se reportaron" in texto or "no fue necesario" in texto

    def test_formatted_output_is_conversational(self):
        """La salida formateada debe leerse como lenguaje natural, no como lista."""
        plan = generate_workout_plan(
            objetivo="hipertrofia",
            nivel="intermedio",
            musculo="pecho",
            equipamiento="mancuernas",
            ejercicios_num=4,
            tiempo_min=45,
            condiciones="diabetes",
        )
        explanation = _get_explanation(plan)
        result = format_explanation_block(explanation)
        # No debe parecer una lista de campos (viejo formato)
        assert "Datos usados:" not in result.split("\n")[0] or "tome en cuenta" in result
        # Debe contener verbos conversacionales
        assert any(word in result.lower() for word in [
            "porque", "dado que", "considerando", "elegí", "seleccione",
            "diseñe", "recomiendo", "sugiero"
        ]), "La explicacion debe usar lenguaje conversacional"
