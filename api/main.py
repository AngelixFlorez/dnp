"""
API REST Backend — Sistema de Información del Índice de Desempeño Fiscal (IDF) Departamental
Departamento Nacional de Planeación (DNP)

Provee endpoints analíticos de alta velocidad basados en FastAPI y SQLite relacional.
Documentación interactiva disponible en /docs (Swagger UI) y /redoc.
"""

from fastapi import FastAPI, HTTPException, Path, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import shutil
import tempfile
from typing import Optional

from api.services import (
    get_metadata,
    get_instructivo_data,
    get_ficha_departamental,
    get_consolidado_data,
    get_distribucion_data,
    get_datos_completos
)

# Inicialización de la aplicación FastAPI con metadata OpenAPI
app = FastAPI(
    title="API REST — Índice de Desempeño Fiscal (IDF) Departamental",
    description=(
        "Servicio backend oficial para el visualizador del Índice de Desempeño Fiscal Departamental (DNP). "
        "Permite consultar indicadores fiscales (80%), gestión territorial (20%), insumos presupuestales CUIPO "
        "y distribuciones geográficas para las 32 entidades territoriales en las vigencias 2020 a 2024."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuración de CORS para permitir consumo desde navegador y desarrollo local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, "index.html")

# Montaje de carpetas estáticas para servir geo, js, data y multimedia
for folder in ["geo", "js", "css", "images", "data"]:
    folder_path = os.path.join(BASE_DIR, folder)
    if os.path.isdir(folder_path):
        app.mount(f"/{folder}", StaticFiles(directory=folder_path), name=folder)


@app.get("/", tags=["General"])
def root():
    """Sirve el visualizador interactivo index.html directamente en la raíz."""
    if os.path.exists(INDEX_PATH):
        return FileResponse(INDEX_PATH, media_type="text/html")
    return {
        "sistema": "API REST — Índice de Desempeño Fiscal (IDF) Departamental DNP",
        "version": "1.0.0",
        "documentacion": "/docs"
    }


@app.get("/api", tags=["General"])
def api_info():
    """Ruta con información y catálogo de endpoints principales."""
    return {
        "sistema": "API REST — Índice de Desempeño Fiscal (IDF) Departamental DNP",
        "version": "1.0.0",
        "estado": "operativo",
        "documentacion": "/docs",
        "endpoints_principales": [
            "/api/v1/meta",
            "/api/v1/instructivo/{anio}",
            "/api/v1/ficha/{departamento}/{anio}",
            "/api/v1/consolidado/{departamento}/{anio}",
            "/api/v1/distribucion/{anio}",
            "/api/v1/datos-completos"
        ]
    }


@app.get("/health", tags=["General"])
def health_check():
    """Chequeo de salud del servicio y de la conexión a base de datos."""
    try:
        meta = get_metadata()
        return {
            "status": "healthy",
            "base_datos": "conectada",
            "total_departamentos": len(meta["departamentos"]),
            "vigencias_disponibles": meta["anios"]
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.get("/api/v1/meta", tags=["Catálogos"])
def api_get_meta():
    """
    Retorna los catálogos maestros del sistema:
    - Lista de vigencias fiscales registradas (2020 a 2024).
    - Lista de 32 departamentos oficiales (códigos DIVIPOLA 2 y 5 dígitos, nombre, región).
    - Rangos institucionales de desempeño (Deterioro, Riesgo, Vulnerable, Solvente, Sostenible) con sus colores oficiales.
    """
    return get_metadata()


@app.get("/api/v1/instructivo/{anio}", tags=["Instructivo & Tablero Nacional"])
def api_get_instructivo(
    anio: int = Path(..., ge=2020, le=2024, description="Vigencia fiscal a consultar (2020-2024)")
):
    """
    Datos analíticos para la pestaña **Instructivo / Tablero Nacional**:
    - Serie histórica nacional consolidada (promedio, máximo, mínimo, variación pp).
    - Ranking nacional completo del 1 al 32 para el año seleccionado.
    - Distribución por rangos de desempeño.
    - Distribución por categorías de Ley 617 y tipologías DNP.
    """
    return get_instructivo_data(anio)


@app.get("/api/v1/ficha/{departamento}/{anio}", tags=["Ficha Departamental"])
def api_get_ficha(
    departamento: str = Path(..., description="Nombre del departamento o código DIVIPOLA (ej. ANTIOQUIA, 05, CASANARE)"),
    anio: int = Path(..., ge=2020, le=2024, description="Vigencia fiscal (2020 a 2024)")
):
    """
    Ficha técnica integral del departamento:
    - Datos de identificación territorial (DIVIPOLA, región, categoría, tipología).
    - Puntaje IDF final, ranking nacional y variación interanual.
    - Desglose de Resultados Fiscales (80%): 5 indicadores con resultado y calificación.
    - Desglose de Gestión Territorial (20%): 3 indicadores + bonificación de esfuerzo propio.
    - Insumos presupuestales detallados del CUIPO (21 cuentas contables/financieras).
    - Historial multianual completo (2020–2024) del departamento para gráficas de tendencia.
    """
    ficha = get_ficha_departamental(departamento, anio)
    if not ficha:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró información para el departamento '{departamento}' en la vigencia {anio}."
        )
    return ficha


@app.get("/api/v1/consolidado/{departamento}/{anio}", tags=["Consolidado & Benchmarking"])
def api_get_consolidado(
    departamento: str = Path(..., description="Nombre del departamento o código DIVIPOLA"),
    anio: int = Path(..., ge=2020, le=2024, description="Vigencia fiscal")
):
    """
    Módulo de benchmarking y comparación contra pares:
    - Valores individuales del departamento.
    - Promedios de referencia del grupo par: **Nacional**, **Categoría Ley 617** y **Tipología DNP**.
    - Brechas cuantitativas relativas para cada dimensión e indicador fiscal.
    """
    consolidado = get_consolidado_data(departamento, anio)
    if not consolidado:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró información para el departamento '{departamento}' en la vigencia {anio}."
        )
    return consolidado


