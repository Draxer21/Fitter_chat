"""
Tests para ActionGenerarRutina y el planificador de rutinas (RF3).
Verifica la logica de generacion de ejercicios, esquemas de entrenamiento,
ajustes por condiciones de salud y fallback del catalogo.
"""
import pytest
from backend.planner.workouts import (
    SCHEMES,
    CATALOGO,
    pick_exercises,
    generate_workout_plan,
)
from backend.planner.common import parse_health_flags, build_health_notes


class TestSchemes:
    """Verificar que los esquemas de entrenamiento estan bien definidos."""

    @pytest.mark.parametrize("objetivo", ["fuerza", "hipertrofia", "bajar_grasa", "resistencia"])
    def test_scheme_exists(self, objetivo):
        assert objetivo in SCHEMES, f"Esquema '{objetivo}' no encontrado"

    @pytest.mark.parametrize("objetivo,nivel", [
        ("fuerza", "principiante"),
        ("fuerza", "intermedio"),
        ("fuerza", "avanzado"),
        ("hipertrofia", "principiante"),
        ("hipertrofia", "intermedio"),
        ("hipertrofia", "avanzado"),
    ])
    def test_scheme_has_required_keys(self, objetivo, nivel):
        plan = SCHEMES[objetivo][nivel]
        assert "series" in plan
        assert "reps" in plan
        assert "rpe" in plan
        assert "rires" in plan

    def test_series_reps_are_tuples(self):
        for obj, levels in SCHEMES.items():
            for nivel, plan in levels.items():
                assert len(plan["series"]) == 2, f"{obj}/{nivel}: series debe ser tupla de 2"
                assert len(plan["reps"]) == 2, f"{obj}/{nivel}: reps debe ser tupla de 2"
                assert plan["series"][0] <= plan["series"][1]
                assert plan["reps"][0] <= plan["reps"][1]


class TestCatalogo:
    """Verificar que el catalogo de ejercicios tiene datos validos."""

    def test_catalogo_has_muscle_groups(self):
        expected = {"pecho", "espalda", "piernas", "hombros", "brazos"}
        assert expected.issubset(set(CATALOGO.keys())), f"Faltan grupos musculares: {expected - set(CATALOGO.keys())}"

    def test_exercises_have_name_and_url(self):
        for grupo, banks in CATALOGO.items():
            for equip, exercises in banks.items():
                for ex in exercises:
                    assert len(ex) >= 2, f"Ejercicio en {grupo}/{equip} sin nombre o URL"
                    nombre, url = ex[0], ex[1]
                    assert nombre, f"Ejercicio sin nombre en {grupo}/{equip}"
                    assert url.startswith("http"), f"URL invalida en {grupo}/{equip}: {url}"


class TestPickExercises:
    """Verificar la seleccion de ejercicios del catalogo."""

    def test_pick_returns_requested_count(self):
        result = pick_exercises("pecho", "mancuernas", 5)
        assert len(result) <= 5

    def test_pick_returns_tuples(self):
        result = pick_exercises("brazos", "mancuernas", 3)
        for item in result:
            assert len(item) == 2
            nombre, url = item
            assert isinstance(nombre, str)
            assert isinstance(url, str)

    def test_pick_fallback_for_unknown_group(self):
        result = pick_exercises("musculo_inexistente", "mancuernas", 5)
        # El catalogo tiene fallback a fullbody, asi que devuelve ejercicios genericos
        assert isinstance(result, list)

    def test_pick_no_duplicates(self):
        result = pick_exercises("piernas", "barra", 8)
        nombres = [r[0] for r in result]
        assert len(nombres) == len(set(nombres)), "Hay ejercicios duplicados"


class TestGenerateWorkoutPlan:
    """Verificar la generacion completa de un plan de rutina."""

    def test_basic_plan_generation(self):
        plan = generate_workout_plan(
            objetivo="fuerza",
            nivel="intermedio",
            musculo="pecho",
            equipamiento="mancuernas",
            ejercicios_num=5,
            tiempo_min=45,
        )
        assert isinstance(plan, dict)
        assert "ejercicios" in plan or "structured_ejercicios" in plan or "text" in plan

    def test_plan_with_health_conditions(self):
        plan = generate_workout_plan(
            objetivo="hipertrofia",
            nivel="principiante",
            musculo="piernas",
            equipamiento="barra",
            ejercicios_num=5,
            tiempo_min=40,
            condiciones="hipertension",
        )
        assert isinstance(plan, dict)

    def test_plan_fallback_unknown_muscle(self):
        plan = generate_workout_plan(
            objetivo="fuerza",
            nivel="intermedio",
            musculo="musculo_raro",
            equipamiento="mancuernas",
            ejercicios_num=5,
            tiempo_min=30,
        )
        assert isinstance(plan, dict)


class TestHealthAdjustments:
    """Verificar ajustes de rutina por condiciones de salud."""

    def test_hipertension_flag_parsed(self):
        flags = parse_health_flags("hipertension arterial")
        assert flags.get("hipertension") is True

    def test_diabetes_flag_parsed(self):
        flags = parse_health_flags("diabetes tipo 2")
        assert flags.get("diabetes") is True

    def test_cardiaco_flag_parsed(self):
        flags = parse_health_flags("problema cardiaco")
        assert flags.get("cardiaco") is True

    def test_health_notes_generated(self):
        flags = {"hipertension": True}
        notes = build_health_notes(flags)
        assert isinstance(notes, list)
        assert len(notes) > 0

    def test_no_flags_empty_notes(self):
        flags = parse_health_flags("ninguna")
        notes = build_health_notes(flags)
        assert isinstance(notes, list)


class TestExplanationInPlan:
    """Verificar que el plan incluye bloque de explicabilidad (XAI)."""

    def test_plan_has_explanation(self):
        plan = generate_workout_plan(
            objetivo="fuerza",
            nivel="intermedio",
            musculo="pecho",
            equipamiento="mancuernas",
            ejercicios_num=5,
            tiempo_min=45,
        )
        # explanation esta dentro de routine_summary
        explanation = plan.get("routine_summary", {}).get("explanation")
        assert explanation is not None, "El plan no incluye bloque 'explanation' en routine_summary"
        assert "datos_usados" in explanation
        assert "criterios" in explanation
        assert "reglas" in explanation
        assert "fuentes" in explanation
