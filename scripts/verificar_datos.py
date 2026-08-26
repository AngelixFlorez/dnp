import json
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('data/datos_idf.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
print('=== Verificacion final ===')
print()
print('1. Evolucion historica:')
for item in data['dashboard']['evolucion_historica']:
    anio = item['anio']
    idf = item['idf_promedio']
    var = item['var_pp']
    mx = item['maximo']
    mn = item['minimo']
    print(f'   {anio}: IDF={idf} | Var={var} | Max={mx} | Min={mn}')
print()
print('2. Distribucion rangos:')
for item in data['dashboard']['distribucion_rangos']:
    rango = item['rango']
    cant = item['cantidad']
    pct = item['porcentaje']
    idf_prom = item['idf_promedio']
    print(f'   {rango}: cant={cant} | %={pct} | IDF prom={idf_prom}')
print()
print('3. Top 10 departamentos:')
for item in data['dashboard']['top10_departamentos']:
    rank = item['ranking']
    depto = item['departamento']
    idf = item['idf']
    rango = item['rango']
    print(f'   #{rank} {depto}: IDF={idf} | {rango}')
print()
print('4. Componente resultados (primer item):')
cr = data['dashboard']['componente_resultados'][0]
print(f'   {cr["indicador"]}: ResProm={cr["resultado_promedio"]} | CalifProm={cr["calificacion_promedio"]}')
print()
print('5. Distribucion categoria (primer item):')
dc = data['dashboard']['distribucion_categoria'][0]
print(f'   {dc["categoria"]}: Det={dc["deterioro"]} | Ries={dc["riesgo"]} | Vuln={dc["vulnerable"]} | Solv={dc["solvente"]} | Sost={dc["sostenible"]} | Total={dc["total"]} | IDF={dc["idf_promedio"]}')
