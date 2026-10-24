import pandas as pd
import numpy as np
import sys

sys.stdout.reconfigure(encoding='utf-8')
excel_path = 'Desempeño Fiscal departamentos 2020-2024.xlsx'

df_var = pd.read_excel(excel_path, sheet_name='IDF 20-24 con variables', header=3)
df_var.columns = df_var.columns.astype(str).str.strip()
df_var = df_var.dropna(subset=['Departamento', 'Año']).copy()
df_var['Año'] = df_var['Año'].astype(int)
df_var['Departamento'] = df_var['Departamento'].astype(str).str.strip().str.upper()

print("=== 1. COBERTURA DE TIPOLOGÍA POR AÑO ===")
for y in sorted(df_var['Año'].unique()):
    sub = df_var[df_var['Año'] == y]
    non_null_tip = sub['Tipologías'].dropna()
    print(f"Año {y}: {len(non_null_tip)} de {len(sub)} registros tienen Tipología. Valores:", sub['Tipologías'].unique())

print("\n=== 2. COBERTURA DE CATEGORÍA POR AÑO ===")
for y in sorted(df_var['Año'].unique()):
    sub = df_var[df_var['Año'] == y]
    non_null_cat = sub['Categorías'].dropna()
    print(f"Año {y}: {len(non_null_cat)} de {len(sub)} registros tienen Categoría. Valores:", sub['Categorías'].unique())

print("\n=== 3. COBERTURA DE REGIÓN POR AÑO ===")
for y in sorted(df_var['Año'].unique()):
    sub = df_var[df_var['Año'] == y]
    non_null_reg = sub['Región'].dropna()
    print(f"Año {y}: {len(non_null_reg)} de {len(sub)} registros tienen Región. Valores:", sub['Región'].unique())

print("\n=== 4. AUDITORIA DE NULOS EN INDICADORES CLAVE ===")
key_cols = [
    'Dependencia de las transferencias "Resultado"',
    'Relevancia FBKF "Resultado"',
    'Endeudamiento "Resultado"',
    'Ahorro corriente "Resultado"',
    'Balance Fiscal Primario "Resultado"',
    'Holgura "Resultado"',
    'Capacidad de programación y recaudo de ingresos "Resultado"',
    'Capacidad de Ejecución de Inversión "Resultado"',
    'Bonificación Esfuerzo Porpio "Calificación"',
    'Nuevo IDF'
]
for col in key_cols:
    if col in df_var.columns:
        null_count = df_var[col].isna().sum()
        print(f"Columna '{col}': {null_count} nulos de {len(df_var)}")
    else:
        print(f"Columna '{col}' NO ENCONTRADA")

print("\n=== 5. AUDITORIA DE INSUMOS FISCALES BÁSICOS (CUIPO/FUT) ===")
insumo_cols = [c for c in df_var.columns if any(term in c for term in ['A1000', 'A2000', 'A3010', 'D1000', 'INGRESOS TOTALES', 'Inversión', 'FBK', 'Activos', 'Pasivos', 'Recaudo', 'Compromisos', 'Pagos'])]
for c in insumo_cols[:15]:
    null_c = df_var[c].isna().sum()
    print(f"  '{c}': {null_c} nulos")
