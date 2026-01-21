@echo off
echo ====================================================
echo   MIGRACION MASIVA DE CODIGOS DESDE EXCEL
echo ====================================================
echo.
echo Este script importara TODOS los codigos desde los
echo archivos Excel en C:\INACAL-PDF\
echo.
echo Esto puede tardar varios minutos si son muchos archivos...
echo.
pause

cd /d "%~dp0"
venv\Scripts\python.exe migrar_codigos_historicos.py

pause
