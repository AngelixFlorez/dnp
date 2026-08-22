import pandas as pd
import json

# 1. Definir el nombre del archivo
archivo_excel = r"C:\Users\PC\Downloads\Desempeño Fiscal departamentos 2020-2024.xlsx"

# 2. Leer la hoja específica que contiene los códigos DIVIPOLA y saltar las tres primeras filas (que son encabezados combinados)
print("Leyendo el archivo Excel...")
df = pd.read_excel(archivo_excel, sheet_name='IDF 20-24 con variables', header=3)

# Limpiar espacios en blanco en los nombres de las columnas
df.columns = df.columns.astype(str).str.strip()

# 3. Seleccionar únicamente las columnas de códigos y nombre del departamento
columnas_deseadas = {
    'Código (5 digitos)': 'DIVIPOLA_5',
    'Código (2 digitos)': 'DIVIPOLA_2',
    'Departamento': 'Departamento'
}

# Filtrar el dataframe y renombrar las columnas
df_mapa = df[list(columnas_deseadas.keys())].rename(columns=columnas_deseadas)

# 4. Limpiar datos y obtener registros únicos por departamento
df_mapa = df_mapa.dropna(subset=['Departamento']).drop_duplicates(subset=['Departamento'])

# Función para formatear códigos de DIVIPOLA manteniendo ceros a la izquierda
def formatear_codigo(val, longitud):
    if pd.isna(val) or val == '' or str(val).strip() == '':
        return None
    try:
        return str(int(float(val))).zfill(longitud)
    except (ValueError, TypeError):
        return str(val).strip().zfill(longitud)

# Formatear códigos de 5 y 2 dígitos
df_mapa['DIVIPOLA_5'] = df_mapa['DIVIPOLA_5'].apply(lambda x: formatear_codigo(x, 5))
df_mapa['DIVIPOLA_2'] = df_mapa['DIVIPOLA_2'].apply(lambda x: formatear_codigo(x, 2))

# 5. Transformar a estructura JSON (diccionario por departamento)
datos_finales = {}

for index, row in df_mapa.iterrows():
    # Dar prioridad al código de 5 dígitos; si no existe, usar el de 2 dígitos
    codigo_clave = row['DIVIPOLA_5'] if row['DIVIPOLA_5'] else row['DIVIPOLA_2']
    
    datos_finales[codigo_clave] = {
        "Departamento": row['Departamento'],
        "Cod_5_digitos": row['DIVIPOLA_5'],
        "Cod_2_digitos": row['DIVIPOLA_2']
    }

# 6. Exportar a JSON
nombre_json = 'cod_dep.json'
with open(nombre_json, 'w', encoding='utf-8') as f:
    json.dump(datos_finales, f, ensure_ascii=False, indent=4)

print(f"¡Proceso completado! Se ha generado el archivo '{nombre_json}'.")
print("Muestra de los datos procesados (primeros 2 departamentos):")
print(json.dumps(dict(list(datos_finales.items())[:2]), indent=4, ensure_ascii=False))