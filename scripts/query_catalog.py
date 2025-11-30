import requests, json, sys

urls = [
    'http://127.0.0.1:5000/notifications/catalog?limit=5',
    'http://127.0.0.1:5000/notifications/catalog?min_kcal=100&max_kcal=200&limit=10'
]

for u in urls:
    print('\nQuerying:', u)
    try:
        r = requests.get(u, timeout=10)
    except Exception as e:
        print('Connection error:', e)
        sys.exit(2)
    print('Status code:', r.status_code)
    try:
        obj = r.json()
        items = obj.get('items', [])
        print('Items returned:', len(items))
        if items:
            print('First items (up to 3):')
            print(json.dumps(items[:3], ensure_ascii=False, indent=2))
    except Exception:
        print('Non-JSON response:', r.text[:1000])
