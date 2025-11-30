import os
from backend.food.composer import compose_diet
import statistics


def avg_energy_per_item(meals):
    vals = []
    for m in meals:
        for it in m.get('items', []):
            ek = it.get('energy_kcal_100g')
            if ek:
                vals.append(ek)
    return statistics.mean(vals) if vals else 0


def avg_protein_density(meals):
    vals = []
    for m in meals:
        for it in m.get('items', []):
            p = it.get('energy_kcal_100g') and it.get('energy_kcal_100g') and it.get('kcal')
            # best-effort: use proteins_g_100g when available (composer copies energy_kcal_100g)
            # but fallback to 0
            prot = it.get('energy_kcal_100g') and 0
            vals.append(prot)
    return statistics.mean(vals) if vals else 0


def test_objective_difference():
    d_gain = compose_diet(2500, n_meals=3, catalog_path=os.path.join('backend', 'data', 'food_catalog.json'), objetivo='hipertrofia')
    d_loss = compose_diet(1800, n_meals=3, catalog_path=os.path.join('backend', 'data', 'food_catalog.json'), objetivo='bajar_grasa')

    # check that generated approximate kcal differ according to target
    assert d_gain['summary']['approx_kcal'] != d_loss['summary']['approx_kcal']

    # check that the gain diet tends to include higher kcal items on average
    gain_avg = avg_energy_per_item(d_gain['meals'])
    loss_avg = avg_energy_per_item(d_loss['meals'])
    assert gain_avg >= loss_avg
