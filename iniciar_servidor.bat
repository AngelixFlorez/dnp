@echo off
chcp 65001 >nul
title Servidor IDF Departamental — DNP

echo ====================================================================
echo  Iniciando Sistema de Informacion del Indice de Desempeno Fiscal
echo  Departamento Nacional de Planeacion (DNP)
echo ====================================================================
echo.
echo [1/2] Levantando servidor API REST FastAPI / SQLite...
start "Servidor API REST IDF" cmd /k "python -m uvicorn api.main:app --port 8000 --reload"

echo [2/2] Esperando inicio del servidor...
timeout /t 3 /nobreak >nul

echo Abriendo visualizador en el navegador...
start http://localhost:8000/

echo.
echo ====================================================================
echo  Sistema iniciado correctamente:
echo   - Visualizador Web:       http://localhost:8000/
echo   - Documentacion Swagger:  http://localhost:8000/docs
echo   - API Health Check:       http://localhost:8000/health
echo ====================================================================
echo Puedes cerrar esta ventana. El servidor continuara en su terminal.
pause
