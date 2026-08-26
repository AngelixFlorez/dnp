import pandas as pd
import json
import os
import math

def redondear_1d(valor):
    """Redondea a 1 decimal. Retorna None si no es valido."""
    if valor is None or valor == '' or valor == '-' or valor == '—':
        return None
    try:
        v = float(valor)
        if math.isnan(v) or math.isinf(v):
            return None
        return round(v, 1)
    except:
        return None

def fmt_signo(valor):
    """Formatea un valor con signo y 1 decimal. Retorna None si no es valido."""
    if valor is None or valor == '' or valor == '-' or valor == '—':
        return None
    try:
        v = float(valor)
        if math.isnan(v) or math.isinf(v):
            return None
        return round(v, 1)
    except:
        return None

def limpiar_nan(obj):
    """Reemplaza NaN/Inf por None recursivamente en estructuras anidadas."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: limpiar_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [limpiar_nan(item) for item in obj]
    return obj

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
        
    # ============================================================
    # EXTRAER DASHBOARD IDF desde la hoja "Dashboard IDF"
    # ============================================================
    print("Extrayendo datos del Dashboard IDF...")
    df_dash = pd.read_excel(archivo_excel, sheet_name='Dashboard IDF', header=None)
    
    dashboard = {}
    
    # --- Evolucion historica (rows 9-13, cols 0-5) ---
    evolucion = []
    for i in range(9, 14):
        row = df_dash.iloc[i]
        anio = int(row[0]) if pd.notna(row[0]) else None
        idf_prom = redondear_1d(row[1])
        var_pp = fmt_signo(row[2]) if str(row[2]).strip() != '-' else None
        deptos = int(row[3]) if pd.notna(row[3]) else None
        maximo = redondear_1d(row[4])
        minimo = redondear_1d(row[5])
        evolucion.append({
            "anio": anio,
            "idf_promedio": idf_prom,
            "var_pp": var_pp,
            "deptos": deptos,
            "maximo": maximo,
            "minimo": minimo
        })
    dashboard["evolucion_historica"] = evolucion
    
    # --- Distribucion por rangos (rows 9-13, cols 8-11) ---
    dist_rangos = []
    for i in range(9, 14):
        row = df_dash.iloc[i]
        nombre = str(row[8]).strip() if pd.notna(row[8]) else ""
        cantidad = int(row[9]) if pd.notna(row[9]) else 0
        pct_raw = row[10] if pd.notna(row[10]) else 0
        try:
            pct = round(float(pct_raw) * 100, 1)
        except:
            pct = 0.0
        idf_prom_r = redondear_1d(row[11])
        dist_rangos.append({
            "rango": nombre,
            "cantidad": cantidad,
            "porcentaje": pct,
            "idf_promedio": idf_prom_r
        })
    dashboard["distribucion_rangos"] = dist_rangos
    
    # --- Componente Resultados (rows 17-22, cols 0-6) ---
    comps_resultados = []
    for i in range(17, 23):
        row = df_dash.iloc[i]
        nombre = str(row[0]).strip().replace('\n', ' ') if pd.notna(row[0]) else ""
        comps_resultados.append({
            "indicador": nombre,
            "resultado_promedio": redondear_1d(row[1]),
            "calificacion_promedio": redondear_1d(row[2]),
            "resultado_anio_anterior": redondear_1d(row[3]),
            "calificacion_anio_anterior": redondear_1d(row[4]),
            "var_resultado": fmt_signo(row[5]),
            "var_calificacion": fmt_signo(row[6])
        })
    dashboard["componente_resultados"] = comps_resultados
    
    # --- Top 10 Departamentos (rows 17-26, cols 8-11) ---
    top10 = []
    for i in range(17, 27):
        row = df_dash.iloc[i]
        ranking = int(row[8]) if pd.notna(row[8]) else None
        depto = str(row[9]).strip() if pd.notna(row[9]) else ""
        idf_val = redondear_1d(row[10])
        rango = str(row[11]).strip() if pd.notna(row[11]) else ""
        if ranking is not None and depto:
            top10.append({
                "ranking": ranking,
                "departamento": depto,
                "idf": idf_val,
                "rango": rango
            })
    dashboard["top10_departamentos"] = top10
    
    # --- Componente Gestion (rows 30-34, cols 0-6) ---
    comps_gestion = []
    for i in range(30, 35):
        row = df_dash.iloc[i]
        nombre = str(row[0]).strip().replace('\n', ' ') if pd.notna(row[0]) else ""
        comps_gestion.append({
            "indicador": nombre,
            "resultado_promedio": redondear_1d(row[1]),
            "calificacion_promedio": redondear_1d(row[2]),
            "resultado_anio_anterior": redondear_1d(row[3]),
            "calificacion_anio_anterior": redondear_1d(row[4]),
            "var_resultado": fmt_signo(row[5]),
            "var_calificacion": fmt_signo(row[6])
        })
    dashboard["componente_gestion"] = comps_gestion
    
    # --- Consulta por Tipologia (rows 61-63, cols 0-5) ---
    tipologia = []
    for i in range(61, 64):
        row = df_dash.iloc[i]
        nombre = str(row[0]).strip() if pd.notna(row[0]) else ""
        idf_sel = redondear_1d(row[1])
        idf_ant = redondear_1d(row[2])
        var_val = fmt_signo(row[3])
        deptos = int(row[4]) if pd.notna(row[4]) else 0
        pct_raw = row[5] if pd.notna(row[5]) else 0
        try:
            pct = round(float(pct_raw) * 100, 1)
        except:
            pct = 0.0
        tipologia.append({
            "tipologia": nombre,
            "idf_anio_seleccionado": idf_sel,
            "idf_anio_anterior": idf_ant,
            "var_pp": var_val,
            "deptos": deptos,
            "porcentaje": pct
        })
    dashboard["tipologia"] = tipologia
    
    # --- Distribucion por tipologia (rows 61-63, cols 8-11) ---
    dist_tipologia = []
    for i in range(61, 64):
        row = df_dash.iloc[i]
        nombre = str(row[8]).strip() if pd.notna(row[8]) else ""
        deterioro = int(row[9]) if pd.notna(row[9]) else 0
        riesgo = int(row[10]) if pd.notna(row[10]) else 0
        vulnerable = int(row[11]) if pd.notna(row[11]) else 0
        dist_tipologia.append({
            "tipologia": nombre,
            "deterioro": deterioro,
            "riesgo": riesgo,
            "vulnerable": vulnerable
        })
    dashboard["distribucion_tipologia"] = dist_tipologia
    
    # --- Distribucion por categoria (rows 69-73, cols 0-7) ---
    dist_categoria = []
    for i in range(69, 74):
        row = df_dash.iloc[i]
        nombre = str(row[0]).strip() if pd.notna(row[0]) else ""
        deterioro = int(row[1]) if pd.notna(row[1]) else 0
        riesgo = int(row[2]) if pd.notna(row[2]) else 0
        vulnerable = int(row[3]) if pd.notna(row[3]) else 0
        solvente = int(row[4]) if pd.notna(row[4]) else 0
        sostenible = int(row[5]) if pd.notna(row[5]) else 0
        total = int(row[6]) if pd.notna(row[6]) else 0
        idf_prom = redondear_1d(row[7])
        dist_categoria.append({
            "categoria": nombre,
            "deterioro": deterioro,
            "riesgo": riesgo,
            "vulnerable": vulnerable,
            "solvente": solvente,
            "sostenible": sostenible,
            "total": total,
            "idf_promedio": idf_prom
        })
    dashboard["distribucion_categoria"] = dist_categoria
    
    # Agregar dashboard al JSON principal
    datos["dashboard"] = dashboard
    
    # Limpiar todos los NaN/Inf del JSON antes de guardar
    datos = limpiar_nan(datos)
    print(f"Dashboard IDF extraido correctamente.")
    
    # Guardar como JSON en data/datos_idf.json
    nombre_json = os.path.join("data", "datos_idf.json")
    with open(nombre_json, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)
        
    print(f"¡Exportación exitosa! Se ha guardado el archivo '{nombre_json}'.")

if __name__ == '__main__':
    clean_data()
