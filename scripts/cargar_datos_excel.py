"""
FASE 2 — ETL Completo: Excel  →  Base de Datos SQLite IDF

Pasos cubiertos:
  2.1  Lectura de la hoja maestra 'IDF 20-24 con variables'
  2.2  Transformaciones y normalización de datos
  2.3  Inserción transaccional en las 5 tablas de hechos
  2.4  Creación de las 3 vistas analíticas

Fuente  : Desempeño Fiscal departamentos 2020-2024.xlsx
Destino : data/idf_database.db
"""

import os
import sys
import math
import sqlite3
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

# ──────────────────────────────────────────
# RUTAS
# ──────────────────────────────────────────
BASE_DIR  = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
EXCEL     = os.path.join(BASE_DIR, 'Desempeño Fiscal departamentos 2020-2024.xlsx')
DB_PATH   = os.path.join(BASE_DIR, 'data', 'idf_database.db')
SHEET     = 'IDF 20-24 con variables'


# ──────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────
def safe_float(val):
    """Convierte a float; devuelve None si es nulo, NaN o no numérico."""
    if val is None:
        return None
    try:
        f = float(val)
        return None if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return None


def safe_int(val):
    """Convierte a int; devuelve None si es nulo."""
    f = safe_float(val)
    return int(round(f)) if f is not None else None


def pad_code(val, length):
    """Formatea un código DIVIPOLA con ceros a la izquierda."""
    try:
        return str(int(float(val))).zfill(length)
    except (TypeError, ValueError):
        return None


RANGO_MAP = {
    '1. Deterioro (<40)':       (1, 'Deterioro'),
    '2. Riesgo (>=40 y <60)':   (2, 'Riesgo'),
    '3. Vulnerable (>=60 y <70)':(3, 'Vulnerable'),
    '4. Solvente (>=70 y <80)': (4, 'Solvente'),
    '5. Sostenible (>=80)':      (5, 'Sostenible'),
}

def resolver_rango_id(rango_texto, idf_val):
    """Devuelve el rango_id a partir del texto del Excel o del valor IDF."""
    txt = str(rango_texto).strip() if rango_texto else ''
    if txt in RANGO_MAP:
        return RANGO_MAP[txt][0]
    # Fallback: calcular por valor
    if idf_val is None:
        return None
    if idf_val < 40:   return 1
    if idf_val < 60:   return 2
    if idf_val < 70:   return 3
    if idf_val < 80:   return 4
    return 5


# ══════════════════════════════════════════
# PASO 2.1  Lectura de la hoja maestra
# ══════════════════════════════════════════
def paso_2_1():
    print("[2.1] Leyendo hoja maestra…")
    df = pd.read_excel(EXCEL, sheet_name=SHEET, header=3)
    df.columns = df.columns.astype(str).str.strip()

    # Conservar solo filas con Departamento y Año válidos
    df = df.dropna(subset=['Departamento', 'Año']).copy()
    df['Año'] = df['Año'].astype(int)
    df['Departamento'] = df['Departamento'].astype(str).str.strip().str.upper()

    anios  = sorted(df['Año'].unique())
    deptos = sorted(df['Departamento'].unique())
    print(f"[2.1] ✔ {len(df)} registros | {len(anios)} vigencias: {anios} | {len(deptos)} departamentos")
    return df


