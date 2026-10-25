"""
Servicios de consulta analítica sobre la base de datos SQLite del IDF Departamental.
Provee funciones para cada endpoint de la API REST.
"""

from typing import Dict, Any, List, Optional
from api.database import get_db

def _clean_val(val, decimals: Optional[int] = None):
    """Limpia y opcionalmente redondea valores numéricos para serialización JSON."""
    if val is None:
        return None
    try:
        f = float(val)
        if decimals is not None:
            return round(f, decimals)
        return f
    except (ValueError, TypeError):
        return val


def get_metadata() -> Dict[str, Any]:
    """Retorna los catálogos maestros fijos: años, departamentos y rangos de desempeño."""
    with get_db() as conn:
        anios = [
            r['anio'] for r in conn.execute(
                "SELECT anio FROM vigencia_fiscal ORDER BY anio"
            ).fetchall()
        ]
        
        deptos = conn.execute(
            """
            SELECT 
                codigo_divipola_2 AS divipola_2,
                codigo_divipola_5 AS divipola_5,
                nombre,
                nombre_visual,
                region
            FROM departamento
            ORDER BY nombre
            """
        ).fetchall()
        
        rangos = conn.execute(
            """
            SELECT 
                rango_id,
                codigo,
                nombre_completo,
                limite_inferior,
                limite_superior,
                color_hex,
                descripcion_cualitativa AS descripcion
            FROM catalogo_rango_desempeno
            ORDER BY rango_id
            """
        ).fetchall()
        
        return {
            "anios": anios,
            "departamentos": deptos,
            "rangos": rangos
        }


def get_instructivo_data(anio: int) -> Dict[str, Any]:
    """
    Retorna los datos para la pestaña Instructivo / Dashboard Nacional para la vigencia solicitada:
    - Evolución histórica multianual (2020–2024)
    - Ranking nacional completo del año
    - Distribución por rangos, categorías y tipologías
    """
    with get_db() as conn:
        # 1. Evolución histórica
        evolucion = conn.execute(
            """
            SELECT 
                anio,
                idf_promedio,
                idf_maximo AS maximo,
                idf_minimo AS minimo,
                deptos_evaluados AS deptos,
                var_pp_promedio AS var_pp
            FROM vw_visualizador_evolucion_nacional
            ORDER BY anio
            """
        ).fetchall()

        # 2. Ranking completo de la vigencia
        ranking = conn.execute(
            """
            SELECT 
                departamento,
                nombre_visual,
                codigo_divipola_2,
                region,
                categoria,
                tipologia,
                idf,
                ranking,
                var_pp,
                rango,
                rango_completo,
                color_hex
            FROM vw_visualizador_mapa
            WHERE anio = ?
            ORDER BY ranking
            """,
            (anio,)
        ).fetchall()

        # 3. Distribución por rangos en la vigencia
        dist_rangos = conn.execute(
            """
            SELECT 
                cr.rango_id,
                cr.codigo AS rango,
                cr.nombre_completo,
                cr.color_hex,
                COUNT(r.departamento_id) AS total_departamentos,
                ROUND(AVG(r.puntaje_idf_final), 2) AS idf_promedio
            FROM catalogo_rango_desempeno cr
            LEFT JOIN resultado_idf_anual r 
                   ON cr.rango_id = r.rango_id AND r.anio = ?
            GROUP BY cr.rango_id, cr.codigo, cr.nombre_completo, cr.color_hex
            ORDER BY cr.rango_id
            """,
            (anio,)
        ).fetchall()

        # 4. Distribución por categorías Ley 617
        dist_categoria = conn.execute(
            """
            SELECT 
                c.categoria_ley_617 AS categoria,
                COUNT(r.departamento_id) AS total,
                ROUND(AVG(r.puntaje_idf_final), 2) AS idf_promedio,
                SUM(CASE WHEN cr.codigo = 'Deterioro' THEN 1 ELSE 0 END) AS deterioro,
                SUM(CASE WHEN cr.codigo = 'Riesgo' THEN 1 ELSE 0 END) AS riesgo,
                SUM(CASE WHEN cr.codigo = 'Vulnerable' THEN 1 ELSE 0 END) AS vulnerable,
                SUM(CASE WHEN cr.codigo = 'Solvente' THEN 1 ELSE 0 END) AS solvente,
                SUM(CASE WHEN cr.codigo = 'Sostenible' THEN 1 ELSE 0 END) AS sostenible
            FROM clasificacion_anual c
            JOIN resultado_idf_anual r 
              ON c.departamento_id = r.departamento_id AND c.anio = r.anio
            JOIN catalogo_rango_desempeno cr 
              ON r.rango_id = cr.rango_id
            WHERE c.anio = ?
            GROUP BY c.categoria_ley_617
            ORDER BY c.categoria_ley_617
            """,
            (anio,)
        ).fetchall()

        # 5. Distribución por tipologías DNP (si aplica)
        dist_tipologia = conn.execute(
            """
            SELECT 
                c.tipologia_dnp AS tipologia,
                COUNT(r.departamento_id) AS total,
                ROUND(AVG(r.puntaje_idf_final), 2) AS idf_promedio,
                SUM(CASE WHEN cr.codigo = 'Deterioro' THEN 1 ELSE 0 END) AS deterioro,
                SUM(CASE WHEN cr.codigo = 'Riesgo' THEN 1 ELSE 0 END) AS riesgo,
                SUM(CASE WHEN cr.codigo = 'Vulnerable' THEN 1 ELSE 0 END) AS vulnerable,
                SUM(CASE WHEN cr.codigo = 'Solvente' THEN 1 ELSE 0 END) AS solvente,
                SUM(CASE WHEN cr.codigo = 'Sostenible' THEN 1 ELSE 0 END) AS sostenible
            FROM clasificacion_anual c
            JOIN resultado_idf_anual r 
              ON c.departamento_id = r.departamento_id AND c.anio = r.anio
            JOIN catalogo_rango_desempeno cr 
              ON r.rango_id = cr.rango_id
            WHERE c.anio = ? AND c.tipologia_dnp IS NOT NULL
            GROUP BY c.tipologia_dnp
            ORDER BY c.tipologia_dnp
            """,
            (anio,)
        ).fetchall()

        return {
            "anio": anio,
            "evolucion_historica": evolucion,
            "ranking_nacional": ranking,
            "distribucion_rangos": dist_rangos,
            "distribucion_categoria": dist_categoria,
            "distribucion_tipologia": dist_tipologia
        }


