import os
from actions.actions import calc_target_kcal_and_macros


def test_calc_basic_values():
    # given
    weight = 75.0
    height = 175.0
    age = 30
    sex = 'm'
    activity = 'moderado'
    objetivo = 'bajar_grasa'

    # when
    res = calc_target_kcal_and_macros(weight, height, age, sex, activity, objetivo)

    # then
    assert res is not None
    assert isinstance(res.get('target_kcal'), int)
    assert isinstance(res.get('proteinas_g'), int)
    assert isinstance(res.get('carbs_g'), int)
    assert isinstance(res.get('fats_g'), int)
    assert res.get('bmr') > 1000


def test_missing_data():
    # if weight or height missing, function returns note and None values
    res = calc_target_kcal_and_macros(None, None, None, None, None, 'equilibrada')
    assert res.get('target_kcal') is None
    assert 'Insuficientes datos' in (res.get('note') or '')
