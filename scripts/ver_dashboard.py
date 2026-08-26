import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')
df = pd.read_excel('Desempeño Fiscal departamentos 2020-2024.xlsx', sheet_name='Dashboard IDF', header=None)
print('=== Dashboard IDF completo (filas 0-35, cols 0-11) ===')
for i in range(0, 36):
    row = df.iloc[i]
    vals = []
    for j in range(min(12, len(df.columns))):
        v = row[j]
        if pd.notna(v):
            vals.append(str(v)[:40])
        else:
            vals.append('NaN')
    sep = ' | '
    print(f'Row {i:2d}: {sep.join(vals)}')
