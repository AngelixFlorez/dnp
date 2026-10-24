"""
FASE 1 — PASO 1.1, 1.2 y 1.3
Inicializa la base de datos SQLite del proyecto IDF Departamental (DNP).

Crea:
  - data/idf_database.db
  - 8 tablas relacionales en 3FN con constraints e índices
  - Catálogos maestros fijos:
      * 32 departamentos (DIVIPOLA + región)
      * 5 vigencias fiscales (2020–2024)
      * 5 rangos de desempeño fiscal
"""

import sqlite3
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

# ──────────────────────────────────────────
# CONFIGURACIÓN
# ──────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'idf_database.db')
DB_PATH = os.path.normpath(DB_PATH)


# ══════════════════════════════════════════
# PASO 1.1  Crear/verificar carpeta y archivo
# ══════════════════════════════════════════
def paso_1_1():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    print(f"[1.1] ✔ Directorio verificado: {os.path.dirname(DB_PATH)}")
    print(f"[1.1]   Archivo BD: {DB_PATH}")


# ══════════════════════════════════════════
# PASO 1.2  DDL — 8 tablas + índices
# ══════════════════════════════════════════
DDL = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- ── 1. Catálogo maestro de departamentos ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS departamento (
    codigo_divipola_2  TEXT PRIMARY KEY           CHECK(length(codigo_divipola_2)  = 2),
    codigo_divipola_5  TEXT NOT NULL UNIQUE       CHECK(length(codigo_divipola_5)  = 5),
    nombre             TEXT NOT NULL UNIQUE,   -- mayúsculas, sin tilde (key interna)
    nombre_visual      TEXT NOT NULL,          -- capitalizado para UI
    region             TEXT NOT NULL,
    activo             INTEGER NOT NULL DEFAULT 1,
    created_at         TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ── 2. Maestro de vigencias fiscales ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vigencia_fiscal (
    anio               INTEGER PRIMARY KEY,
    descripcion        TEXT    NOT NULL,
    es_vigencia_activa INTEGER NOT NULL DEFAULT 0,
    fecha_publicacion_dnp TEXT NULL       -- ISO-8601 o NULL
);

-- ── 3. Catálogo paramétrico de rangos de desempeño ───────────────────────────
CREATE TABLE IF NOT EXISTS catalogo_rango_desempeno (
    rango_id               INTEGER PRIMARY KEY,   -- 1..5
    codigo                 TEXT    NOT NULL UNIQUE,
    nombre_completo        TEXT    NOT NULL,
    limite_inferior        REAL    NOT NULL,
    limite_superior        REAL    NOT NULL,
    color_hex              TEXT    NOT NULL,
    descripcion_cualitativa TEXT   NOT NULL,
    CHECK(rango_id BETWEEN 1 AND 5),
    CHECK(limite_inferior >= 0 AND limite_superior <= 105)
);

-- ── 4. Clasificación anual (Categoría Ley 617 + Tipología DNP) ───────────────
CREATE TABLE IF NOT EXISTS clasificacion_anual (
    departamento_id   TEXT    NOT NULL REFERENCES departamento(codigo_divipola_2) ON UPDATE CASCADE ON DELETE RESTRICT,
    anio              INTEGER NOT NULL REFERENCES vigencia_fiscal(anio)           ON UPDATE CASCADE ON DELETE RESTRICT,
    categoria_ley_617 TEXT    NOT NULL,   -- 'ESP', '1', '2', '3', '4'
    tipologia_dnp     INTEGER NULL,       -- 1, 2 o 3; NULL para vigencias antes de 2024
    observacion       TEXT    NULL,
    PRIMARY KEY (departamento_id, anio),
    CHECK(tipologia_dnp IN (1, 2, 3) OR tipologia_dnp IS NULL)
);

-- ── 5. Insumos presupuestales y contables CUIPO / FUT ────────────────────────
CREATE TABLE IF NOT EXISTS insumo_presupuestal_cuipo (
    departamento_id                   TEXT    NOT NULL REFERENCES departamento(codigo_divipola_2) ON UPDATE CASCADE ON DELETE RESTRICT,
    anio                              INTEGER NOT NULL REFERENCES vigencia_fiscal(anio)           ON UPDATE CASCADE ON DELETE RESTRICT,
    -- Ingresos
    ingresos_tributarios_a1000        REAL NULL,   -- A1000
    ingresos_no_tributarios_a2000     REAL NULL,   -- A2000
    transferencias_corrientes_a3010   REAL NULL,   -- A3010 (sin SGR)
    transferencias_nacionales_d1000   REAL NULL,   -- D1000 total
    ingresos_totales_a                REAL NULL,   -- A total
    ingresos_corrientes_ao            REAL NULL,   -- AO corrientes
    ahorro_corriente_c                REAL NULL,   -- C
    -- Gasto e inversión
    gasto_inversion_e                 REAL NULL,   -- E
    gasto_fbkf                        REAL NULL,   -- FBKF
    -- Deuda
    intereses_deuda_b2000             REAL NULL,   -- B2000
    deficit_superavit_total_g         REAL NULL,   -- G
    recursos_balance_cuipo            REAL NULL,
    desembolsos_credito               REAL NULL,
    -- Balance patrimonial
    activos_totales                   REAL NULL,
    pasivos_totales                   REAL NULL,
    -- Ley 617
    gastos_funcionamiento_icld        REAL NULL,   -- % GF/ICLD
    limite_ley_617                    REAL NULL,   -- % límite legal
    -- Ejecución presupuestal
    presupuesto_inicial               REAL NULL,
    recaudo_efectivo                  REAL NULL,
    compromisos_inversion             REAL NULL,
    pagos_inversion                   REAL NULL,
    PRIMARY KEY (departamento_id, anio)
);

-- ── 6. Evaluación Dimensión Resultados (80 %) ─────────────────────────────────
CREATE TABLE IF NOT EXISTS evaluacion_resultados_fiscales (
    departamento_id             TEXT    NOT NULL REFERENCES departamento(codigo_divipola_2) ON UPDATE CASCADE ON DELETE RESTRICT,
    anio                        INTEGER NOT NULL REFERENCES vigencia_fiscal(anio)           ON UPDATE CASCADE ON DELETE RESTRICT,
    -- 5 indicadores de resultados
    dep_transf_resultado        REAL NOT NULL,
    dep_transf_calificacion     REAL NOT NULL,
    relevancia_fbkf_resultado   REAL NOT NULL,
    relevancia_fbkf_calificacion REAL NOT NULL,
    endeudamiento_resultado     REAL NOT NULL,
    endeudamiento_calificacion  REAL NOT NULL,
    ahorro_corriente_resultado  REAL NOT NULL,
    ahorro_corriente_calificacion REAL NOT NULL,
    balance_primario_resultado  REAL NOT NULL,
    balance_primario_calificacion REAL NOT NULL,
    -- Subtotal ponderado
    puntaje_subtotal_resultados REAL NOT NULL,
    aporte_al_idf               REAL NOT NULL,   -- subtotal * 0.80
    PRIMARY KEY (departamento_id, anio)
);

-- ── 7. Evaluación Dimensión Gestión (20 %) ────────────────────────────────────
CREATE TABLE IF NOT EXISTS evaluacion_gestion_territorial (
    departamento_id                   TEXT    NOT NULL REFERENCES departamento(codigo_divipola_2) ON UPDATE CASCADE ON DELETE RESTRICT,
    anio                              INTEGER NOT NULL REFERENCES vigencia_fiscal(anio)           ON UPDATE CASCADE ON DELETE RESTRICT,
    -- 3 indicadores de gestión
    holgura_resultado                 REAL NOT NULL,
    holgura_promedio_categoria        REAL NULL,
    holgura_calificacion              REAL NOT NULL,
    cap_prog_recaudo_resultado        REAL NOT NULL,
    cap_prog_recaudo_calificacion     REAL NOT NULL,
    cap_ejec_inversion_resultado      REAL NOT NULL,
    cap_ejec_inversion_calificacion   REAL NOT NULL,
    -- Bonificación esfuerzo propio
    bonificacion_esfuerzo_propio      REAL NOT NULL DEFAULT 0,
    -- Subtotales
    puntaje_gestion_sin_bonos         REAL NOT NULL,
    puntaje_gestion_con_bonos         REAL NOT NULL,
    aporte_al_idf                     REAL NOT NULL,   -- con_bonos * 0.20
    PRIMARY KEY (departamento_id, anio)
);

-- ── 8. Hecho central: Resultado IDF anual ────────────────────────────────────
CREATE TABLE IF NOT EXISTS resultado_idf_anual (
    departamento_id               TEXT    NOT NULL REFERENCES departamento(codigo_divipola_2)     ON UPDATE CASCADE ON DELETE RESTRICT,
    anio                          INTEGER NOT NULL REFERENCES vigencia_fiscal(anio)               ON UPDATE CASCADE ON DELETE RESTRICT,
    puntaje_idf_sin_bonos         REAL    NOT NULL,
    puntaje_idf_final             REAL    NOT NULL,
    rango_id                      INTEGER NOT NULL REFERENCES catalogo_rango_desempeno(rango_id),
    ranking_nacional              INTEGER NOT NULL,
    variacion_puntos_porcentuales REAL    NULL,   -- NULL para el primer año de la serie
    PRIMARY KEY (departamento_id, anio),
    UNIQUE  (anio, ranking_nacional),
    CHECK   (ranking_nacional BETWEEN 1 AND 32),
    CHECK   (puntaje_idf_final BETWEEN 0 AND 110)
);

-- ── Índices de rendimiento ────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_resultado_anio       ON resultado_idf_anual(anio);
CREATE INDEX IF NOT EXISTS idx_resultado_rango      ON resultado_idf_anual(rango_id);
CREATE INDEX IF NOT EXISTS idx_resultado_ranking    ON resultado_idf_anual(anio, ranking_nacional);
CREATE INDEX IF NOT EXISTS idx_clasificacion_cat    ON clasificacion_anual(categoria_ley_617);
CREATE INDEX IF NOT EXISTS idx_clasificacion_tip    ON clasificacion_anual(tipologia_dnp);
CREATE INDEX IF NOT EXISTS idx_depto_region         ON departamento(region);
"""


def paso_1_2(conn):
    # executescript ejecuta el DDL completo de una vez, maneja correctamente
    # los comentarios inline y los bloques multi-línea con punto y coma.
    conn.executescript(DDL)
    conn.commit()
    print("[1.2] ✔ 8 tablas creadas + índices de rendimiento aplicados.")


# ══════════════════════════════════════════
# PASO 1.3  Catálogos maestros fijos
# ══════════════════════════════════════════

# 32 departamentos: (divipola_2, divipola_5, nombre_clave, nombre_visual, región)
DEPARTAMENTOS = [
    ('05', '05000', 'ANTIOQUIA',           'Antioquia',             'Eje Cafetero'),
    ('08', '08000', 'ATLANTICO',           'Atlántico',             'Caribe'),
    ('13', '13000', 'BOLIVAR',             'Bolívar',               'Caribe'),
    ('15', '15000', 'BOYACA',              'Boyacá',                'Centro Oriente'),
    ('17', '17000', 'CALDAS',              'Caldas',                'Eje Cafetero'),
    ('18', '18000', 'CAQUETA',             'Caquetá',               'Centro Sur Amazonia'),
    ('19', '19000', 'CAUCA',               'Cauca',                 'Pacifico'),
    ('20', '20000', 'CESAR',               'Cesar',                 'Caribe'),
    ('23', '23000', 'CORDOBA',             'Córdoba',               'Caribe'),
    ('25', '25000', 'CUNDINAMARCA',        'Cundinamarca',          'Centro Oriente'),
    ('27', '27000', 'CHOCO',               'Chocó',                 'Pacifico'),
    ('41', '41000', 'HUILA',               'Huila',                 'Centro Sur Amazonia'),
    ('44', '44000', 'GUAJIRA',             'La Guajira',            'Caribe'),
    ('47', '47000', 'MAGDALENA',           'Magdalena',             'Caribe'),
    ('50', '50000', 'META',                'Meta',                  'Del Llano'),
    ('52', '52000', 'NARIÑO',              'Nariño',                'Pacifico'),
    ('54', '54000', 'NORTE DE SANTANDER',  'Norte de Santander',    'Centro Oriente'),
    ('63', '63000', 'QUINDIO',             'Quindío',               'Eje Cafetero'),
    ('66', '66000', 'RISARALDA',           'Risaralda',             'Eje Cafetero'),
    ('68', '68000', 'SANTANDER',           'Santander',             'Centro Oriente'),
    ('70', '70000', 'SUCRE',               'Sucre',                 'Caribe'),
    ('73', '73000', 'TOLIMA',              'Tolima',                'Centro Sur Amazonia'),
    ('76', '76000', 'VALLE DEL CAUCA',     'Valle del Cauca',       'Pacifico'),
    ('81', '81000', 'ARAUCA',              'Arauca',                'Del Llano'),
    ('85', '85000', 'CASANARE',            'Casanare',              'Del Llano'),
    ('86', '86000', 'PUTUMAYO',            'Putumayo',              'Centro Sur Amazonia'),
    ('88', '88000', 'SAN ANDRÉS',          'San Andrés',            'Caribe'),
    ('91', '91000', 'AMAZONAS',            'Amazonas',              'Centro Sur Amazonia'),
    ('94', '94000', 'GUAINIA',             'Guainía',               'Del Llano'),
    ('95', '95000', 'GUAVIARE',            'Guaviare',              'Del Llano'),
    ('97', '97000', 'VAUPES',              'Vaupés',                'Del Llano'),
    ('99', '99000', 'VICHADA',             'Vichada',               'Del Llano'),
]

# 5 vigencias fiscales
VIGENCIAS = [
    (2020, 'Vigencia Fiscal 2020', 0, None),
    (2021, 'Vigencia Fiscal 2021', 0, None),
    (2022, 'Vigencia Fiscal 2022', 0, None),
    (2023, 'Vigencia Fiscal 2023', 0, None),
    (2024, 'Vigencia Fiscal 2024', 1, None),   # activa por defecto
]

# 5 rangos de desempeño
RANGOS = [
    (1, 'Deterioro',  '1. Deterioro (<40)',          0.0,  40.0, '#fd0200', 'Situación fiscal crítica: alta dependencia de transferencias, bajo ahorro corriente y elevado endeudamiento. Requiere intervención urgente del nivel central.'),
    (2, 'Riesgo',     '2. Riesgo (>=40 y <60)',       40.0, 60.0, '#fddd00', 'Desempeño fiscal débil, con vulnerabilidades fiscales que pueden agravarse ante choques externos si no se adoptan medidas correctivas.'),
    (3, 'Vulnerable', '3. Vulnerable (>=60 y <70)',   60.0, 70.0, '#2476c5', 'Desempeño aceptable pero con áreas de mejora. El departamento mantiene equilibrios básicos aunque enfrenta restricciones fiscales.'),
    (4, 'Solvente',   '4. Solvente (>=70 y <80)',     70.0, 80.0, '#0046b1', 'Desempeño fiscal sólido. Buena capacidad de ahorro, baja dependencia de transferencias y adecuada ejecución presupuestal.'),
    (5, 'Sostenible', '5. Sostenible (>=80)',          80.0, 105.0,'#0e7c66', 'Desempeño fiscal sobresaliente. Alta eficiencia en recaudo, inversión y gestión financiera. Referente nacional de buenas prácticas fiscales.'),
]


def paso_1_3(conn):
    cur = conn.cursor()

    # — departamentos —
    cur.executemany(
        """INSERT OR IGNORE INTO departamento
           (codigo_divipola_2, codigo_divipola_5, nombre, nombre_visual, region)
           VALUES (?, ?, ?, ?, ?)""",
        DEPARTAMENTOS
    )
    n_depto = cur.execute("SELECT COUNT(*) FROM departamento").fetchone()[0]
    print(f"[1.3] ✔ Departamentos insertados: {n_depto} / 32")

    # — vigencias —
    cur.executemany(
        """INSERT OR IGNORE INTO vigencia_fiscal
           (anio, descripcion, es_vigencia_activa, fecha_publicacion_dnp)
           VALUES (?, ?, ?, ?)""",
        VIGENCIAS
    )
    n_vig = cur.execute("SELECT COUNT(*) FROM vigencia_fiscal").fetchone()[0]
    print(f"[1.3] ✔ Vigencias fiscales insertadas: {n_vig} / 5  (2024 marcada como activa)")

    # — rangos —
    cur.executemany(
        """INSERT OR IGNORE INTO catalogo_rango_desempeno
           (rango_id, codigo, nombre_completo, limite_inferior, limite_superior,
            color_hex, descripcion_cualitativa)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        RANGOS
    )
    n_rango = cur.execute("SELECT COUNT(*) FROM catalogo_rango_desempeno").fetchone()[0]
    print(f"[1.3] ✔ Rangos de desempeño insertados: {n_rango} / 5")

    conn.commit()


# ══════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════
if __name__ == '__main__':
    print("=" * 60)
    print("FASE 1 — Inicialización de la Base de Datos IDF (SQLite)")
    print("=" * 60)

    # Paso 1.1
    paso_1_1()

    # Conectar (crea el archivo si no existe)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        # Paso 1.2
        paso_1_2(conn)

        # Paso 1.3
        paso_1_3(conn)

        # Verificación rápida
        print()
        print("─" * 40)
        print("VERIFICACIÓN RÁPIDA DE TABLAS CREADAS:")
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        for t in tables:
            n = conn.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]
            print(f"  {t[0]:<40} {n:>4} filas")

        indexes = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
        ).fetchall()
        print(f"\nÍndices creados: {len(indexes)}")
        for ix in indexes:
            print(f"  {ix[0]}")

        print()
        print("=" * 60)
        print("✔  FASE 1 COMPLETADA SIN ERRORES")
        print(f"   Base de datos: {DB_PATH}")
        print("=" * 60)

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] La fase 1 falló: {e}")
        raise
    finally:
        conn.close()
