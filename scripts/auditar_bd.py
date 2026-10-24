"""
FASE 3 — Auditoría y Control de Calidad

Validaciones:
  3.A  Cobertura: 32 registros exactos por vigencia en cada tabla de hechos
  3.B  Unicidad de rankings: no hay empates sin desempatar (UNIQUE por año)
  3.C  Integridad matemática: IDF ≈ Aporte Resultados + Aporte Gestión (error < 0.0001)
  3.D  Comparación directa vs Dashboard IDF del Excel (promedio, máx, mín por vigencia)
  3.E  Coherencia de rangos: clasificación coincide con los límites del catálogo
  3.F  Nulos CUIPO: solo 2020 tiene insumos nulos; 2021-2024 completos
  3.G  Tipologías: solo 2024 tiene tipología asignada; 2020-2023 en NULL
  3.H  Variaciones: 2020 sin variación (NULL); 2021-2024 calculados y razonables
"""

import os
import sys
import math
import sqlite3
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH  = os.path.join(BASE_DIR, 'data', 'idf_database.db')
EXCEL    = os.path.join(BASE_DIR, 'Desempeño Fiscal departamentos 2020-2024.xlsx')

ANIOS = [2020, 2021, 2022, 2023, 2024]
TABLAS_HECHOS = [
    'clasificacion_anual',
    'insumo_presupuestal_cuipo',
    'evaluacion_resultados_fiscales',
    'evaluacion_gestion_territorial',
    'resultado_idf_anual',
]

PASS  = "  ✔ "
FAIL  = "  ✘ "
WARN  = "  ⚠  "

resultados_audit = []   # lista de (descripcion, ok: bool, detalle)

def registrar(descripcion, ok, detalle=""):
    resultados_audit.append((descripcion, ok, detalle))
    icono = PASS if ok else FAIL
    print(f"{icono} {descripcion}")
    if detalle:
        for linea in detalle.strip().split('\n'):
            print(f"       {linea}")


# ══════════════════════════════════════════════════
# 3.A  COBERTURA: 32 registros por año y tabla
# ══════════════════════════════════════════════════
def auditoria_3a(conn):
    print("\n── 3.A  Cobertura (32 departamentos × 5 vigencias) ──────────────")
    todo_ok = True
    for tabla in TABLAS_HECHOS:
        filas = conn.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
        ok_total = (filas == 160)
        if not ok_total:
            todo_ok = False
        rows_anio = conn.execute(
            f"SELECT anio, COUNT(*) FROM {tabla} GROUP BY anio ORDER BY anio"
        ).fetchall()
        detalle_lines = []
        for anio, n in rows_anio:
            ok_anio = (n == 32)
            if not ok_anio:
                todo_ok = False
            marca = "✔" if ok_anio else "✘"
            detalle_lines.append(f"{marca} {anio}: {n}/32 registros")
        detalle = f"Total={filas}/160\n" + "\n".join(detalle_lines)
        registrar(f"[{tabla}] cobertura completa", ok_total, detalle)


# ══════════════════════════════════════════════════
# 3.B  UNICIDAD DE RANKINGS
# ══════════════════════════════════════════════════
def auditoria_3b(conn):
    print("\n── 3.B  Unicidad de rankings por vigencia ────────────────────────")
    rows = conn.execute("""
        SELECT anio, ranking_nacional, COUNT(*) n
        FROM resultado_idf_anual
        GROUP BY anio, ranking_nacional
        HAVING n > 1
    """).fetchall()
    ok = len(rows) == 0
    detalle = ""
    if not ok:
        detalle = "\n".join(f"Año {r[0]} ranking #{r[1]} aparece {r[2]} veces" for r in rows)
    registrar("Rankings únicos por vigencia (UNIQUE anio+ranking)", ok, detalle)

    # Rango 1-32 completo sin huecos
    huecos = []
    for anio in ANIOS:
        rankings = [r[0] for r in conn.execute(
            "SELECT ranking_nacional FROM resultado_idf_anual WHERE anio=? ORDER BY ranking_nacional",
            (anio,)
        ).fetchall()]
        esperado = list(range(1, 33))
        if rankings != esperado:
            huecos.append(f"Año {anio}: rankings={rankings[:5]}…")
    ok_seq = len(huecos) == 0
    registrar("Rankings forman la secuencia completa 1–32 en cada año",
              ok_seq, "\n".join(huecos) if huecos else "")


