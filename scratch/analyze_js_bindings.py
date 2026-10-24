import re

with open('index.html', 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

# Let's inspect each function in JS
js_blocks = re.findall(r'<script\b[^>]*>(.*?)</script>', html, re.DOTALL)
main_js = ""
for b in js_blocks:
    if "idfData" in b:
        main_js = b
        break

print(f"Longitud del script principal JS: {len(main_js)} caracteres")

# Find all occurrences where properties of d or record are accessed
# e.g., d.idf, d.rango, d.categoria, d.tipologia, d.region, d.resultados, d.gestion, d.presupuesto
pattern = r'(?:d|depto|dd|rec|record|pt|item)\.([a-zA-Z0-9_\.]+)'
matches = set(re.findall(pattern, main_js))
print("\nPropiedades de departamento/record accedidas en JS:")
for m in sorted(matches):
    print("  ." + m)

# Find all functions that populate views
pop_funcs = re.findall(r'function\s+(populate[a-zA-Z0-9_]*|refresh[a-zA-Z0-9_]*|update[a-zA-Z0-9_]*|build[a-zA-Z0-9_]*|render[a-zA-Z0-9_]*)\s*\(', main_js)
print("\nFunciones de renderizado/poblado en JS:")
for pf in set(pop_funcs):
    print("  - " + pf)

