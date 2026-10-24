"""
Script utilitario para migrar datos desde SQLite (data/idf_database.db)
hacia un servidor central MySQL administrado con MySQL Workbench.

Requisitos:
  pip install pymysql
Uso:
  python scripts/migrar_a_mysql.py --host localhost --user root --password tu_pass --database idf_departamental_dnp
"""

import os
import sys
import argparse
import sqlite3

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

def migrar(host, port, user, password, database):
    try:
        import pymysql
    except ImportError:
        print("✘ Error: Se requiere el paquete pymysql. Instálalo con: pip install pymysql")
        sys.exit(1)

    if not os.path.exists(DB_SQLITE):
        print(f"✘ Error: No se encontró la base de datos SQLite en: {DB_SQLITE}")
        sys.exit(1)

    print("==========================================================")
    print("MIGRACIÓN DE DATOS: SQLite ➔ MySQL")
    print("==========================================================")
    print(f"Origen  : {DB_SQLITE}")
    print(f"Destino : mysql://{user}@{host}:{port}/{database}\n")

    # Conectar origen
    sq_conn = sqlite3.connect(DB_SQLITE)
    sq_conn.row_factory = sqlite3.Row

    # Conectar destino
    try:
        my_conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        print(f"✘ Error al conectar a MySQL: {e}")
        print("Verifica que el servidor MySQL esté encendido y que la base de datos exista.")
        sys.exit(1)

    total_migrados = 0
    with my_conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
        for t in TABLAS_ORDENADAS:
            rows = sq_conn.execute(f"SELECT * FROM {t}").fetchall()
            if not rows:
                print(f"  ⚠  Tabla `{t}`: sin registros en SQLite.")
                continue

            cols = list(rows[0].keys())
            col_str = ", ".join([f"`{c}`" for c in cols])
            placeholders = ", ".join(["%s"] * len(cols))
            sql = f"REPLACE INTO `{t}` ({col_str}) VALUES ({placeholders})"
            values = [tuple(r[c] for c in cols) for r in rows]

            cur.executemany(sql, values)
            total_migrados += len(values)
            print(f"  ✔ Tabla `{t}`: {len(values)} registros migrados con éxito.")

        cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
        my_conn.commit()

    sq_conn.close()
    my_conn.close()

    print("\n==========================================================")
    print(f"🎯 Migración finalizada con éxito: {total_migrados} registros transferidos.")
    print("==========================================================")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Migrador de SQLite a MySQL para el proyecto IDF DNP")
    parser.add_argument("--host", default="localhost", help="Host del servidor MySQL (default: localhost)")
    parser.add_argument("--port", type=int, default=3306, help="Puerto MySQL (default: 3306)")
    parser.add_argument("--user", default="root", help="Usuario de MySQL (default: root)")
    parser.add_argument("--password", default="", help="Contraseña de MySQL")
    parser.add_argument("--database", default="idf_departamental_dnp", help="Nombre de la base de datos MySQL")
    args = parser.parse_args()

    migrar(args.host, args.port, args.user, args.password, args.database)
