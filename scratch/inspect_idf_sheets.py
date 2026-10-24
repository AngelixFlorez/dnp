import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8')

excel_path = 'Desempeño Fiscal departamentos 2020-2024.xlsx'

print("=== HOJA: IDF 20-24 con variables ===")
df_var = pd.read_excel(excel_path, sheet_name='IDF 20-24 con variables', header=None)
print("Forma total df_var:", df_var.shape)

# Let's inspect first 5 rows to see multi-level headers
for r in range(5):
    row = df_var.iloc[r].dropna()
    print(f"Fila {r} (primeros 15 no nulos):")
    for c, val in row.items():
        if c < 20:
            print(f"  Col {c}: {val}")

# Let's see row 3 (which looks like the actual column names)
header_row_3 = df_var.iloc[3]
print("\n--- Columnas de la Fila 3 ---")
for idx, col in enumerate(header_row_3):
    f0 = df_var.iloc[0, idx] if pd.notna(df_var.iloc[0, idx]) else ""
    f1 = df_var.iloc[1, idx] if pd.notna(df_var.iloc[1, idx]) else ""
    f2 = df_var.iloc[2, idx] if pd.notna(df_var.iloc[2, idx]) else ""
    print(f"Col {idx:02d}: [{col}] | Grupo Fila 0: '{f0}' | Fila 1: '{f1}' | Fila 2: '{f2}'")

# Data rows starting at row 4
data_rows = df_var.iloc[4:].dropna(how='all')
print("\nTotal filas de datos no vacías:", len(data_rows))

# Let's see non-null 'Departamento' and 'Año'
# Col 2 is Año, Col 3 is Departamento, Col 0 is Código (2 digitos)
col_anio = data_rows[2].dropna()
print("Años encontrados:", col_anio.unique())
print("Conteo por año:")
print(col_anio.value_counts())

col_depto = data_rows[3].dropna()
print("\nDepartamentos únicos:", len(col_depto.unique()))
print(sorted(col_depto.unique()))

# Let's check IDF 20-24 Sin variables
print("\n=== HOJA: IDF 20-24 Sin variables ===")
df_sin = pd.read_excel(excel_path, sheet_name='IDF 20-24 Sin variables', header=None)
print("Forma total df_sin:", df_sin.shape)
header_sin = df_sin.iloc[3]
print("\n--- Columnas de la Fila 3 en 'Sin variables' ---")
for idx, col in enumerate(header_sin):
    f0 = df_sin.iloc[0, idx] if pd.notna(df_sin.iloc[0, idx]) else ""
    f1 = df_sin.iloc[1, idx] if pd.notna(df_sin.iloc[1, idx]) else ""
    f2 = df_sin.iloc[2, idx] if pd.notna(df_sin.iloc[2, idx]) else ""
    print(f"Col {idx:02d}: [{col}] | F0: '{f0}' | F1: '{f1}' | F2: '{f2}'")