def get_ficha_departamental(departamento: str, anio: int) -> Optional[Dict[str, Any]]:
    """
    Retorna la ficha técnica integral de un departamento para un año específico,
    junto con la serie histórica de sus indicadores clave (2020 a 2024).
    """
    dept_norm = departamento.strip().upper()
    with get_db() as conn:
        # Fila de la vista
        row = conn.execute(
            """
            SELECT * FROM vw_visualizador_ficha
            WHERE (
                UPPER(departamento) = ? 
                OR UPPER(nombre_visual) = ? 
                OR codigo_divipola_2 = ?
            ) AND anio = ?
            """,
            (dept_norm, dept_norm, dept_norm, anio)
        ).fetchone()

        if not row:
            return None

        # Serie histórica de este departamento (2020 a 2024)
        historico = conn.execute(
            """
            SELECT 
                r.anio,
                r.puntaje_idf_final AS idf,
                r.puntaje_idf_sin_bonos AS idf_sin_bonos,
                r.ranking_nacional AS ranking,
                r.variacion_puntos_porcentuales AS var_pp,
                cr.codigo AS rango,
                cr.color_hex,
                res.puntaje_subtotal_resultados AS resultados_score,
                ges.puntaje_gestion_con_bonos AS gestion_score
            FROM resultado_idf_anual r
            JOIN catalogo_rango_desempeno cr ON r.rango_id = cr.rango_id
            JOIN evaluacion_resultados_fiscales res 
              ON r.departamento_id = res.departamento_id AND r.anio = res.anio
            JOIN evaluacion_gestion_territorial ges 
              ON r.departamento_id = ges.departamento_id AND r.anio = ges.anio
            WHERE r.departamento_id = ?
            ORDER BY r.anio
            """,
            (row['codigo_divipola_2'],)
        ).fetchall()

        # Estructuramos la respuesta jerárquicamente
        return {
            "identificacion": {
                "codigo_divipola_2": row['codigo_divipola_2'],
                "codigo_divipola_5": row['codigo_divipola_5'],
                "departamento": row['departamento'],
                "nombre_visual": row['nombre_visual'],
                "region": row['region'],
                "categoria": row['categoria'],
                "tipologia": row['tipologia'],
                "anio": row['anio']
            },
            "idf": {
                "puntaje_final": row['idf'],
                "puntaje_sin_bonos": row['idf_sin_bonos'],
                "ranking": row['ranking'],
                "var_pp": row['var_pp'],
                "rango": row['rango'],
                "rango_completo": row['rango_completo'],
                "color_hex": row['color_hex']
            },
            "resultados_fiscales": {
                "score": row['resultados_score'],
                "aporte_al_idf": row['resultados_aporte'],
                "indicadores": {
                    "dependencia_transferencias": {
                        "resultado": row['dep_transf_resultado'],
                        "calificacion": row['dep_transf_calificacion']
                    },
                    "relevancia_fbkf": {
                        "resultado": row['relevancia_fbkf_resultado'],
                        "calificacion": row['relevancia_fbkf_calificacion']
                    },
                    "endeudamiento": {
                        "resultado": row['endeudamiento_resultado'],
                        "calificacion": row['endeudamiento_calificacion']
                    },
                    "ahorro_corriente": {
                        "resultado": row['ahorro_corriente_resultado'],
                        "calificacion": row['ahorro_corriente_calificacion']
                    },
                    "balance_fiscal_primario": {
                        "resultado": row['balance_primario_resultado'],
                        "calificacion": row['balance_primario_calificacion']
                    }
                }
            },
            "gestion_territorial": {
                "score": row['gestion_score'],
                "aporte_al_idf": row['gestion_aporte'],
                "indicadores": {
                    "holgura": {
                        "resultado": row['holgura_resultado'],
                        "promedio_categoria": row['holgura_promedio_categoria'],
                        "calificacion": row['holgura_calificacion']
                    },
                    "capacidad_programacion_recaudo": {
                        "resultado": row['cap_prog_recaudo_resultado'],
                        "calificacion": row['cap_prog_recaudo_calificacion']
                    },
                    "capacidad_ejecucion_inversion": {
                        "resultado": row['cap_ejec_inversion_resultado'],
                        "calificacion": row['cap_ejec_inversion_calificacion']
                    },
                    "bonificacion_esfuerzo_propio": {
                        "resultado": row['bonificacion_esfuerzo_propio'],
                        "calificacion": row['bonificacion_esfuerzo_propio']
                    }
                }
            },
            "insumos_presupuestales_cuipo": {
                "ingresos_tributarios_a1000": row['ingresos_tributarios_a1000'],
                "ingresos_no_tributarios_a2000": row['ingresos_no_tributarios_a2000'],
                "transferencias_corrientes_a3010": row['transferencias_corrientes_a3010'],
                "transferencias_nacionales_d1000": row['transferencias_nacionales_d1000'],
                "ingresos_totales_a": row['ingresos_totales_a'],
                "ingresos_corrientes_ao": row['ingresos_corrientes_ao'],
                "ahorro_corriente_c": row['ahorro_corriente_c'],
                "gasto_inversion_e": row['gasto_inversion_e'],
                "gasto_fbkf": row['gasto_fbkf'],
                "activos_totales": row['activos_totales'],
                "pasivos_totales": row['pasivos_totales'],
                "gastos_funcionamiento_icld": row['gastos_funcionamiento_icld'],
                "limite_ley_617": row['limite_ley_617'],
                "presupuesto_inicial": row['presupuesto_inicial'],
                "recaudo_efectivo": row['recaudo_efectivo'],
                "compromisos_inversion": row['compromisos_inversion'],
                "pagos_inversion": row['pagos_inversion']
            },
            "historico_departamental": historico
        }


