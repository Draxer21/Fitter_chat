import json
p='backend/data/food_catalog.json'
with open(p, encoding='utf-8') as f:
    data = json.load(f)
print(f'Loaded {len(data)} items from {p}')
