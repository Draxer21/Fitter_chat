import os
from backend.food.composer import compose_diet


def test_objective_difference():
    d_gain = compose_diet(
        2500,
        n_meals=3,
        catalog_path=os.path.join("backend", "data", "food_catalog.json"),
        objetivo="hipertrofia",
    )
    d_loss = compose_diet(
        1800,
        n_meals=3,
        catalog_path=os.path.join("backend", "data", "food_catalog.json"),
        objetivo="bajar_grasa",
    )

    gain_kcal = float(d_gain["summary"]["approx_kcal"])
    loss_kcal = float(d_loss["summary"]["approx_kcal"])

    # Invariante real: mas target => mas kcal aproximadas
    assert gain_kcal > loss_kcal

    # Invariante real: aproximacion razonable al objetivo (ajusta si tu composer es mas/menos estricto)
    assert abs(gain_kcal - 2500) / 2500 <= 0.35
    assert abs(loss_kcal - 1800) / 1800 <= 0.35

    # Sanity minima: el composer puede agregar colacion/snack para cuadrar kcal
    assert len(d_gain["meals"]) >= 3
    assert len(d_loss["meals"]) >= 3
    assert len(d_gain["meals"]) <= 5
    assert len(d_loss["meals"]) <= 5
    assert any(m.get("items") for m in d_gain["meals"])
    assert any(m.get("items") for m in d_loss["meals"])
