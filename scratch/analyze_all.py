import json
import os
import sys
import openpyxl
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

print("=== 1. ANALIZANDO INDEX.HTML ===")
with open('index.html', 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

import re
titles = re.findall(r'<title>(.*?)</title>', html, re.I)
print("Title:", titles)

# Find sections / views / tabs
tab_buttons = re.findall(r'<button[^>]*data-tab=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</button>', html, re.I | re.DOTALL)
print("Tabs by data-tab:", [(t[0], re.sub(r'<[^>]+>', '', t[1]).strip()) for t in tab_buttons])

# Find ids of main sections or views
views = re.findall(r'<(?:div|section)[^>]*id=[\'"]([^\'"]*(?:tab|view|section|panel|dashboard|container)[^\'"]*)[\'"]', html, re.I)
print("Main view/panel IDs (sample):", list(set(views))[:20])

# Find chart canvas or containers
charts = re.findall(r'<(?:canvas|div)[^>]*id=[\'"]([^\'"]*(?:chart|grafic|map|ranking|tabla)[^\'"]*)[\'"]', html, re.I)
print("Chart/table/map IDs:", list(set(charts)))

# Search for json keys referenced in script tags
print("\n=== 2. ANALIZANDO DATOS_IDF.JSON ===")
with open('data/datos_idf.json', 'r', encoding='utf-8') as f:
    data_json = json.load(f)

print("Top keys in datos_idf.json:", list(data_json.keys()))
for k in data_json.keys():
    v = data_json[k]
    if isinstance(v, dict):
        print(f"  {k}: dict with {len(v)} keys -> subkeys: {list(v.keys())[:5]}")
        # inspect first item
        first_k = list(v.keys())[0]
        if isinstance(v[first_k], dict):
            print(f"    Sample '{first_k}': {list(v[first_k].keys())[:10]}")
            # if nested further:
            second_k = list(v[first_k].keys())[0]
            if isinstance(v[first_k][second_k], dict):
                print(f"      Sample '{second_k}': {list(v[first_k][second_k].keys())[:10]}")
    elif isinstance(v, list):
        print(f"  {k}: list with {len(v)} items -> first item: {type(v[0]) if v else 'empty'}")

print("\n=== 3. ANALIZANDO HOJAS DE EXCEL ===")
excel_path = 'Desempeño Fiscal departamentos 2020-2024.xlsx'
xl = pd.ExcelFile(excel_path)
print("Sheets in Excel:", xl.sheet_names)

for sheet in xl.sheet_names:
    print(f"\n--- HOJA: {sheet} ---")
    df_preview = pd.read_excel(excel_path, sheet_name=sheet, nrows=10, header=None)
    print(f"Dimensiones de muestra: {df_preview.shape}")
    # Show first 5 non-empty rows
    for r in range(min(7, len(df_preview))):
        row_vals = [f"Col{c}: {str(df_preview.iloc[r, c])[:30]}" for c in range(min(10, df_preview.shape[1])) if pd.notna(df_preview.iloc[r, c])]
        if row_vals:
            print(f"  Fila {r}: {row_vals[:6]}")