def get_consolidado_data(departamento: str, anio: int) -> Optional[Dict[str, Any]]:
    """
    Retorna la comparación de un departamento contra sus grupos de referencia:
    - Promedio Nacional
    - Promedio de su Categoría Ley 617
    - Promedio de su Tipología DNP (si aplica)
    Calcula brechas cuantitativas para cada indicador.
    """
    dept_norm = departamento.strip().upper()
    with get_db() as conn:
        # Registro del departamento
        depto_row = conn.execute(
            """
            SELECT * FROM vw_visualizador_ficha
            WHERE (
                UPPER(departamento) = ? 
                OR UPPER(nombre_visual) = ? 
                OR codigo_divipola_2 = ?
            ) AND anio = ?
            """,
            (dept_norm, dept_norm, dept_norm, anio)
        ).fetchone()

        if not depto_row:
            return None

        categoria = depto_row['categoria']
        tipologia = depto_row['tipologia']

        # Promedio nacional
        sql_bench = """
            SELECT 
                ROUND(AVG(r.puntaje_idf_final), 2) AS idf,
                ROUND(AVG(res.puntaje_subtotal_resultados), 2) AS resultados_score,
                ROUND(AVG(res.dep_transf_calificacion), 2) AS dep_transf_calificacion,
                ROUND(AVG(res.relevancia_fbkf_calificacion), 2) AS relevancia_fbkf_calificacion,
                ROUND(AVG(res.endeudamiento_calificacion), 2) AS endeudamiento_calificacion,
                ROUND(AVG(res.ahorro_corriente_calificacion), 2) AS ahorro_corriente_calificacion,
                ROUND(AVG(res.balance_primario_calificacion), 2) AS balance_primario_calificacion,
                ROUND(AVG(ges.puntaje_gestion_con_bonos), 2) AS gestion_score,
                ROUND(AVG(ges.holgura_calificacion), 2) AS holgura_calificacion,
                ROUND(AVG(ges.cap_prog_recaudo_calificacion), 2) AS cap_prog_recaudo_calificacion,
                ROUND(AVG(ges.cap_ejec_inversion_calificacion), 2) AS cap_ejec_inversion_calificacion
            FROM resultado_idf_anual r
            JOIN evaluacion_resultados_fiscales res 
              ON r.departamento_id = res.departamento_id AND r.anio = res.anio
            JOIN evaluacion_gestion_territorial ges 
              ON r.departamento_id = ges.departamento_id AND r.anio = ges.anio
            JOIN clasificacion_anual c 
              ON r.departamento_id = c.departamento_id AND r.anio = c.anio
            WHERE r.anio = ?
        """

        nacional = conn.execute(sql_bench, (anio,)).fetchone()
        
        # Promedio de la categoría
        categoria_avg = conn.execute(
            sql_bench + " AND c.categoria_ley_617 = ?", 
            (anio, categoria)
        ).fetchone()

        # Promedio de la tipología
        tipologia_avg = None
        if tipologia:
            tipologia_avg = conn.execute(
                sql_bench + " AND c.tipologia_dnp = ?", 
                (anio, tipologia)
            ).fetchone()

        def calcular_brecha(val, bench):
            if val is None or bench is None:
                return None
            return round(val - bench, 2)

        # Calculamos brechas
        brechas_nacional = {
            k: calcular_brecha(depto_row.get(k), nacional.get(k))
            for k in nacional.keys() if k in depto_row
        }
        brechas_categoria = {
            k: calcular_brecha(depto_row.get(k), categoria_avg.get(k))
            for k in categoria_avg.keys() if k in depto_row
        }
        brechas_tipologia = {}
        if tipologia_avg:
            brechas_tipologia = {
                k: calcular_brecha(depto_row.get(k), tipologia_avg.get(k))
                for k in tipologia_avg.keys() if k in depto_row
            }

        return {
            "departamento": {
                "nombre": depto_row['departamento'],
                "codigo_divipola_2": depto_row['codigo_divipola_2'],
                "anio": anio,
                "categoria": categoria,
                "tipologia": tipologia,
                "valores": {k: depto_row.get(k) for k in nacional.keys() if k in depto_row}
            },
            "promedios": {
                "nacional": nacional,
                "categoria": categoria_avg,
                "tipologia": tipologia_avg
            },
            "brechas": {
                "vs_nacional": brechas_nacional,
                "vs_categoria": brechas_categoria,
                "vs_tipologia": brechas_tipologia
            }
        }


