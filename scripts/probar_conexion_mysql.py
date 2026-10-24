"""
Script de diagnóstico y prueba de conexión a MySQL para el proyecto IDF DNP.
Verifica que las credenciales del archivo .env funcionen y comprueba
la existencia de las 8 tablas y 3 vistas en la base de datos `idf`.

Uso:
  python scripts/probar_conexion_mysql.py
"""

import os
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from api.database import cargar_configuracion, ENV_PATH, CONFIG_PATH

TABLAS_ESPERADAS = [
    'departamento',
    'vigencia_fiscal',
    'catalogo_rango_desempeno',
    'clasificacion_anual',
    'insumo_presupuestal_cuipo',
    'evaluacion_resultados_fiscales',
    'evaluacion_gestion_territorial',
    'resultado_idf_anual'
]

VISTAS_ESPERADAS = [
    'vw_visualizador_ficha',
    'vw_visualizador_mapa',
    'vw_visualizador_evolucion_nacional'
]

def probar():
    print("====================================================================")
    print("DIAGNÓSTICO DE CONEXIÓN A MYSQL (MySQL Workbench / Servidor Central)")
    print("====================================================================")

    fuente_config = []
    if os.path.exists(ENV_PATH):
        fuente_config.append(f".env ({ENV_PATH})")
    if os.path.exists(CONFIG_PATH):
        fuente_config.append(f"config_db.json ({CONFIG_PATH})")

    if not fuente_config:
        print(f"✘ Error: No existe ni '.env' ni 'config_db.json' en el proyecto.")
        sys.exit(1)

    cfg = cargar_configuracion()

    host = cfg.get("host", "localhost")
    port = int(cfg.get("puerto", 3306))
    user = cfg.get("usuario", "root")
    password = cfg.get("password", "")
    database = cfg.get("base_datos", "idf")

    print(f"Fuentes de configuración detectadas:")
    for f in fuente_config:
        print(f"  • {f}")
    print(f"\nParámetros efectivos de conexión:")
    print(f"  • Motor       : {cfg.get('motor', 'mysql')}")
    print(f"  • Host        : {host}:{port}")
    print(f"  • Usuario     : {user}")
    print(f"  • Password    : {'******' if password else '(vacía)'}")
    print(f"  • Base de datos: {database}\n")

    try:
        import pymysql
    except ImportError:
        print("✘ Error: No se encontró la biblioteca 'pymysql'. Instálala con: pip install pymysql")
        sys.exit(1)

    print("Conectando con el servidor MySQL...")
    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=4
        )
        print("✔ CONEXIÓN EXITOSA AL SERVIDOR MYSQL.")
    except Exception as e:
        print(f"\n✘ NO SE PUDO CONECTAR A MYSQL: {e}")
        print("\nVerificaciones sugeridas:")
        print(" 1. Asegúrate de que el servidor MySQL esté corriendo (en MySQL Workbench o Servicios de Windows).")
        print(" 2. Revisa que el usuario y la contraseña en '.env' sean los correctos.")
        print(" 3. Confirma que la base de datos 'idf' exista en MySQL Workbench.")
        return False

    with conn.cursor() as cur:
        # Verificar tablas existentes
        cur.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE';")
        tablas_db = [list(r.values())[0] for r in cur.fetchall()]

        # Verificar vistas existentes
        cur.execute("SHOW FULL TABLES WHERE Table_type = 'VIEW';")
        vistas_db = [list(r.values())[0] for r in cur.fetchall()]

        print("\nEstado de las Tablas:")
        todas_tablas_ok = True
        for t in TABLAS_ESPERADAS:
            if t in tablas_db:
                cur.execute(f"SELECT COUNT(*) AS n FROM `{t}`;")
                count = cur.fetchone()['n']
                print(f"  ✔ Tabla `{t:<35}` : {count:>4} filas")
            else:
                print(f"  ✘ Tabla `{t:<35}` : FALTA (ejecuta data/schema_mysql.sql)")
                todas_tablas_ok = False

        print("\nEstado de las Vistas Analíticas:")
        todas_vistas_ok = True
        for v in VISTAS_ESPERADAS:
            if v in vistas_db:
                print(f"  ✔ Vista `{v:<35}` : Creada y activa")
            else:
                print(f"  ✘ Vista `{v:<35}` : FALTA (ejecuta data/schema_mysql.sql)")
                todas_vistas_ok = False

        if todas_tablas_ok and todas_vistas_ok:
            print("\n====================================================================")
            print("🎯 TODO LISTO: La base de datos MySQL `idf` está 100% configurada.")
            print("====================================================================")
        else:
            print("\n====================================================================")
            print("ℹ Recuerda ejecutar 'data/migracion_completa_mysql.sql' en MySQL Workbench")
            print("  para crear las tablas y cargar los datos automáticamente.")
            print("====================================================================")

    conn.close()
    return True

if __name__ == '__main__':
    probar()