# ══════════════════════════════════════════
# PASO 2.2  Transformaciones por fila
# ══════════════════════════════════════════
def transformar_fila(r):
    """
    Recibe una fila del DataFrame y devuelve un dict estructurado
    listo para insertar en la BD.
    """
    anio = int(r['Año'])

    # ── Identificadores ──────────────────────────────────────────
    div2 = pad_code(r['Código (2 digitos)'], 2)
    div5 = pad_code(r['Código (5 digitos)'], 5)
    dept = str(r['Departamento']).strip().upper()

    # Normalización de nombres especiales (tilde en la clave interna)
    NOMBRE_NORM = {
        'NARIÑO':   'NARIÑO',
        'SAN ANDRÉS': 'SAN ANDRÉS',
    }
    dept = NOMBRE_NORM.get(dept, dept)

    # ── Clasificación anual ───────────────────────────────────────
    cat = str(r.get('Categorías', '')).strip()
    tip_raw = r.get('Tipologías')
    tipologia = safe_int(tip_raw)   # None para 2020-2023

    # ── Insumos CUIPO (nulos para 2020) ───────────────────────────
    # 2020 no tiene cuentas CUIPO: comprobamos si A1000 es nulo
    tiene_cuipo = safe_float(r.get("A1000-Ingresos tributarios (No SGR")) is not None

    def cuipo(col):
        return safe_float(r.get(col)) if tiene_cuipo else None

    insumos = {
        'ingresos_tributarios_a1000':      cuipo("A1000-Ingresos tributarios (No SGR"),
        'ingresos_no_tributarios_a2000':   cuipo("A2000-Ingresos no tributarios (No SGR)"),
        'transferencias_corrientes_a3010': cuipo("A3010-Transferencias corrientes de nivel nacional (NO tiene SGR)"),
        'transferencias_nacionales_d1000': cuipo("D1000-Transferencias nacionales (No tiene SGR)"),
        'ingresos_totales_a':              cuipo("A-INGRESOS TOTALES (NO SGR)"),
        'ingresos_corrientes_ao':          cuipo("Ingreso corriente"),
        'ahorro_corriente_c':              cuipo("Ahorro corriente"),
        'gasto_inversion_e':               cuipo("Gasto en Inversión"),
        'gasto_fbkf':                      cuipo("Gasto en Formación Bruta de Capital"),
        'intereses_deuda_b2000':           cuipo("B2000-Intereses de la deuda pública -NO tiene SGR"),
        'deficit_superavit_total_g':       cuipo("G-Déficit o Superávit Total (No Tiene SGR)"),
        'recursos_balance_cuipo':          cuipo("Recursos del Balance CUIPO"),
        'desembolsos_credito':             cuipo("Desembolsos (No tiene SGR)"),
        'activos_totales':                 cuipo("Activos totales"),
        'pasivos_totales':                 cuipo("Pasivos totales"),
        'gastos_funcionamiento_icld':      cuipo("Gastos de funcionamiento / ICLD"),
        'limite_ley_617':                  cuipo("Límite Ley 617 de 2000"),
        'presupuesto_inicial':             cuipo("Presupuesto Inicial"),
        'recaudo_efectivo':                cuipo("Recaudo"),
        'compromisos_inversion':           cuipo("Compromisos"),
        'pagos_inversion':                 cuipo("Pagos"),
    }

    # ── Evaluación: Dimensión Resultados (80 %) ───────────────────
    resultados = {
        'dep_transf_resultado':          safe_float(r.get('Dependencia de las transferencias "Resultado"')),
        'dep_transf_calificacion':       safe_float(r.get('Dependencia de las transferencias "Calificación"')),
        'relevancia_fbkf_resultado':     safe_float(r.get('Relevancia FBKF "Resultado"')),
        'relevancia_fbkf_calificacion':  safe_float(r.get('FBK fijo/ Inversión  (Con SGR)*')),
        'endeudamiento_resultado':       safe_float(r.get('Endeudamiento "Resultado"')),
        'endeudamiento_calificacion':    safe_float(r.get('Endeudamiento "Calificación"')),
        'ahorro_corriente_resultado':    safe_float(r.get('Ahorro corriente "Resultado"')),
        'ahorro_corriente_calificacion': safe_float(r.get('Ahorro corriente "Calificación"')),
        'balance_primario_resultado':    safe_float(r.get('Balance Fiscal Primario "Resultado"')),
        'balance_primario_calificacion': safe_float(r.get('Balance Fiscal Primario "Calificación"')),
        'puntaje_subtotal_resultados':   safe_float(r.get('Resultados')),
        'aporte_al_idf':                 safe_float(r.get('Calificación Resultados')),
    }

    # ── Evaluación: Dimensión Gestión (20 %) ──────────────────────
    bono = safe_float(r.get('Bonificación Esfuerzo Porpio "Calificación"')) or 0.0

    gestion = {
        'holgura_resultado':               safe_float(r.get('Holgura "Resultado"')),
        'holgura_promedio_categoria':      safe_float(r.get('Promedio Holgura por Categoría')),
        'holgura_calificacion':            safe_float(r.get('Holgura "Calificación"')),
        'cap_prog_recaudo_resultado':      safe_float(r.get('Capacidad de programación y recaudo de ingresos "Resultado"')),
        'cap_prog_recaudo_calificacion':   safe_float(r.get('Capacidad de programación y recaudo de Ingresos "Calificación"')),
        'cap_ejec_inversion_resultado':    safe_float(r.get('Capacidad de Ejecución de Inversión "Resultado"')),
        'cap_ejec_inversion_calificacion': safe_float(r.get('Capacidad de Ejecución de Inversión "Calificación"')),
        'bonificacion_esfuerzo_propio':    bono,
        'puntaje_gestion_sin_bonos':       safe_float(r.get('Resultados Gestión')),
        'puntaje_gestion_con_bonos':       safe_float(r.get('Gestión +Bonos')),
        'aporte_al_idf':                   safe_float(r.get('Calificación Resultados Gestión')),
    }

    # ── Resultado IDF anual ───────────────────────────────────────
    idf_final    = safe_float(r.get('Nuevo IDF'))
    idf_sin_bono = safe_float(r.get('Nuevo IDF (sin bonos)'))
    rango_id     = resolver_rango_id(r.get('Rango'), idf_final)
    ranking      = safe_int(r.get('Ranking nacional'))

    resultado_idf = {
        'puntaje_idf_sin_bonos': idf_sin_bono,
        'puntaje_idf_final':     idf_final,
        'rango_id':              rango_id,
        'ranking_nacional':      ranking,
        # variacion_puntos_porcentuales se calcula DESPUÉS de cargar todos los años
    }

    return {
        'div2': div2,
        'anio': anio,
        'cat':  cat,
        'tipologia': tipologia,
        'insumos':   insumos,
        'resultados': resultados,
        'gestion':    gestion,
        'resultado_idf': resultado_idf,
    }


