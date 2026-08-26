import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/datos_idf.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

excel_data = {
    '2020': {'avg': 54.088868, 'max': 73.550686, 'min': 38.857279},
    '2021': {'avg': 57.480757, 'max': 75.965848, 'min': 40.29319},
    '2022': {'avg': 54.725204, 'max': 74.954986, 'min': 40.17105},
    '2023': {'avg': 56.601959, 'max': 73.040468, 'min': 42.08596},
    '2024': {'avg': 53.462243, 'max': 70.904288, 'min': 38.127031},
}

print('=== Comparacion: Excel vs JSON actual ===')
for year in ['2020','2021','2022','2023','2024']:
    records = data['records'].get(year, {})
    scores = [r['idf'] for r in records.values() if r.get('idf') is not None]
    json_avg = sum(scores)/len(scores) if scores else 0
    json_max = max(scores) if scores else 0
    json_min = min(scores) if scores else 0
    ex = excel_data[year]
    
    d_avg = json_avg - ex['avg']
    d_max = json_max - ex['max']
    d_min = json_min - ex['min']
    
    print(f'{year}:')
    print(f'  Promedio: Excel={ex["avg"]:.6f}  JSON={json_avg:.6f}  diff={d_avg:+.6f}')
    print(f'  Maximo:   Excel={ex["max"]:.6f}  JSON={json_max:.6f}  diff={d_max:+.6f}')
    print(f'  Minimo:   Excel={ex["min"]:.6f}  JSON={json_min:.6f}  diff={d_min:+.6f}')
