from backend.food.catalog import get_catalog
import os

cat = get_catalog(path=os.path.join('backend','data','food_catalog.json'))
items = cat.all()

def loss_key(it):
    prot = it.get('proteins_g_100g') or 0.0
    ek = it.get('energy_kcal_100g') or 0.0
    return prot * 12.0 - ek * 0.5

sorted_items = sorted(items, key=loss_key, reverse=True)
print('Top 20 items by loss_key (prot*12 - ek*0.5):')
for it in sorted_items[:20]:
    print(it.get('name'), 'ek=', it.get('energy_kcal_100g'), 'prot=', it.get('proteins_g_100g'), 'key=', loss_key(it))

print('\nBottom 20 items by loss_key:')
for it in sorted(items, key=loss_key, reverse=True)[-20:]:
    print(it.get('name'), 'ek=', it.get('energy_kcal_100g'), 'prot=', it.get('proteins_g_100g'), 'key=', loss_key(it))