# ══════════════════════════════════════════
# PASO 2.3  Inserción transaccional
# ══════════════════════════════════════════
def paso_2_3(conn, registros):
    cur = conn.cursor()

    # Tabla: clasificacion_anual
    SQL_CLAS = """
        INSERT OR REPLACE INTO clasificacion_anual
            (departamento_id, anio, categoria_ley_617, tipologia_dnp, observacion)
        VALUES (?, ?, ?, ?, ?)
    """
    # Tabla: insumo_presupuestal_cuipo
    SQL_CUIPO = """
        INSERT OR REPLACE INTO insumo_presupuestal_cuipo (
            departamento_id, anio,
            ingresos_tributarios_a1000, ingresos_no_tributarios_a2000,
            transferencias_corrientes_a3010, transferencias_nacionales_d1000,
            ingresos_totales_a, ingresos_corrientes_ao, ahorro_corriente_c,
            gasto_inversion_e, gasto_fbkf,
            intereses_deuda_b2000, deficit_superavit_total_g,
            recursos_balance_cuipo, desembolsos_credito,
            activos_totales, pasivos_totales,
            gastos_funcionamiento_icld, limite_ley_617,
            presupuesto_inicial, recaudo_efectivo,
            compromisos_inversion, pagos_inversion
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """
    # Tabla: evaluacion_resultados_fiscales
    SQL_RES = """
        INSERT OR REPLACE INTO evaluacion_resultados_fiscales (
            departamento_id, anio,
            dep_transf_resultado, dep_transf_calificacion,
            relevancia_fbkf_resultado, relevancia_fbkf_calificacion,
            endeudamiento_resultado, endeudamiento_calificacion,
            ahorro_corriente_resultado, ahorro_corriente_calificacion,
            balance_primario_resultado, balance_primario_calificacion,
            puntaje_subtotal_resultados, aporte_al_idf
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """
    # Tabla: evaluacion_gestion_territorial
    SQL_GES = """
        INSERT OR REPLACE INTO evaluacion_gestion_territorial (
            departamento_id, anio,
            holgura_resultado, holgura_promedio_categoria, holgura_calificacion,
            cap_prog_recaudo_resultado, cap_prog_recaudo_calificacion,
            cap_ejec_inversion_resultado, cap_ejec_inversion_calificacion,
            bonificacion_esfuerzo_propio,
            puntaje_gestion_sin_bonos, puntaje_gestion_con_bonos, aporte_al_idf
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """
    # Tabla: resultado_idf_anual (sin variación por ahora)
    SQL_IDF = """
        INSERT OR REPLACE INTO resultado_idf_anual (
            departamento_id, anio,
            puntaje_idf_sin_bonos, puntaje_idf_final,
            rango_id, ranking_nacional
        ) VALUES (?,?,?,?,?,?)
    """

    ok = 0
    errores = []

    for rec in registros:
        d   = rec['div2']
        a   = rec['anio']
        ins = rec['insumos']
        res = rec['resultados']
        ges = rec['gestion']
        idf = rec['resultado_idf']

        try:
            # clasificacion_anual
            cur.execute(SQL_CLAS, (
                d, a, rec['cat'], rec['tipologia'], None
            ))

            # insumo_presupuestal_cuipo
            cur.execute(SQL_CUIPO, (
                d, a,
                ins['ingresos_tributarios_a1000'],
                ins['ingresos_no_tributarios_a2000'],
                ins['transferencias_corrientes_a3010'],
                ins['transferencias_nacionales_d1000'],
                ins['ingresos_totales_a'],
                ins['ingresos_corrientes_ao'],
                ins['ahorro_corriente_c'],
                ins['gasto_inversion_e'],
                ins['gasto_fbkf'],
                ins['intereses_deuda_b2000'],
                ins['deficit_superavit_total_g'],
                ins['recursos_balance_cuipo'],
                ins['desembolsos_credito'],
                ins['activos_totales'],
                ins['pasivos_totales'],
                ins['gastos_funcionamiento_icld'],
                ins['limite_ley_617'],
                ins['presupuesto_inicial'],
                ins['recaudo_efectivo'],
                ins['compromisos_inversion'],
                ins['pagos_inversion'],
            ))

            # evaluacion_resultados_fiscales
            cur.execute(SQL_RES, (
                d, a,
                res['dep_transf_resultado'],
                res['dep_transf_calificacion'],
                res['relevancia_fbkf_resultado'],
                res['relevancia_fbkf_calificacion'],
                res['endeudamiento_resultado'],
                res['endeudamiento_calificacion'],
                res['ahorro_corriente_resultado'],
                res['ahorro_corriente_calificacion'],
                res['balance_primario_resultado'],
                res['balance_primario_calificacion'],
                res['puntaje_subtotal_resultados'],
                res['aporte_al_idf'],
            ))

            # evaluacion_gestion_territorial
            cur.execute(SQL_GES, (
                d, a,
                ges['holgura_resultado'],
                ges['holgura_promedio_categoria'],
                ges['holgura_calificacion'],
                ges['cap_prog_recaudo_resultado'],
                ges['cap_prog_recaudo_calificacion'],
                ges['cap_ejec_inversion_resultado'],
                ges['cap_ejec_inversion_calificacion'],
                ges['bonificacion_esfuerzo_propio'],
                ges['puntaje_gestion_sin_bonos'],
                ges['puntaje_gestion_con_bonos'],
                ges['aporte_al_idf'],
            ))

            # resultado_idf_anual
            cur.execute(SQL_IDF, (
                d, a,
                idf['puntaje_idf_sin_bonos'],
                idf['puntaje_idf_final'],
                idf['rango_id'],
                idf['ranking_nacional'],
            ))

            ok += 1

        except Exception as e:
            errores.append(f"  [{d}/{a}] {e}")

    # ── Calcular variación interanual y actualizar resultado_idf_anual ──
    cur.execute("""
        UPDATE resultado_idf_anual AS r
        SET variacion_puntos_porcentuales = (
            r.puntaje_idf_final - (
                SELECT p.puntaje_idf_final
                FROM resultado_idf_anual p
                WHERE p.departamento_id = r.departamento_id
                  AND p.anio = r.anio - 1
            )
        )
        WHERE r.anio > (SELECT MIN(anio) FROM resultado_idf_anual)
    """)

    conn.commit()

    print(f"[2.3] ✔ {ok} registros insertados correctamente.")
    if errores:
        print(f"[2.3] ⚠  {len(errores)} errores:")
        for e in errores:
            print(e)
    return ok, errores


