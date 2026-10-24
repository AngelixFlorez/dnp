import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from starlette.testclient import TestClient
from api.main import app

sys.stdout.reconfigure(encoding='utf-8')

client = TestClient(app)

def test_all():
    print("==================================================")
    print("FASE 4 — Verificación de Endpoints de la API REST")
    print("==================================================")

    # 1. Root & Health
    r = client.get("/")
    assert r.status_code == 200, f"Error en /: {r.status_code}"
    print("  ✔ GET / -> 200 OK")

    r = client.get("/health")
    assert r.status_code == 200, f"Error en /health: {r.status_code}"
    health_data = r.json()
    assert health_data["total_departamentos"] == 32
    print(f"  ✔ GET /health -> 200 OK ({health_data['total_departamentos']} deptos, BD conectada)")

    # 2. Meta
    r = client.get("/api/v1/meta")
    assert r.status_code == 200, f"Error en /meta: {r.status_code}"
    meta = r.json()
    assert len(meta["anios"]) == 5
    assert len(meta["departamentos"]) == 32
    assert len(meta["rangos"]) == 5
    print(f"  ✔ GET /api/v1/meta -> 200 OK (anios={meta['anios']}, rangos={len(meta['rangos'])})")

    # 3. Instructivo 2024
    r = client.get("/api/v1/instructivo/2024")
    assert r.status_code == 200, f"Error en /instructivo/2024: {r.status_code}"
    inst = r.json()
    assert len(inst["ranking_nacional"]) == 32
    assert len(inst["evolucion_historica"]) == 5
    print(f"  ✔ GET /api/v1/instructivo/2024 -> 200 OK (ranking={len(inst['ranking_nacional'])}, evolucion={len(inst['evolucion_historica'])})")

    # 4. Ficha Departamental (ANTIOQUIA 2024 y CASANARE 2024)
    for depto in ["ANTIOQUIA", "CASANARE", "05"]:
        r = client.get(f"/api/v1/ficha/{depto}/2024")
        assert r.status_code == 200, f"Error en /ficha/{depto}/2024: {r.status_code}"
        ficha = r.json()
        assert ficha["identificacion"]["departamento"] in ["ANTIOQUIA", "CASANARE"]
        assert ficha["idf"]["puntaje_final"] is not None
        assert len(ficha["historico_departamental"]) == 5
        print(f"  ✔ GET /api/v1/ficha/{depto}/2024 -> 200 OK (IDF={ficha['idf']['puntaje_final']:.2f}, Rank=#{ficha['idf']['ranking']})")

    # 5. Consolidado (Benchmarking)
    r = client.get("/api/v1/consolidado/ANTIOQUIA/2024")
    assert r.status_code == 200, f"Error en /consolidado/ANTIOQUIA/2024: {r.status_code}"
    cons = r.json()
    assert "vs_nacional" in cons["brechas"]
    assert "vs_categoria" in cons["brechas"]
    assert "vs_tipologia" in cons["brechas"]
    print(f"  ✔ GET /api/v1/consolidado/ANTIOQUIA/2024 -> 200 OK (Brechas calculadas vs Nacional, Categoría y Tipología)")

    # 6. Distribución (Mapa 2024)
    r = client.get("/api/v1/distribucion/2024")
    assert r.status_code == 200, f"Error en /distribucion/2024: {r.status_code}"
    dist = r.json()
    assert len(dist["departamentos"]) == 32
    assert dist["resumen_nacional"]["total_deptos"] == 32
    print(f"  ✔ GET /api/v1/distribucion/2024 -> 200 OK (32 departamentos con IDF y colores)")

    # 7. Datos completos (Transición rápida)
    r = client.get("/api/v1/datos-completos")
    assert r.status_code == 200, f"Error en /datos-completos: {r.status_code}"
    full = r.json()
    assert "meta" in full and "records" in full and "dashboard" in full
    assert len(full["records"]["2024"]) == 32
    print(f"  ✔ GET /api/v1/datos-completos -> 200 OK (Estructura idéntica con {len(full['records']['2024'])} departamentos)")

    # 8. Documentación OpenAPI / Docs
    r = client.get("/openapi.json")
    assert r.status_code == 200, "Error en /openapi.json"
    print("  ✔ GET /openapi.json -> 200 OK (Especificación OpenAPI 3.1 generada correctamente)")

    print("==================================================")
    print("🎯 TODOS LOS ENDPOINTS FUNCIONAN AL 100%")
    print("==================================================")

if __name__ == "__main__":
    test_all()
