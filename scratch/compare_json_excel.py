import json
import re

with open('data/datos_idf.json', 'r', encoding='utf-8') as f:
    djson = json.load(f)

print("=== ESTRUCTURA DE DATOS_IDF.JSON ===")
print("Keys:", djson.keys())

# Let's inspect meta
print("Meta:", djson['meta'])

# Let's inspect a record
sample_depto = list(djson['records']['2024'].keys())[0]
print(f"\nCampos en records['2024']['{sample_depto}']:")
rec = djson['records']['2024'][sample_depto]
for k, v in rec.items():
    print(f"  {k}: {type(v).__name__} = {repr(v)[:50]}")

# Let's compare values between records['2024'][sample_depto] and Excel sheet 'IDF 20-24 con variables'
import pandas as pd
excel_path = 'Desempeño Fiscal departamentos 2020-2024.xlsx'
df = pd.read_excel(excel_path, sheet_name='IDF 20-24 con variables', header=3)
df.columns = df.columns.astype(str).str.strip()
df_clean = df.dropna(subset=['Departamento', 'Año']).copy()
df_clean['Año'] = df_clean['Año'].astype(int)
df_clean['Departamento'] = df_clean['Departamento'].astype(str).str.strip().str.upper()

row_excel = df_clean[(df_clean['Año'] == 2024) & (df_clean['Departamento'] == sample_depto)]
print(f"\nVerificación de correspondencia para {sample_depto} en 2024:")
if not row_excel.empty:
    r = row_excel.iloc[0]
    print(f"  Excel IDF: {r['Nuevo IDF']} | JSON IDF: {rec.get('idf')}")
    print(f"  Excel Rango: {r['Rango']} | JSON Rango: {rec.get('rango')}")
    print(f"  Excel Ranking: {r['Ranking nacional']} | JSON Ranking: {rec.get('ranking')}")
    print(f"  Excel Categoria: {r['Categorías']} | JSON Categoria: {rec.get('categoria')}")
    print(f"  Excel Tipologia: {r['Tipologías']} | JSON Tipologia: {rec.get('tipologia')}")
    print(f"  Excel Region: {r['Región']} | JSON Region: {rec.get('region')}")

# What else is in records? Let's check variables and dimensions
print("\nSubestructuras en rec:")
for sub in ['dimensiones', 'variables', 'insumos', 'componentes', 'gestion', 'resultados']:
    if sub in rec:
        print(f"  Subkey '{sub}':", rec[sub])

# Now let's check index.html for all accesses to idfData
with open('index.html', 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

# Let's find all idfData accesses
print("\n=== ACCESOS A idfData EN INDEX.HTML ===")
accesses = set(re.findall(r'idfData\.([a-zA-Z0-9_\.\[\]]+)', html))
for a in sorted(accesses):
    print("  idfData." + a)