# ══════════════════════════════════════════
# PASO 2.4  Vistas analíticas
# ══════════════════════════════════════════
VISTAS = {

    'vw_visualizador_evolucion_nacional': """
        CREATE VIEW IF NOT EXISTS vw_visualizador_evolucion_nacional AS
        SELECT
            r.anio,
            ROUND(AVG(r.puntaje_idf_final), 6)  AS idf_promedio,
            ROUND(MAX(r.puntaje_idf_final), 6)  AS idf_maximo,
            ROUND(MIN(r.puntaje_idf_final), 6)  AS idf_minimo,
            COUNT(r.departamento_id)             AS deptos_evaluados,
            ROUND(AVG(r.variacion_puntos_porcentuales), 4) AS var_pp_promedio
        FROM resultado_idf_anual r
        GROUP BY r.anio
        ORDER BY r.anio
    """,

    'vw_visualizador_mapa': """
        CREATE VIEW IF NOT EXISTS vw_visualizador_mapa AS
        SELECT
            d.codigo_divipola_2,
            d.codigo_divipola_5,
            d.nombre              AS departamento,
            d.nombre_visual,
            d.region,
            r.anio,
            r.puntaje_idf_final   AS idf,
            r.puntaje_idf_sin_bonos,
            r.ranking_nacional    AS ranking,
            r.variacion_puntos_porcentuales AS var_pp,
            cr.rango_id,
            cr.codigo             AS rango,
            cr.nombre_completo    AS rango_completo,
            cr.color_hex,
            c.categoria_ley_617   AS categoria,
            c.tipologia_dnp       AS tipologia
        FROM resultado_idf_anual r
        JOIN departamento             d  ON r.departamento_id = d.codigo_divipola_2
        JOIN catalogo_rango_desempeno cr ON r.rango_id        = cr.rango_id
        JOIN clasificacion_anual      c  ON r.departamento_id = c.departamento_id
                                        AND r.anio            = c.anio
        ORDER BY r.anio, r.ranking_nacional
    """,

    'vw_visualizador_ficha': """
        CREATE VIEW IF NOT EXISTS vw_visualizador_ficha AS
        SELECT
            d.codigo_divipola_2,
            d.codigo_divipola_5,
            d.nombre              AS departamento,
            d.nombre_visual,
            d.region,
            r.anio,
            c.categoria_ley_617   AS categoria,
            c.tipologia_dnp       AS tipologia,
            -- IDF y ranking
            r.puntaje_idf_final       AS idf,
            r.puntaje_idf_sin_bonos   AS idf_sin_bonos,
            r.ranking_nacional        AS ranking,
            r.variacion_puntos_porcentuales AS var_pp,
            cr.rango_id,
            cr.codigo             AS rango,
            cr.nombre_completo    AS rango_completo,
            cr.color_hex,
            -- Dimensión Resultados (80 %)
            res.puntaje_subtotal_resultados  AS resultados_score,
            res.aporte_al_idf                AS resultados_aporte,
            res.dep_transf_resultado,        res.dep_transf_calificacion,
            res.relevancia_fbkf_resultado,   res.relevancia_fbkf_calificacion,
            res.endeudamiento_resultado,     res.endeudamiento_calificacion,
            res.ahorro_corriente_resultado,  res.ahorro_corriente_calificacion,
            res.balance_primario_resultado,  res.balance_primario_calificacion,
            -- Dimensión Gestión (20 %)
            ges.puntaje_gestion_con_bonos    AS gestion_score,
            ges.aporte_al_idf                AS gestion_aporte,
            ges.holgura_resultado,           ges.holgura_promedio_categoria,
            ges.holgura_calificacion,
            ges.cap_prog_recaudo_resultado,  ges.cap_prog_recaudo_calificacion,
            ges.cap_ejec_inversion_resultado, ges.cap_ejec_inversion_calificacion,
            ges.bonificacion_esfuerzo_propio,
            -- Insumos CUIPO / FUT
            ins.ingresos_tributarios_a1000,
            ins.ingresos_no_tributarios_a2000,
            ins.transferencias_corrientes_a3010,
            ins.transferencias_nacionales_d1000,
            ins.ingresos_totales_a,
            ins.ingresos_corrientes_ao,
            ins.ahorro_corriente_c,
            ins.gasto_inversion_e,
            ins.gasto_fbkf,
            ins.activos_totales,
            ins.pasivos_totales,
            ins.gastos_funcionamiento_icld,
            ins.limite_ley_617,
            ins.presupuesto_inicial,
            ins.recaudo_efectivo,
            ins.compromisos_inversion,
            ins.pagos_inversion
        FROM resultado_idf_anual r
        JOIN departamento             d   ON r.departamento_id = d.codigo_divipola_2
        JOIN catalogo_rango_desempeno cr  ON r.rango_id        = cr.rango_id
        JOIN clasificacion_anual      c   ON r.departamento_id = c.departamento_id
                                         AND r.anio            = c.anio
        JOIN evaluacion_resultados_fiscales res
                                          ON r.departamento_id = res.departamento_id
                                         AND r.anio            = res.anio
        JOIN evaluacion_gestion_territorial ges
                                          ON r.departamento_id = ges.departamento_id
                                         AND r.anio            = ges.anio
        LEFT JOIN insumo_presupuestal_cuipo ins
                                          ON r.departamento_id = ins.departamento_id
                                         AND r.anio            = ins.anio
    """,
}


