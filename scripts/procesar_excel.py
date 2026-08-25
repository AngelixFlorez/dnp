import pandas as pd
import json
import os

def clean_data():
    archivo_excel = "Desempeño Fiscal departamentos 2020-2024.xlsx"
    print(f"Leyendo la hoja de datos desde '{archivo_excel}'...")
    
    # Cargar la hoja 'IDF 20-24 con variables', con las columnas que empiezan en la fila 3 (header=3)
    df = pd.read_excel(archivo_excel, sheet_name='IDF 20-24 con variables', header=3)
    
    # Limpiar nombres de columnas eliminando espacios al inicio y al final
    df.columns = df.columns.astype(str).str.strip()
    
    # Filtrar registros válidos: donde Año y Departamento no sean nulos
    df_clean = df.dropna(subset=['Departamento', 'Año']).copy()
    
    # Asegurar que el año sea un entero y departamento esté en mayúsculas
    df_clean['Año'] = df_clean['Año'].astype(int)
    df_clean['Departamento'] = df_clean['Departamento'].astype(str).str.strip().str.upper()
    
    # Formatear códigos DIVIPOLA a string con ceros a la izquierda
    def pad_code(val, length):
        if pd.isna(val) or val == '':
            return ""
        try:
            return str(int(float(val))).zfill(length)
        except:
            return str(val).strip().zfill(length)
            
    df_clean['DIVIPOLA_2'] = df_clean['Código (2 digitos)'].apply(lambda x: pad_code(x, 2))
    df_clean['DIVIPOLA_5'] = df_clean['Código (5 digitos)'].apply(lambda x: pad_code(x, 5))
    
    print(f"Se encontraron {len(df_clean)} registros limpios de departamentos.")
    
    # Crear estructura jerárquica para el JSON
    # Años disponibles
    anios = sorted(df_clean['Año'].unique())
    # Lista de departamentos únicos
    departamentos_unicos = sorted(df_clean['Departamento'].unique())
    
    # Crear el diccionario de datos
    datos = {
        "meta": {
            "anios": [str(a) for a in anios],
            "departamentos": departamentos_unicos,
            "rangos": {
                "Deterioro": {"min": 0, "max": 40, "nombre": "Deterioro (<40)", "color": "#fd0200"},
                "Riesgo": {"min": 40, "max": 60, "nombre": "Riesgo (>=40 y <60)", "color": "#fddd00"},
                "Vulnerable": {"min": 60, "max": 70, "nombre": "Vulnerable (>=60 y <70)", "color": "#2476c5"},
                "Solvente": {"min": 70, "max": 80, "nombre": "Solvente (>=70 y <80)", "color": "#0046b1"},
                "Sostenible": {"min": 80, "max": 100, "nombre": "Sostenible (>=80)", "color": "#0e7c66"}
            }
        },
        "records": {}
    }
    
    for _, row in df_clean.iterrows():
        anio = str(row['Año'])
        depto = row['Departamento']
        
        if anio not in datos['records']:
            datos['records'][anio] = {}
            
        # Determinar el rango de forma limpia
        rango_crudo = str(row['Rango']).strip() if pd.notna(row['Rango']) else "Sin rango"
        # Mapear los rangos a nombres limpios
        rango_limpio = "Riesgo"
        if "Deterioro" in rango_crudo or (pd.notna(row['Nuevo IDF']) and row['Nuevo IDF'] < 40):
            rango_limpio = "Deterioro"
        elif "Riesgo" in rango_crudo:
            rango_limpio = "Riesgo"
        elif "Vulnerable" in rango_crudo:
            rango_limpio = "Vulnerable"
        elif "Solvente" in rango_crudo:
            rango_limpio = "Solvente"
        elif "Sostenible" in rango_crudo or (pd.notna(row['Nuevo IDF']) and row['Nuevo IDF'] >= 80):
            rango_limpio = "Sostenible"
            
        # Construir record detallado
        datos['records'][anio][depto] = {
            "departamento": depto,
            "ano": row['Año'],
            "divipola_2": row['DIVIPOLA_2'],
            "divipola_5": row['DIVIPOLA_5'],
            "categoria": str(row['Categorías']).strip() if pd.notna(row['Categorías']) else "N/A",
            "tipologia": str(row['Tipologías']).strip() if pd.notna(row['Tipologías']) else "N/A",
            "region": str(row['Región']).strip() if pd.notna(row['Región']) else "N/A",
            
            # Puntaje final e indicadores agregados
            "idf": float(row['Nuevo IDF']) if pd.notna(row['Nuevo IDF']) else 0.0,
            "idf_sin_bonos": float(row['Nuevo IDF (sin bonos)']) if pd.notna(row['Nuevo IDF (sin bonos)']) else 0.0,
            "rango": rango_limpio,
            "rango_completo": rango_crudo,
            "ranking": int(row['Ranking nacional']) if pd.notna(row['Ranking nacional']) else 0,
            
            # Dimensión Resultados (Peso 80%)
            "resultados": {
                "score": float(row['Resultados']) if pd.notna(row['Resultados']) else 0.0,
                "calificacion": float(row['Calificación Resultados']) if pd.notna(row['Calificación Resultados']) else 0.0,
                "indicadores": {
                    "dependencia_transferencias": {
                        "nombre": "Dependencia de las transferencias",
                        "resultado": float(row['Dependencia de las transferencias "Resultado"']) if pd.notna(row['Dependencia de las transferencias "Resultado"']) else 0.0,
                        "calificacion": float(row['Dependencia de las transferencias "Calificación"']) if pd.notna(row['Dependencia de las transferencias "Calificación"']) else 0.0
                    },
                    "relevancia_fbkf": {
                        "nombre": "Relevancia FBKF",
                        "resultado": float(row['Relevancia FBKF "Resultado"']) if pd.notna(row['Relevancia FBKF "Resultado"']) else 0.0,
                        "calificacion": float(row['Relevancia FBKF "Resultado"']) if pd.notna(row['Relevancia FBKF "Resultado"']) else 0.0,
                        "fbk_fijo_inversion": float(row['FBK fijo/ Inversión  (Con SGR)*']) if pd.notna(row['FBK fijo/ Inversión  (Con SGR)*']) else 0.0
                    },
                    "endeudamiento": {
                        "nombre": "Endeudamiento",
                        "resultado": float(row['Endeudamiento "Resultado"']) if pd.notna(row['Endeudamiento "Resultado"']) else 0.0,
                        "calificacion": float(row['Endeudamiento "Calificación"']) if pd.notna(row['Endeudamiento "Calificación"']) else 0.0
                    },
                    "ahorro_corriente": {
                        "nombre": "Ahorro corriente",
                        "resultado": float(row['Ahorro corriente "Resultado"']) if pd.notna(row['Ahorro corriente "Resultado"']) else 0.0,
                        "calificacion": float(row['Ahorro corriente "Calificación"']) if pd.notna(row['Ahorro corriente "Calificación"']) else 0.0
                    },
                    "balance_fiscal_primario": {
                        "nombre": "Balance fiscal primario",
                        "resultado": float(row['Balance Fiscal Primario "Resultado"']) if pd.notna(row['Balance Fiscal Primario "Resultado"']) else 0.0,
                        "calificacion": float(row['Balance Fiscal Primario "Calificación"']) if pd.notna(row['Balance Fiscal Primario "Calificación"']) else 0.0
                    }
                }
            },
            
            # Dimensión Gestión (Peso 20% + Bonos)
            "gestion": {
                "score": float(row['Resultados Gestión']) if pd.notna(row['Resultados Gestión']) else 0.0,
                "gestion_mas_bonos": float(row['Gestión +Bonos']) if pd.notna(row['Gestión +Bonos']) else 0.0,
                "calificacion": float(row['Calificación Resultados Gestión']) if pd.notna(row['Calificación Resultados Gestión']) else 0.0,
                "indicadores": {
                    "holgura": {
                        "nombre": "Holgura",
                        "resultado": float(row['Holgura "Resultado"']) if pd.notna(row['Holgura "Resultado"']) else 0.0,
                        "calificacion": float(row['Holgura "Calificación"']) if pd.notna(row['Holgura "Calificación"']) else 0.0,
                        "promedio_holgura_categoria": float(row['Promedio Holgura por Categoría']) if pd.notna(row['Promedio Holgura por Categoría']) else 0.0
                    },
                    "capacidad_programacion_recaudo": {
                        "nombre": "Capacidad de programación y recaudo de ingresos",
                        "resultado": float(row['Capacidad de programación y recaudo de ingresos "Resultado"']) if pd.notna(row['Capacidad de programación y recaudo de ingresos "Resultado"']) else 0.0,
                        "calificacion": float(row['Capacidad de programación y recaudo de Ingresos "Calificación"']) if pd.notna(row['Capacidad de programación y recaudo de Ingresos "Calificación"']) else 0.0
                    },
                    "capacidad_ejecucion_inversion": {
                        "nombre": "Capacidad de ejecución de inversión",
                        "resultado": float(row['Capacidad de Ejecución de Inversión "Resultado"']) if pd.notna(row['Capacidad de Ejecución de Inversión "Resultado"']) else 0.0,
                        "calificacion": float(row['Capacidad de Ejecución de Inversión "Calificación"']) if pd.notna(row['Capacidad de Ejecución de Inversión "Calificación"']) else 0.0
                    },
                    "bonificacion_esfuerzo_propio": {
                        "nombre": "Bonificación esfuerzo propio",
                        "resultado": float(row['Bonificación Esfuerzo Porpio "Calificación"']) if pd.notna(row['Bonificación Esfuerzo Porpio "Calificación"']) else 0.0,
                        "calificacion": float(row['Bonificación Esfuerzo Porpio "Calificación"']) if pd.notna(row['Bonificación Esfuerzo Porpio "Calificación"']) else 0.0
                    }
                }
            },
            
            # Variables presupuestales y financieras básicas (Para la calculadora paso a paso)
            "presupuesto": {
                "ingresos_tributarios_a1000": float(row['A1000-Ingresos tributarios (No SGR']) if pd.notna(row['A1000-Ingresos tributarios (No SGR']) else 0.0,
                "ingresos_no_tributarios_a2000": float(row['A2000-Ingresos no tributarios (No SGR)']) if pd.notna(row['A2000-Ingresos no tributarios (No SGR)']) else 0.0,
                "transferencias_corrientes_nacionales_a3010": float(row['A3010-Transferencias corrientes de nivel nacional (NO tiene SGR)']) if pd.notna(row['A3010-Transferencias corrientes de nivel nacional (NO tiene SGR)']) else 0.0,
                "transferencias_nacionales_totales_d1000": float(row['D1000-Transferencias nacionales (No tiene SGR)']) if pd.notna(row['D1000-Transferencias nacionales (No tiene SGR)']) else 0.0,
                "ingresos_totales_a": float(row['A-INGRESOS TOTALES (NO SGR)']) if pd.notna(row['A-INGRESOS TOTALES (NO SGR)']) else 0.0,
                "gasto_inversion": float(row['Gasto en Inversión']) if pd.notna(row['Gasto en Inversión']) else 0.0,
                "gasto_fbkf": float(row['Gasto en Formación Bruta de Capital']) if pd.notna(row['Gasto en Formación Bruta de Capital']) else 0.0,
                "ingreso_corriente": float(row['Ingreso corriente']) if pd.notna(row['Ingreso corriente']) else 0.0,
                "ahorro_corriente": float(row['Ahorro corriente']) if pd.notna(row['Ahorro corriente']) else 0.0,
                "intereses_deuda_b2000": float(row['B2000-Intereses de la deuda pública -NO tiene SGR']) if pd.notna(row['B2000-Intereses de la deuda pública -NO tiene SGR']) else 0.0,
                "deficit_superavit_total_g": float(row['G-Déficit o Superávit Total (No Tiene SGR)']) if pd.notna(row['G-Déficit o Superávit Total (No Tiene SGR)']) else 0.0,
                "recursos_balance_cuipo": float(row['Recursos del Balance CUIPO']) if pd.notna(row['Recursos del Balance CUIPO']) else 0.0,
                "desembolsos": float(row['Desembolsos (No tiene SGR)']) if pd.notna(row['Desembolsos (No tiene SGR)']) else 0.0,
                "activos_totales": float(row['Activos totales']) if pd.notna(row['Activos totales']) else 0.0,
                "pasivos_totales": float(row['Pasivos totales']) if pd.notna(row['Pasivos totales']) else 0.0,
                "gastos_funcionamiento": float(row['Gastos de funcionamiento / ICLD']) if pd.notna(row['Gastos de funcionamiento / ICLD']) else 0.0,
                "limite_ley_617": float(row['Límite Ley 617 de 2000']) if pd.notna(row['Límite Ley 617 de 2000']) else 0.0,
                "presupuesto_inicial": float(row['Presupuesto Inicial']) if pd.notna(row['Presupuesto Inicial']) else 0.0,
                "recaudo": float(row['Recaudo']) if pd.notna(row['Recaudo']) else 0.0,
                "compromisos": float(row['Compromisos']) if pd.notna(row['Compromisos']) else 0.0,
                "pagos": float(row['Pagos']) if pd.notna(row['Pagos']) else 0.0,
                "sgp_otras_transferencias": float(row['SGP + otras transferencias nacionales']) if pd.notna(row['SGP + otras transferencias nacionales']) else 0.0,
                "ingresos_totales_calc": float(row['Ingresos totales']) if pd.notna(row['Ingresos totales']) else 0.0,
                "deficit_superavit_intereses_rb": float(row['Déficit o superávit + intereses deuda+RB']) if pd.notna(row['Déficit o superávit + intereses deuda+RB']) else 0.0,
                "ingresos_totales_desembolsos": float(row['Ingresos totales + desembolsos']) if pd.notna(row['Ingresos totales + desembolsos']) else 0.0,
            }
        }
        
    # Guardar como JSON en datos_idf.json
    nombre_json = "datos_idf.json"
    with open(nombre_json, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)
        
    print(f"¡Exportación exitosa! Se ha guardado el archivo '{nombre_json}'.")

if __name__ == '__main__':
    clean_data()