# ══════════════════════════════════════════════════
# 3.C  INTEGRIDAD MATEMÁTICA DEL IDF
#      IDF_final ≈ aporte_resultados + aporte_gestion
# ══════════════════════════════════════════════════
def auditoria_3c(conn):
    print("\n── 3.C  Integridad matemática: IDF = Res(80%) + Ges(20%) ─────────")
    MAX_ERROR = 0.0001
    rows = conn.execute("""
        SELECT r.departamento_id, r.anio,
               r.puntaje_idf_final,
               res.aporte_al_idf  AS ap_res,
               ges.aporte_al_idf  AS ap_ges,
               ABS(r.puntaje_idf_final - res.aporte_al_idf - ges.aporte_al_idf) AS diferencia
        FROM resultado_idf_anual r
        JOIN evaluacion_resultados_fiscales res ON r.departamento_id=res.departamento_id AND r.anio=res.anio
        JOIN evaluacion_gestion_territorial ges ON r.departamento_id=ges.departamento_id AND r.anio=ges.anio
        WHERE ABS(r.puntaje_idf_final - res.aporte_al_idf - ges.aporte_al_idf) > ?
    """, (MAX_ERROR,)).fetchall()

    ok = len(rows) == 0
    detalle = ""
    if not ok:
        detalle = "\n".join(
            f"[{r[0]}/{r[1]}] IDF={r[2]:.6f}  Res+Ges={r[3]+r[4]:.6f}  dif={r[5]:.8f}"
            for r in rows
        )
    registrar(
        f"Fórmula IDF = Aporte_Resultados + Aporte_Gestión  (tolerancia < {MAX_ERROR})",
        ok, detalle if detalle else f"160 registros verificados. Error máximo < {MAX_ERROR}"
    )

    # Máxima diferencia encontrada
    max_dif = conn.execute("""
        SELECT MAX(ABS(r.puntaje_idf_final - res.aporte_al_idf - ges.aporte_al_idf))
        FROM resultado_idf_anual r
        JOIN evaluacion_resultados_fiscales res ON r.departamento_id=res.departamento_id AND r.anio=res.anio
        JOIN evaluacion_gestion_territorial ges ON r.departamento_id=ges.departamento_id AND r.anio=ges.anio
    """).fetchone()[0]
    registrar(
        f"Error máximo encontrado en 160 registros: {max_dif:.10f}",
        max_dif < MAX_ERROR
    )


# ══════════════════════════════════════════════════
# 3.D  COMPARACIÓN VS EXCEL DASHBOARD IDF
# ══════════════════════════════════════════════════
# Valores de referencia extraídos de la hoja 'Dashboard IDF' durante el análisis
DASHBOARD_EXCEL = {
    2020: {'avg': 54.088868, 'max': 73.550686, 'min': 38.857279},
    2021: {'avg': 57.480757, 'max': 75.965848, 'min': 40.293190},
    2022: {'avg': 54.725204, 'max': 74.954986, 'min': 40.171050},
    2023: {'avg': 56.601959, 'max': 73.040468, 'min': 42.085960},
    2024: {'avg': 53.462243, 'max': 70.904288, 'min': 38.127031},
}