def paso_2_4(conn):
    for nombre, sql in VISTAS.items():
        # Eliminar si existía para recrear limpia
        conn.execute(f"DROP VIEW IF EXISTS {nombre}")
        conn.execute(sql.strip())
    conn.commit()
    vistas = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name"
    ).fetchall()
    print(f"[2.4] ✔ {len(vistas)} vistas analíticas creadas:")
    for v in vistas:
        print(f"      {v[0]}")


# ══════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════
if __name__ == '__main__':
    print("=" * 62)
    print("FASE 2 — ETL: Excel → Base de Datos SQLite IDF")
    print("=" * 62)

    # ── 2.1 Lectura ──────────────────────────────────────────────
    df = paso_2_1()

    # ── 2.2 Transformación fila a fila ───────────────────────────
    print("[2.2] Transformando y normalizando registros…")
    registros = []
    for _, row in df.iterrows():
        registros.append(transformar_fila(row))
    print(f"[2.2] ✔ {len(registros)} registros transformados.")

    # Resumen de nulos en insumos CUIPO por año
    nulos_cuipo = {}
    for rec in registros:
        a = rec['anio']
        tiene = any(v is not None for v in rec['insumos'].values())
        nulos_cuipo[a] = nulos_cuipo.get(a, 0) + (0 if tiene else 1)
    for a in sorted(nulos_cuipo):
        n = nulos_cuipo[a]
        nota = "  ← nulos CUIPO esperados" if n > 0 else ""
        print(f"       Año {a}: {n} fila(s) sin insumos CUIPO{nota}")

    # ── 2.3 Inserción transaccional ──────────────────────────────
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    print("[2.3] Iniciando transacción de carga…")
    try:
        ok, errores = paso_2_3(conn, registros)
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"[ERROR CRÍTICO] {e}")
        sys.exit(1)

    # ── 2.4 Vistas analíticas ────────────────────────────────────
    paso_2_4(conn)

    # ── Verificación final ───────────────────────────────────────
    print()
    print("─" * 50)
    print("VERIFICACIÓN RÁPIDA DE CARGA:")

    tablas = [
        'clasificacion_anual',
        'insumo_presupuestal_cuipo',
        'evaluacion_resultados_fiscales',
        'evaluacion_gestion_territorial',
        'resultado_idf_anual',
    ]
    for t in tablas:
        n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:<45} {n:>4} filas")

    print()
    print("  Registros con variación calculada:")
    n_var = conn.execute(
        "SELECT COUNT(*) FROM resultado_idf_anual WHERE variacion_puntos_porcentuales IS NOT NULL"
    ).fetchone()[0]
    print(f"    {n_var} de {ok} (las 32 filas de 2020 no tienen año anterior → variación=NULL)")

    print()
    print("  Muestra — IDF 2024 (Top 5 por ranking):")
    rows = conn.execute("""
        SELECT d.nombre_visual, r.puntaje_idf_final, cr.codigo, r.ranking_nacional,
               ROUND(r.variacion_puntos_porcentuales,2) as var
        FROM resultado_idf_anual r
        JOIN departamento d ON r.departamento_id = d.codigo_divipola_2
        JOIN catalogo_rango_desempeno cr ON r.rango_id = cr.rango_id
        WHERE r.anio = 2024
        ORDER BY r.ranking_nacional
        LIMIT 5
    """).fetchall()
    for rw in rows:
        print(f"    #{rw[3]:02d}  {rw[0]:<25} IDF={rw[1]:.4f}  {rw[2]:<12}  Var={rw[4]}")

    conn.close()

    print()
    print("=" * 62)
    if not errores:
        print("✔  FASE 2 COMPLETADA SIN ERRORES")
    else:
        print(f"⚠  FASE 2 COMPLETADA CON {len(errores)} ADVERTENCIAS")
    print(f"   Base de datos: {DB_PATH}")
    print("=" * 62)