@app.get("/api/v1/distribucion/{anio}", tags=["Distribución Geográfica & Mapa"])
def api_get_distribucion(
    anio: int = Path(..., ge=2020, le=2024, description="Vigencia fiscal a consultar (2020 a 2024)")
):
    """
    Datos espaciales y de distribución territorial para alimentar el mapa coroplético de Colombia:
    - Listado de los 32 departamentos con IDF, ranking, rango de desempeño, color institucional y variación pp.
    - Métricas estadísticas resumen del país en dicho año.
    """
    return get_distribucion_data(anio)


@app.get("/api/v1/datos-completos", tags=["Transición Rápida"])
def api_get_datos_completos():
    """
    **Endpoint de compatibilidad y transición rápida:**
    Genera dinámicamente desde SQLite la estructura completa de datos requerida por el visualizador
    (llaves `meta`, `records` y `dashboard`), ofreciendo compatibilidad 100% inmediata con el frontend existente.
    """
    return get_datos_completos()


@app.post("/api/v1/admin/cargar-excel", tags=["Administración & Ingesta"])
async def api_cargar_excel(
    archivo: UploadFile = File(..., description="Archivo Excel (.xlsx o .xls) con nuevas vigencias o ajustes departamentales")
):
    """
    **Endpoint de Ingesta Institucional:**
    Permite subir cualquier archivo de Excel sin importar su nombre o ubicación.
    El backend extrae los registros, normaliza variables, actualiza transaccionalmente 
    la base de datos relacional y recalcula las vistas analíticas en tiempo real.
    """
    if not (archivo.filename.lower().endswith(".xlsx") or archivo.filename.lower().endswith(".xls")):
        raise HTTPException(
            status_code=400,
            detail="Formato de archivo no admitido. Debe subir un libro de Microsoft Excel (.xlsx o .xls)."
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        shutil.copyfileobj(archivo.file, tmp)
        tmp_path = tmp.name

    try:
        from scripts.cargar_datos_excel import ejecutar_pipeline_etl
        res = ejecutar_pipeline_etl(excel_path=tmp_path)
        return {
            "mensaje": f"Archivo '{archivo.filename}' procesado e integrado exitosamente en la base de datos.",
            "detalle": res
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error durante la ingesta del archivo Excel: {str(e)}"
        )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
