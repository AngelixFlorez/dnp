"""
Módulo de conexión agnóstico a la Base de Datos (MySQL / SQLite) para el IDF Departamental.
Permite alternar entre MySQL (MySQL Workbench) y SQLite con fallback automático de 2 niveles.
"""

import os
import json
import sqlite3
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_SQLITE_PATH = os.path.join(BASE_DIR, 'data', 'idf_database.db')
CONFIG_PATH = os.path.join(BASE_DIR, 'config_db.json')

ENV_PATH = os.path.join(BASE_DIR, '.env')

# Configuración por defecto
DEFAULT_CONFIG = {
    "motor": "mysql",
    "host": "localhost",
    "puerto": 3306,
    "usuario": "root",
    "password": "",
    "base_datos": "idf"
}


def cargar_env():
    """Carga variables desde el archivo .env si existe."""
    if not os.path.exists(ENV_PATH):
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(ENV_PATH, override=False)
    except ImportError:
        # Parser nativo de respaldo sin dependencias externas
        try:
            with open(ENV_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass


def cargar_configuracion():
    """
    Carga la configuración de base de datos con prioridad profesional:
    1. Variables de entorno del sistema o definidas en .env
    2. Archivo config_db.json (compatibilidad retroactiva)
    3. Valores predeterminados del sistema
    """
    cargar_env()
    cfg = DEFAULT_CONFIG.copy()

    # Compatibilidad retroactiva con config_db.json
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                user_cfg = json.load(f)
                cfg.update(user_cfg)
        except Exception as e:
            pass

    # Las variables de entorno (.env o variables del OS) tienen máxima prioridad
    cfg["motor"] = (os.getenv("DB_ENGINE") or os.getenv("IDF_DB_ENGINE") or cfg.get("motor", "mysql")).lower()
    cfg["host"] = os.getenv("DB_HOST") or os.getenv("MYSQL_HOST") or cfg.get("host", "localhost")
    puerto_val = os.getenv("DB_PORT") or os.getenv("MYSQL_PORT") or cfg.get("puerto", 3306)
    cfg["puerto"] = int(puerto_val)
    cfg["usuario"] = os.getenv("DB_USER") or os.getenv("MYSQL_USER") or cfg.get("usuario", "root")
    cfg["password"] = os.getenv("DB_PASSWORD") if os.getenv("DB_PASSWORD") is not None else (os.getenv("MYSQL_PASSWORD") if os.getenv("MYSQL_PASSWORD") is not None else cfg.get("password", ""))
    cfg["base_datos"] = os.getenv("DB_NAME") or os.getenv("MYSQL_DATABASE") or cfg.get("base_datos", "idf")
    return cfg


class MySQLConnectionWrapper:
    """
    Envoltura ligera sobre PyMySQL para compatibilidad con la sintaxis de sqlite3.
    Permite usar conn.execute(sql, params) tanto con '?' como con '%s',
    y devuelve resultados directamente como diccionarios.
    """
    def __init__(self, raw_conn):
        self._conn = raw_conn

    def execute(self, sql: str, params=None):
        cur = self._conn.cursor()
        # Traducir placeholders SQLite (?) a MySQL (%s) si los hay
        sql_mysql = sql.replace('?', '%s')
        if params is not None:
            cur.execute(sql_mysql, params)
        else:
            cur.execute(sql_mysql)
        return cur

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


def dict_factory_sqlite(cursor, row):
    """Convierte filas SQLite a diccionarios de Python nativos."""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


@contextmanager
def get_db():
    """
    Context manager de conexión con fallback de 2 niveles:
    1. MySQL (Workbench) - prioridad principal
    2. SQLite local (idf_database.db) - respaldo
    
    Muestra mensajes claros en cada nivel de fallback.
    """
    cfg = cargar_configuracion()
    usar_mysql = cfg.get("motor") == "mysql"

    # NIVEL 1: MySQL (Workbench)
    if usar_mysql:
        try:
            import pymysql
            import pymysql.cursors

            raw_conn = pymysql.connect(
                host=cfg["host"],
                port=cfg["puerto"],
                user=cfg["usuario"],
                password=cfg["password"],
                database=cfg["base_datos"],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=3
            )
            wrapped = MySQLConnectionWrapper(raw_conn)
            print(f"[BD] [OK] Conectado a MySQL Workbench: {cfg['usuario']}@{cfg['host']}:{cfg['puerto']}/{cfg['base_datos']}")
            try:
                yield wrapped
            finally:
                wrapped.close()
            return
        except Exception as e:
            # Fallback a SQLite
            print(f"[BD] [WARN] FALLO MySQL: No se pudo conectar a Workbench ({cfg['usuario']}@{cfg['host']}:{cfg['puerto']}/{cfg['base_datos']})")
            print(f"[BD] [WARN] Motivo: {e}")
            print(f"[BD] [INFO] Activando respaldo a SQLite local: {DB_SQLITE_PATH}")

    # NIVEL 2: SQLite local (archivo) - único respaldo
    sqlite_conn = None
    try:
        if os.path.exists(DB_SQLITE_PATH):
            uri = f"file:{os.path.abspath(DB_SQLITE_PATH)}?mode=ro"
            try:
                sqlite_conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
            except Exception:
                sqlite_conn = sqlite3.connect(DB_SQLITE_PATH, check_same_thread=False)
            
            sqlite_conn.row_factory = dict_factory_sqlite
            print(f"[BD] [OK] Conectado a SQLite local (archivo): {DB_SQLITE_PATH}")
            try:
                yield sqlite_conn
            finally:
                sqlite_conn.close()
            return
        else:
            raise FileNotFoundError(f"Archivo SQLite no encontrado: {DB_SQLITE_PATH}")
    except Exception as e:
        if sqlite_conn:
            try:
                sqlite_conn.close()
            except Exception:
                pass
        
        print(f"[BD] [ERROR] ERROR CRITICO: Fallaron los 2 niveles de conexion")
        print(f"[BD] [ERROR] MySQL: No disponible")
        print(f"[BD] [ERROR] SQLite local: No disponible ({DB_SQLITE_PATH})")
        print(f"[BD] [ERROR] Motivo: {e}")
        raise RuntimeError("No se pudo conectar a ninguna fuente de datos (MySQL, SQLite)") from e


def get_active_engine() -> str:
    """
    Detecta cuál motor de base de datos está respondiendo actualmente.
    Retorna: 'mysql', 'sqlite' o 'ninguno'.
    """
    cfg = cargar_configuracion()
    if cfg.get("motor") == "mysql":
        try:
            import pymysql
            conn = pymysql.connect(
                host=cfg["host"], port=cfg["puerto"],
                user=cfg["usuario"], password=cfg["password"],
                database=cfg["base_datos"], charset='utf8mb4',
                connect_timeout=2
            )
            conn.close()
            return "mysql"
        except Exception:
            pass
    if os.path.exists(DB_SQLITE_PATH):
        return "sqlite"
    return "ninguno"