def get_distribucion_data(anio: int) -> Dict[str, Any]:
    """Retorna los datos geográficos de departamentos para renderizar el mapa coroplético."""
    with get_db() as conn:
        deptos = conn.execute(
            """
            SELECT 
                codigo_divipola_2,
                codigo_divipola_5,
                departamento,
                nombre_visual,
                region,
                categoria,
                tipologia,
                idf,
                ranking,
                var_pp,
                rango,
                rango_completo,
                color_hex
            FROM vw_visualizador_mapa
            WHERE anio = ?
            ORDER BY ranking
            """,
            (anio,)
        ).fetchall()

        resumen = conn.execute(
            """
            SELECT 
                ROUND(AVG(puntaje_idf_final), 2) AS idf_promedio,
                ROUND(MAX(puntaje_idf_final), 2) AS idf_maximo,
                ROUND(MIN(puntaje_idf_final), 2) AS idf_minimo,
                COUNT(departamento_id) AS total_deptos
            FROM resultado_idf_anual
            WHERE anio = ?
            """,
            (anio,)
        ).fetchone()

        return {
            "anio": anio,
            "resumen_nacional": resumen,
            "departamentos": deptos
        }


def get_datos_completos() -> Dict[str, Any]:
    """
    Endpoint de compatibilidad y transición rápida:
    Genera en tiempo real desde SQLite la estructura de datos que espera el visualizador frontend
    con llaves: meta, records y dashboard.
    """
    meta = get_metadata()
    anios = meta["anios"]

    records: Dict[str, Dict[str, Any]] = {str(a): {} for a in anios}

    with get_db() as conn:
        for anio in anios:
            rows = conn.execute(
                """
                SELECT * FROM vw_visualizador_ficha
                WHERE anio = ?
                """,
                (anio,)
            ).fetchall()

            for r in rows:
                dept_name = r['departamento']
                records[str(anio)][dept_name] = {
                    "departamento": dept_name,
                    "ano": anio,
                    "divipola_2": r['codigo_divipola_2'],
                    "divipola_5": r['codigo_divipola_5'],
                    "categoria": r['categoria'],
                    "tipologia": r['tipologia'],
                    "region": r['region'],
                    "idf": _clean_val(r['idf']),
                    "idf_sin_bonos": _clean_val(r['idf_sin_bonos']),
                    "rango": r['rango'],
                    "rango_completo": r['rango_completo'],
                    "ranking": r['ranking'],
                    "resultados": {
                        "score": _clean_val(r['resultados_score']),
                        "calificacion": _clean_val(r['resultados_aporte']),
                        "indicadores": {
                            "dependencia_transferencias": {
                                "nombre": "Dependencia de las transferencias",
                                "resultado": _clean_val(r['dep_transf_resultado']),
                                "calificacion": _clean_val(r['dep_transf_calificacion'])
                            },
                            "relevancia_fbkf": {
                                "nombre": "Relevancia FBKF",
                                "resultado": _clean_val(r['relevancia_fbkf_resultado']),
                                "calificacion": _clean_val(r['relevancia_fbkf_calificacion']),
                                "fbk_fijo_inversion": 100.0
                            },
                            "endeudamiento": {
                                "nombre": "Endeudamiento",
                                "resultado": _clean_val(r['endeudamiento_resultado']),
                                "calificacion": _clean_val(r['endeudamiento_calificacion'])
                            },
                            "ahorro_corriente": {
                                "nombre": "Ahorro corriente",
                                "resultado": _clean_val(r['ahorro_corriente_resultado']),
                                "calificacion": _clean_val(r['ahorro_corriente_calificacion'])
                            },
                            "balance_fiscal_primario": {
                                "nombre": "Balance fiscal primario",
                                "resultado": _clean_val(r['balance_primario_resultado']),
                                "calificacion": _clean_val(r['balance_primario_calificacion'])
                            }
                        }
                    },
                    "gestion": {
                        "score": _clean_val(r['gestion_score']),
                        "gestion_mas_bonos": _clean_val(r['gestion_score']),
                        "calificacion": _clean_val(r['gestion_aporte']),
                        "indicadores": {
                            "holgura": {
                                "nombre": "Holgura",
                                "resultado": _clean_val(r['holgura_resultado']),
                                "calificacion": _clean_val(r['holgura_calificacion']),
                                "promedio_holgura_categoria": _clean_val(r['holgura_promedio_categoria'])
                            },
                            "capacidad_programacion_recaudo": {
                                "nombre": "Capacidad de programación y recaudo de ingresos",
                                "resultado": _clean_val(r['cap_prog_recaudo_resultado']),
                                "calificacion": _clean_val(r['cap_prog_recaudo_calificacion'])
                            },
                            "capacidad_ejecucion_inversion": {
                                "nombre": "Capacidad de ejecución de inversión",
                                "resultado": _clean_val(r['cap_ejec_inversion_resultado']),
                                "calificacion": _clean_val(r['cap_ejec_inversion_calificacion'])
                            },
                            "bonificacion_esfuerzo_propio": {
                                "nombre": "Bonificación esfuerzo propio",
                                "resultado": _clean_val(r['bonificacion_esfuerzo_propio']),
                                "calificacion": _clean_val(r['bonificacion_esfuerzo_propio'])
                            }
                        }
                    },
                    "presupuesto": {
                        "ingresos_tributarios_a1000": _clean_val(r['ingresos_tributarios_a1000']),
                        "ingresos_no_tributarios_a2000": _clean_val(r['ingresos_no_tributarios_a2000']),
                        "transferencias_corrientes_nacionales_a3010": _clean_val(r['transferencias_corrientes_a3010']),
                        "transferencias_nacionales_totales_d1000": _clean_val(r['transferencias_nacionales_d1000']),
                        "ingresos_totales_a": _clean_val(r['ingresos_totales_a']),
                        "gasto_inversion": _clean_val(r['gasto_inversion_e']),
                        "gasto_fbkf": _clean_val(r['gasto_fbkf']),
                        "ingreso_corriente": _clean_val(r['ingresos_corrientes_ao']),
                        "ahorro_corriente": _clean_val(r['ahorro_corriente_c']),
                        "activos_totales": _clean_val(r['activos_totales']),
                        "pasivos_totales": _clean_val(r['pasivos_totales']),
                        "gastos_funcionamiento": _clean_val(r['gastos_funcionamiento_icld']),
                        "limite_ley_617": _clean_val(r['limite_ley_617']),
                        "presupuesto_inicial": _clean_val(r['presupuesto_inicial']),
                        "recaudo": _clean_val(r['recaudo_efectivo']),
                        "compromisos": _clean_val(r['compromisos_inversion']),
                        "pagos": _clean_val(r['pagos_inversion'])
                    }
                }

        # Generamos el dashboard nacional
        evolucion = conn.execute(
            """
            SELECT 
                anio,
                idf_promedio,
                idf_maximo AS maximo,
                idf_minimo AS minimo,
                deptos_evaluados AS deptos,
                var_pp_promedio AS var_pp
            FROM vw_visualizador_evolucion_nacional
            ORDER BY anio
            """
        ).fetchall()

        dist_rangos = conn.execute(
            """
            SELECT 
                r.anio,
                cr.codigo AS rango,
                COUNT(r.departamento_id) AS total
            FROM resultado_idf_anual r
            JOIN catalogo_rango_desempeno cr ON r.rango_id = cr.rango_id
            GROUP BY r.anio, cr.rango_id, cr.codigo
            ORDER BY r.anio, cr.rango_id
            """
        ).fetchall()

        # Reorganizamos dist_rangos por anio
        dist_rangos_dict: Dict[int, Dict[str, int]] = {a: {} for a in anios}
        for dr in dist_rangos:
            dist_rangos_dict[dr['anio']][dr['rango']] = dr['total']

        distribucion_rangos_list = []
        for anio in anios:
            d = dist_rangos_dict.get(anio, {})
            distribucion_rangos_list.append({
                "anio": anio,
                "deterioro": d.get("Deterioro", 0),
                "riesgo": d.get("Riesgo", 0),
                "vulnerable": d.get("Vulnerable", 0),
                "solvente": d.get("Solvente", 0),
                "sostenible": d.get("Sostenible", 0)
            })

        # Top 10 de 2024
        top10 = conn.execute(
            """
            SELECT 
                departamento,
                categoria,
                tipologia,
                idf,
                ranking,
                var_pp,
                rango
            FROM vw_visualizador_mapa
            WHERE anio = 2024
            ORDER BY ranking
            LIMIT 10
            """
        ).fetchall()

        # Promedios de resultados por año
        comp_resultados = conn.execute(
            """
            SELECT 
                anio,
                ROUND(AVG(dep_transf_calificacion), 2) AS dependencia_transferencias,
                ROUND(AVG(relevancia_fbkf_calificacion), 2) AS relevancia_fbkf,
                ROUND(AVG(endeudamiento_calificacion), 2) AS endeudamiento,
                ROUND(AVG(ahorro_corriente_calificacion), 2) AS ahorro_corriente,
                ROUND(AVG(balance_primario_calificacion), 2) AS balance_fiscal_primario
            FROM evaluacion_resultados_fiscales
            GROUP BY anio
            ORDER BY anio
            """
        ).fetchall()

        # Promedios de gestión por año
        comp_gestion = conn.execute(
            """
            SELECT 
                anio,
                ROUND(AVG(holgura_calificacion), 2) AS holgura,
                ROUND(AVG(cap_prog_recaudo_calificacion), 2) AS capacidad_programacion_recaudo,
                ROUND(AVG(cap_ejec_inversion_calificacion), 2) AS capacidad_ejecucion_inversion,
                ROUND(AVG(bonificacion_esfuerzo_propio), 2) AS bonificacion_esfuerzo_propio
            FROM evaluacion_gestion_territorial
            GROUP BY anio
            ORDER BY anio
            """
        ).fetchall()

        # Distribución de categorías para 2024
        dist_cat = conn.execute(
            """
            SELECT 
                c.categoria_ley_617 AS categoria,
                SUM(CASE WHEN cr.codigo = 'Deterioro' THEN 1 ELSE 0 END) AS deterioro,
                SUM(CASE WHEN cr.codigo = 'Riesgo' THEN 1 ELSE 0 END) AS riesgo,
                SUM(CASE WHEN cr.codigo = 'Vulnerable' THEN 1 ELSE 0 END) AS vulnerable,
                SUM(CASE WHEN cr.codigo = 'Solvente' THEN 1 ELSE 0 END) AS solvente,
                SUM(CASE WHEN cr.codigo = 'Sostenible' THEN 1 ELSE 0 END) AS sostenible,
                COUNT(r.departamento_id) AS total,
                ROUND(AVG(r.puntaje_idf_final), 1) AS idf_promedio
            FROM clasificacion_anual c
            JOIN resultado_idf_anual r ON c.departamento_id = r.departamento_id AND c.anio = r.anio
            JOIN catalogo_rango_desempeno cr ON r.rango_id = cr.rango_id
            WHERE c.anio = 2024
            GROUP BY c.categoria_ley_617
            ORDER BY c.categoria_ley_617
            """
        ).fetchall()

        # Distribución de tipologías para 2024
        dist_tipo = conn.execute(
            """
            SELECT 
                c.tipologia_dnp AS tipologia,
                SUM(CASE WHEN cr.codigo = 'Deterioro' THEN 1 ELSE 0 END) AS deterioro,
                SUM(CASE WHEN cr.codigo = 'Riesgo' THEN 1 ELSE 0 END) AS riesgo,
                SUM(CASE WHEN cr.codigo = 'Vulnerable' THEN 1 ELSE 0 END) AS vulnerable
            FROM clasificacion_anual c
            JOIN resultado_idf_anual r ON c.departamento_id = r.departamento_id AND c.anio = r.anio
            JOIN catalogo_rango_desempeno cr ON r.rango_id = cr.rango_id
            WHERE c.anio = 2024 AND c.tipologia_dnp IS NOT NULL
            GROUP BY c.tipologia_dnp
            ORDER BY c.tipologia_dnp
            """
        ).fetchall()

        # Metadatos simplificados de rangos para meta.rangos dict en frontend
        rangos_meta_dict = {}
        for rng in meta["rangos"]:
            rangos_meta_dict[rng['codigo']] = {
                "nombre": rng['nombre_completo'],
                "color": rng['color_hex'],
                "min": rng['limite_inferior'],
                "max": rng['limite_superior'],
                "descripcion": rng['descripcion']
            }

        deptos_meta_dict = {}
        for d in meta["departamentos"]:
            deptos_meta_dict[d['nombre']] = {
                "codigo": d['divipola_2'],
                "codigo_completo": d['divipola_5'],
                "nombre_mostrar": d['nombre_visual'],
                "region": d['region']
            }

        return {
            "meta": {
                "anios": [str(a) for a in anios],
                "departamentos": deptos_meta_dict,
                "rangos": rangos_meta_dict
            },
            "records": records,
            "dashboard": {
                "evolucion_historica": evolucion,
                "distribucion_rangos": distribucion_rangos_list,
                "componente_resultados": comp_resultados,
                "top10_departamentos": top10,
                "componente_gestion": comp_gestion,
                "distribucion_categoria": dist_cat,
                "distribucion_tipologia": dist_tipo
            }
        }