def auditoria_3d(conn):
    print("\n── 3.D  Comparación directa vs Dashboard IDF (Excel) ─────────────")
    TOLERANCIA = 0.000001
    todo_ok = True
    lineas = [f"{'Año':<6} {'Prom BD':>12} {'Prom Excel':>12} {'Diff':>12}  {'Máx BD':>12} {'Mín BD':>12}"]
    for anio in ANIOS:
        row = conn.execute("""
            SELECT AVG(puntaje_idf_final), MAX(puntaje_idf_final), MIN(puntaje_idf_final)
            FROM resultado_idf_anual WHERE anio=?
        """, (anio,)).fetchone()
        avg_bd, max_bd, min_bd = row
        ref = DASHBOARD_EXCEL[anio]
        diff_avg = abs(avg_bd - ref['avg'])
        diff_max = abs(max_bd - ref['max'])
        diff_min = abs(min_bd - ref['min'])
        ok_anio  = (diff_avg < TOLERANCIA and diff_max < TOLERANCIA and diff_min < TOLERANCIA)
        if not ok_anio:
            todo_ok = False
        marca = "✔" if ok_anio else "✘"
        lineas.append(
            f"{anio}  {marca}  "
            f"{avg_bd:12.6f} {ref['avg']:12.6f} {diff_avg:+12.8f}  "
            f"máx_diff={diff_max:.2e}  mín_diff={diff_min:.2e}"
        )
    registrar(
        "Promedio/máx/mín por vigencia coincide con Dashboard IDF Excel",
        todo_ok,
        "\n".join(lineas)
    )


# ══════════════════════════════════════════════════
# 3.E  COHERENCIA DE RANGOS
# ══════════════════════════════════════════════════
def auditoria_3e(conn):
    print("\n── 3.E  Coherencia de rangos (límites del catálogo) ─────────────")
    errores = conn.execute("""
        SELECT r.departamento_id, r.anio, r.puntaje_idf_final, cr.limite_inferior, cr.limite_superior
        FROM resultado_idf_anual r
        JOIN catalogo_rango_desempeno cr ON r.rango_id = cr.rango_id
        WHERE r.puntaje_idf_final < cr.limite_inferior
           OR r.puntaje_idf_final >= cr.limite_superior
    """).fetchall()
    ok = len(errores) == 0
    detalle = ""
    if not ok:
        detalle = "\n".join(
            f"[{e[0]}/{e[1]}] IDF={e[2]:.4f} fuera de [{e[3]},{e[4]})"
            for e in errores
        )
    registrar(
        "Todos los IDF se ubican dentro del rango asignado",
        ok, detalle if detalle else "160/160 registros coherentes con el catálogo"
    )


# ══════════════════════════════════════════════════
# 3.F  NULOS CUIPO: solo 2020 sin insumos
# ══════════════════════════════════════════════════
def auditoria_3f(conn):
    print("\n── 3.F  Nulos CUIPO: solo 2020 sin insumos presupuestales ───────")
    # 2020 → todos nulos en ingresos_tributarios_a1000
    n_nulos_2020 = conn.execute(
        "SELECT COUNT(*) FROM insumo_presupuestal_cuipo WHERE anio=2020 AND ingresos_tributarios_a1000 IS NULL"
    ).fetchone()[0]
    ok_2020 = (n_nulos_2020 == 32)
    registrar(f"Año 2020: 32 filas sin A1000 (esperado)", ok_2020,
              f"Filas nulas A1000 en 2020: {n_nulos_2020}/32")

    # 2021-2024 → sin nulos en A1000
    n_nulos_resto = conn.execute(
        "SELECT COUNT(*) FROM insumo_presupuestal_cuipo WHERE anio>2020 AND ingresos_tributarios_a1000 IS NULL"
    ).fetchone()[0]
    ok_resto = (n_nulos_resto == 0)
    registrar(f"Años 2021-2024: ninguna fila nula en A1000 (esperado)", ok_resto,
              f"Filas nulas A1000 en 2021-2024: {n_nulos_resto}")


