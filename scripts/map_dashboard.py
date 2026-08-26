import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_excel('Desempeño Fiscal departamentos 2020-2024.xlsx', sheet_name='Dashboard IDF', header=None)

print('=== PARAMETROS (rows 4-5) ===')
for i in [4, 5]:
    row = df.iloc[i]
    vals = []
    for j in range(12):
        v = row[j]
        if pd.notna(v):
            vals.append(f'col{j}={v}')
    print(f'  Row {i}: {vals}')

print('\n=== EVOLUCION HISTORICA (rows 8-13, cols 0-5) ===')
for i in range(8, 14):
    row = df.iloc[i]
    vals = [str(row[j])[:25] if pd.notna(row[j]) else '-' for j in range(6)]
    print(f'  Row {i}: {vals}')

print('\n=== DISTRIBUCION POR RANGOS (rows 8-13, cols 8-11) ===')
for i in range(8, 14):
    row = df.iloc[i]
    vals = [str(row[j])[:30] if pd.notna(row[j]) else '-' for j in range(8, 12)]
    print(f'  Row {i}: {vals}')

print('\n=== COMPONENTE RESULTADOS (rows 15-22, cols 0-7) ===')
for i in range(15, 23):
    row = df.iloc[i]
    vals = [str(row[j])[:35] if pd.notna(row[j]) else '-' for j in range(8)]
    print(f'  Row {i}: {vals}')

print('\n=== TOP 10 DEPARTAMENTOS (rows 15-26, cols 8-11) ===')
for i in range(15, 27):
    row = df.iloc[i]
    vals = [str(row[j])[:30] if pd.notna(row[j]) else '-' for j in range(8, 12)]
    print(f'  Row {i}: {vals}')

print('\n=== COMPONENTE GESTION (rows 28-34, cols 0-7) ===')
for i in range(28, 35):
    row = df.iloc[i]
    vals = [str(row[j])[:35] if pd.notna(row[j]) else '-' for j in range(8)]
    print(f'  Row {i}: {vals}')

print('\n=== TIPologia (rows 57-65, cols 0-6) ===')
for i in range(57, 66):
    row = df.iloc[i]
    vals = [str(row[j])[:30] if pd.notna(row[j]) else '-' for j in range(7)]
    print(f'  Row {i}: {vals}')

print('\n=== DISTRIBUCION x TIPOLOGIA (rows 59-64, cols 8-11) ===')
for i in range(59, 65):
    row = df.iloc[i]
    vals = [str(row[j])[:25] if pd.notna(row[j]) else '-' for j in range(8, 12)]
    print(f'  Row {i}: {vals}')

print('\n=== CATEGORIA x RANGO (rows 67-74, cols 0-7) ===')
for i in range(67, 75):
    row = df.iloc[i]
    vals = [str(row[j])[:25] if pd.notna(row[j]) else '-' for j in range(8)]
    print(f'  Row {i}: {vals}')

print('\n=== CONSULTA HISTORICA (rows 78-86, cols 0-7) ===')
for i in range(78, 87):
    row = df.iloc[i]
    vals = [str(row[j])[:30] if pd.notna(row[j]) else '-' for j in range(8)]
    print(f'  Row {i}: {vals}')
