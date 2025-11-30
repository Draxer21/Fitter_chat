from backend.food.composer import compose_diet
import os

dg = compose_diet(2500, n_meals=3, catalog_path=os.path.join('backend','data','food_catalog.json'), objetivo='hipertrofia')
dl = compose_diet(1800, n_meals=3, catalog_path=os.path.join('backend','data','food_catalog.json'), objetivo='bajar_grasa')
print('GAIN approx', dg['summary']['approx_kcal'])
print('LOSS approx', dl['summary']['approx_kcal'])

def energies(d):
    out=[]
    for m in d['meals']:
        for it in m['items']:
            out.append((it.get('name'), it.get('energy_kcal_100g'), it.get('proteins_g_100g') if 'proteins_g_100g' in it else None))
    return out

print('\nGAIN items energies:')
for n,e,p in energies(dg):
    print(n, 'kcal100=', e, 'prot100=', p)
print('\nLOSS items energies:')
for n,e,p in energies(dl):
    print(n, 'kcal100=', e, 'prot100=', p)