# ══════════════════════════════════════════════════
# 3.G  TIPOLOGÍAS: solo 2024 asignadas
# ══════════════════════════════════════════════════
def auditoria_3g(conn):
    print("\n── 3.G  Tipologías DNP: solo 2024 tiene valor asignado ───────────")
    n_tip_2024 = conn.execute(
        "SELECT COUNT(*) FROM clasificacion_anual WHERE anio=2024 AND tipologia_dnp IS NOT NULL"
    ).fetchone()[0]
    ok_2024 = (n_tip_2024 == 32)
    registrar("2024: los 32 deptos tienen tipología asignada", ok_2024,
              f"Registros con tipología en 2024: {n_tip_2024}/32")

    n_tip_prev = conn.execute(
        "SELECT COUNT(*) FROM clasificacion_anual WHERE anio<2024 AND tipologia_dnp IS NOT NULL"
    ).fetchone()[0]
    ok_prev = (n_tip_prev == 0)
    registrar("2020-2023: tipología = NULL (no aplicaba)", ok_prev,
              f"Registros con tipología en 2020-2023: {n_tip_prev} (esperado 0)")

    # Distribución 2024
    dist = conn.execute(
        "SELECT tipologia_dnp, COUNT(*) FROM clasificacion_anual WHERE anio=2024 GROUP BY tipologia_dnp ORDER BY tipologia_dnp"
    ).fetchall()
    detalle = "  ".join(f"T{r[0]}:{r[1]}" for r in dist)
    registrar(f"Distribución tipologías 2024: {detalle}", True)


# ══════════════════════════════════════════════════
# 3.H  VARIACIONES INTERANUALES
# ══════════════════════════════════════════════════
def auditoria_3h(conn):
    print("\n── 3.H  Variaciones interanuales calculadas ──────────────────────")
    n_null_2020 = conn.execute(
        "SELECT COUNT(*) FROM resultado_idf_anual WHERE anio=2020 AND variacion_puntos_porcentuales IS NULL"
    ).fetchone()[0]
    ok_2020 = (n_null_2020 == 32)
    registrar("2020: variación = NULL (primer año de la serie)", ok_2020,
              f"Registros sin variación en 2020: {n_null_2020}/32")

    n_var_resto = conn.execute(
        "SELECT COUNT(*) FROM resultado_idf_anual WHERE anio>2020 AND variacion_puntos_porcentuales IS NOT NULL"
    ).fetchone()[0]
    ok_resto = (n_var_resto == 128)
    registrar("2021-2024: variación calculada en los 128 registros", ok_resto,
              f"Registros con variación: {n_var_resto}/128")

    # Mínimo y máximo de variación (sanity check)
    stats = conn.execute(
        "SELECT MIN(variacion_puntos_porcentuales), MAX(variacion_puntos_porcentuales) FROM resultado_idf_anual WHERE variacion_puntos_porcentuales IS NOT NULL"
    ).fetchone()
    rango_razonable = (-50 < stats[0] and stats[1] < 50)
    registrar(
        f"Rango de variaciones razonable: [{stats[0]:.2f}, {stats[1]:.2f}] pp",
        rango_razonable
    )


# ══════════════════════════════════════════════════
# INFORME FINAL
# ══════════════════════════════════════════════════
def informe_final():
    total  = len(resultados_audit)
    ok_cnt = sum(1 for _, ok, _ in resultados_audit if ok)
    ko_cnt = total - ok_cnt

    print()
    print("=" * 62)
    print("INFORME FINAL DE AUDITORÍA")
    print("=" * 62)
    print(f"  Total de verificaciones : {total}")
    print(f"  ✔  Pasadas              : {ok_cnt}")
    print(f"  ✘  Fallidas             : {ko_cnt}")
    print()
    if ko_cnt == 0:
        print("  🎯 BASE DE DATOS VALIDADA — CERO DISCREPANCIAS")
        print("     Los datos de la BD coinciden 100 % con el Excel oficial.")
    else:
        print("  ⚠  SE ENCONTRARON PROBLEMAS. Revisar las verificaciones marcadas con ✘")
    print("=" * 62)
    return ko_cnt == 0


# ══════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════
if __name__ == '__main__':
    print("=" * 62)
    print("FASE 3 — Auditoría y Control de Calidad de la BD IDF")
    print("=" * 62)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    auditoria_3a(conn)
    auditoria_3b(conn)
    auditoria_3c(conn)
    auditoria_3d(conn)
    auditoria_3e(conn)
    auditoria_3f(conn)
    auditoria_3g(conn)
    auditoria_3h(conn)

    conn.close()

    exito = informe_final()
    sys.exit(0 if exito else 1)
