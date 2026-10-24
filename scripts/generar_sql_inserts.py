"""
Generador de Scripts SQL Puros para Carga en MySQL Workbench / PostgreSQL / SQLite.

Permite exportar todos los datos estructurados a un archivo .sql estándar
que un Administrador de Base de Datos (DBA) puede abrir en MySQL Workbench
y ejecutar con un solo clic (F5) sin depender de archivos Excel ni de Python en el servidor.

Uso:
  python scripts/generar_sql_inserts.py --motor mysql --salida data/carga_inicial_mysql.sql
"""

import os
import sys
import sqlite3
import argparse

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_SQLITE = os.path.join(BASE_DIR, 'data', 'idf_database.db')

TABLAS_ORDENADAS = [
    'departamento',
    'vigencia_fiscal',
    'catalogo_rango_desempeno',
    'clasificacion_anual',
    'insumo_presupuestal_cuipo',
    'evaluacion_resultados_fiscales',
    'evaluacion_gestion_territorial',
    'resultado_idf_anual'
]

def fmt_sql_val(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    # Escapar comillas simples
    s = str(v).replace("'", "''")
    return f"'{s}'"

def generar_sql(motor: str, salida: str):
    if not os.path.exists(DB_SQLITE):
        print(f"✘ Error: No existe la base de datos origen en: {DB_SQLITE}")
        sys.exit(1)

    conn = sqlite3.connect(DB_SQLITE)
    conn.row_factory = sqlite3.Row

    lineas = [
        "-- ====================================================================",
        f"-- SCRIPT SQL DE INGESTA INSTITUCIONAL PARA: {motor.upper()}",
        "-- Generado automáticamente para el Sistema IDF Departamental (DNP)",
        "-- Compatible con MySQL Workbench, DBeaver y clientes de terminal.",
        "-- ====================================================================\n",
    ]

    if motor == "mysql":
        lineas.extend([
            "USE `idf`;\n",
            "SET FOREIGN_KEY_CHECKS = 0;",
            "SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';\n"
        ])

    total_registros = 0

    for tabla in TABLAS_ORDENADAS:
        rows = conn.execute(f"SELECT * FROM {tabla}").fetchall()
        if not rows:
            continue

        cols = list(rows[0].keys())
        col_str = ", ".join([f"`{c}`" if motor == "mysql" else f'"{c}"' for c in cols])
        
        lineas.append(f"-- ----------------------------------------------------")
        lineas.append(f"-- Carga de datos: {tabla} ({len(rows)} registros)")
        lineas.append(f"-- ----------------------------------------------------")

        for r in rows:
            vals = [fmt_sql_val(r[c]) for c in cols]
            val_str = ", ".join(vals)
            
            if motor == "mysql":
                # INSERT ... ON DUPLICATE KEY UPDATE para no fallar si ya existe
                updates = [f"`{c}`=VALUES(`{c}`)" for c in cols if c != cols[0]]
                update_str = ", ".join(updates) if updates else f"`{cols[0]}`=`{cols[0]}`"
                lineas.append(f"INSERT INTO `{tabla}` ({col_str}) VALUES ({val_str}) ON DUPLICATE KEY UPDATE {update_str};")
            else:
                lineas.append(f"INSERT OR REPLACE INTO {tabla} ({col_str}) VALUES ({val_str});")

        lineas.append("")
        total_registros += len(rows)

    if motor == "mysql":
        lineas.extend([
            "SET FOREIGN_KEY_CHECKS = 1;",
            "COMMIT;\n",
            "-- Fin de la carga institucional."
        ])

    conn.close()

    # Guardar archivo
    ruta_salida = os.path.join(BASE_DIR, salida) if not os.path.isabs(salida) else salida
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    with open(ruta_salida, 'w', encoding='utf-8') as f:
        f.write("\n".join(lineas))

    print(f"✔ Script SQL generado exitosamente: {ruta_salida}")
    print(f"  Total de sentencias SQL generadas: {total_registros} registros.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generador de sentencias SQL para MySQL Workbench")
    parser.add_argument("--motor", choices=["mysql", "sqlite"], default="mysql", help="Motor de destino (default: mysql)")
    parser.add_argument("--salida", default="data/carga_datos_mysql.sql", help="Ruta del archivo .sql resultante")
    args = parser.parse_args()

    generar_sql(args.motor, args.salida)
