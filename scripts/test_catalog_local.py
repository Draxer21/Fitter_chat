from backend.food.catalog import get_catalog

c = get_catalog(path='backend/data/food_catalog.json')
items = c.all()
print('Loaded items:', len(items))
print('\nFirst 3 item names:')
for it in items[:3]:
    print('-', it.get('name'), '| kcal_100g=', it.get('energy_kcal_100g'))

print('\nFind items approx 130 kcal (30% tol):')
res = c.find_by_kcal_approx(130, tolerance_pct=30, per_serving=False)
print('Matches:', len(res))
for it in res[:5]:
    print('-', it.get('name'), it.get('energy_kcal_100g'))

print('\nFilter out allergens ["nuts"] sample:')
no_nuts = c.filter_allergens(['nuts'])
print('Remaining items after nuts filter:', len(no_nuts))
