@echo off
cd /d "%~dp0"
REM Intenta ejecutar con venv, luego venv_disabled, luego python global
if exist "venv\Scripts\pythonw.exe" (
    start "" "venv\Scripts\pythonw.exe" "main.py"
) else (
    if exist "venv_disabled\Scripts\pythonw.exe" (
        start "" "venv_disabled\Scripts\pythonw.exe" "main.py"
    ) else (
        start "" pythonw "main.py"
    )
)
