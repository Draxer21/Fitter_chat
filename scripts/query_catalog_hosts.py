import requests, json, sys

hosts = ['127.0.0.1', 'localhost', '192.168.1.8']
paths = ['/notifications/catalog?limit=5', '/notifications/catalog?min_kcal=100&max_kcal=200&limit=10']

for h in hosts:
    for p in paths:
        url = f'http://{h}:5000{p}'
        print('\nTrying', url)
        try:
            r = requests.get(url, timeout=5)
            print('OK', r.status_code)
            try:
                obj = r.json()
                print('Items:', len(obj.get('items', [])))
            except Exception:
                print('Non-JSON, text:', r.text[:200])
        except Exception as e:
            print('Error:', e)
