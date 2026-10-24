"""
Módulo de conexión a la base de datos SQLite para la API del IDF Departamental.
Implementa conexión ligera en modo de lectura con row_factory como diccionario.
"""

import os
import sqlite3
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'idf_database.db')

def dict_factory(cursor, row):
    """Convierte filas SQLite a diccionarios de Python nativos."""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

@contextmanager
def get_db():
    """
    Context manager para obtener una conexión SQLite de solo lectura.
    Garantiza el cierre automático de la conexión tras responder a la petición.
    """
    # Intentamos abrir con URI en modo de solo lectura (mode=ro)
    uri = f"file:{os.path.abspath(DB_PATH)}?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    except Exception:
        # Fallback si el URI no está habilitado en alguna versión de SQLite
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)

    conn.row_factory = dict_factory
    try:
        yield conn
    finally:
        conn.close()
