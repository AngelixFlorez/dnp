import openpyxl
import pandas as pd
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

excel_path = 'Desempeño Fiscal departamentos 2020-2024.xlsx'
wb = openpyxl.load_workbook(excel_path, data_only=True)

print("=== DETALLE DE TODAS LAS HOJAS ===")

for sheetname in wb.sheetnames:
    ws = wb[sheetname]
    max_r = ws.max_row
    max_c = ws.max_column
    print(f"\n==========================================")
    print(f"HOJA: '{sheetname}' | Filas: {max_r} | Columnas: {max_c}")
    print(f"==========================================")
    
    # Read with pandas to inspect headers and rows
    # Try reading first 25 rows
    df_raw = pd.read_excel(excel_path, sheet_name=sheetname, header=None, nrows=25)
    
    # Let's find where headers start
    print("Primeras 6 filas (no vacías):")
    for r in range(min(10, len(df_raw))):
        row_vals = [f"[{c}]: {str(df_raw.iloc[r, c])[:40]}" for c in range(min(15, df_raw.shape[1])) if pd.notna(df_raw.iloc[r, c])]
        if row_vals:
            print(f"  Fila {r}: {row_vals[:6]}")

    # Check non-empty row count
    # Let's see actual populated rows and columns
    df_full = pd.read_excel(excel_path, sheet_name=sheetname, header=None)
    non_empty_rows = df_full.dropna(how='all').shape[0]
    non_empty_cols = df_full.dropna(how='all', axis=1).shape[0]
    print(f"Filas no vacías: {non_empty_rows}, Columnas no vacías: {df_full.dropna(how='all', axis=1).shape[1]}")
